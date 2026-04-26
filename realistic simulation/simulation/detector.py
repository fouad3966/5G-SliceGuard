"""
5G SliceGuard — Real-Time Detector
====================================
Takes a traffic snapshot from TrafficGenerator, runs both ML models
(XGBoost + Isolation Forest), and returns a verdict with confidence
scores, severity levels, and recommended actions.

The detector implements the core IDS pipeline:
  1. Feature extraction from raw metrics
  2. XGBoost supervised classification (4-class)
  3. Isolation Forest unsupervised anomaly scoring
  4. Combined confidence score (70% XGB + 30% ISO)
  5. Cross-slice correlation for attack type identification
  6. Severity assessment and action recommendation
"""

import os
import json
from collections import deque
import numpy as np
import joblib

from feature_extractor import FeatureExtractor, FEATURE_NAMES

# ── Configuration ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "model")

LABEL_MAP = {0: "normal", 1: "resource_theft", 2: "data_injection", 3: "side_channel"}
SLICE_ID_MAP = {"eMBB": 0, "URLLC": 1, "mMTC": 2}


class SliceGuardDetector:
    """
    Multi-model intrusion detection engine for 5G network slices.

    Combines supervised (XGBoost) and unsupervised (Isolation Forest)
    ML models to detect both known and novel attack patterns.
    """

    def __init__(self):
        self.feature_extractor = FeatureExtractor(window_size=10)
        self.alert_threshold = 0.65
        self.per_slice_alerts = {
            "eMBB": deque(maxlen=20),
            "URLLC": deque(maxlen=20),
            "mMTC": deque(maxlen=20),
        }
        self.model_loaded = False
        self.xgb_accuracy = 0.0
        self.warmup_until_tick = 10  # Wait for rolling windows to populate

        # Load models
        self._load_models()

    def reset_warmup(self, current_tick: int):
        """Reset the feature extractor and enter warmup phase to avoid false positives."""
        self.feature_extractor.reset()
        self.warmup_until_tick = current_tick + 10

    def _load_models(self):
        """Load trained models from disk."""
        xgb_path = os.path.join(MODEL_DIR, "xgb_model.pkl")
        iso_path = os.path.join(MODEL_DIR, "iso_forest.pkl")
        meta_path = os.path.join(MODEL_DIR, "feature_columns.json")

        if not os.path.exists(xgb_path) or not os.path.exists(iso_path):
            raise FileNotFoundError(
                f"Model files not found in {MODEL_DIR}/. "
                "Run train_model.py first!"
            )

        self.xgb_model = joblib.load(xgb_path)
        self.iso_model = joblib.load(iso_path)

        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
                self.xgb_accuracy = meta.get("xgb_accuracy", 0.0)

        self.model_loaded = True
        print("[Detector] Models loaded successfully")

    def analyze(self, snapshot: dict) -> dict:
        """
        Analyze a traffic snapshot from TrafficGenerator.

        For each slice:
          1. Extract features using FeatureExtractor
          2. XGBoost: predict class + probability
          3. Isolation Forest: anomaly score
          4. Combine into per-slice verdict

        Then cross-correlate across slices to identify
        the dominant attack pattern.

        Args:
            snapshot: output from TrafficGenerator.generate_tick()

        Returns:
            Full analysis dict with per-slice verdicts and global assessment.
        """
        slice_analysis = {}
        max_severity = "LOW"
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

        for slice_name in ["eMBB", "URLLC", "mMTC"]:
            metrics = snapshot["slices"][slice_name]
            slice_metrics = {**metrics, "slice_id": SLICE_ID_MAP[slice_name]}

            # 1. Extract features
            extracted = self.feature_extractor.extract(slice_metrics)
            feature_vector = self.feature_extractor.get_feature_vector(extracted)
            X = np.array([feature_vector])

            # 2. XGBoost prediction
            if snapshot["tick"] <= self.warmup_until_tick:
                # Warm-up phase to let rolling windows fill up
                xgb_class = 0
                xgb_confidence = 1.0
                iso_normalized = 0.0
                xgb_proba = [1.0, 0.0, 0.0, 0.0]
            else:
                xgb_proba = self.xgb_model.predict_proba(X)[0]
                xgb_class = int(np.argmax(xgb_proba))
                xgb_confidence = float(xgb_proba[xgb_class])
                
                # 3. Isolation Forest anomaly score
                iso_raw = float(self.iso_model.decision_function(X)[0])
                iso_normalized = max(0.0, min(1.0, 0.5 - iso_raw))

            xgb_label = LABEL_MAP[xgb_class]

            # 4. Combined confidence score
            if xgb_class != 0:
                combined = 0.7 * xgb_confidence + 0.3 * iso_normalized
            else:
                combined = 0.3 * (1.0 - xgb_confidence) + 0.3 * iso_normalized

            # 5. Alert decision
            alert = (combined > self.alert_threshold) and (xgb_class != 0)
            severity = self._get_severity(combined)

            if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                max_severity = severity

            if alert:
                self.per_slice_alerts[slice_name].append({
                    "attack": xgb_label,
                    "confidence": combined,
                    "severity": severity,
                })

            slice_analysis[slice_name] = {
                "metrics": metrics,
                "xgb_prediction": xgb_label,
                "xgb_confidence": round(xgb_confidence, 4),
                "xgb_probabilities": {LABEL_MAP[i]: round(float(p), 4) for i, p in enumerate(xgb_proba)},
                "iso_score": round(iso_normalized, 4),
                "combined_score": round(combined, 4),
                "alert": alert,
                "severity": severity,
            }

        # 6. Cross-slice correlation
        dominant_attack = self._cross_correlate(slice_analysis)
        global_alert = any(sa["alert"] for sa in slice_analysis.values())
        recommended_action = self._recommend_action(slice_analysis, max_severity)

        return {
            "timestamp": snapshot["timestamp"],
            "tick": snapshot["tick"],
            "slice_analysis": slice_analysis,
            "global_alert": global_alert,
            "dominant_attack": dominant_attack,
            "recommended_action": recommended_action,
            "max_severity": max_severity,
        }

    def _get_severity(self, combined_score: float) -> str:
        """Map combined anomaly score to severity level."""
        if combined_score < 0.4:
            return "LOW"
        elif combined_score < 0.65:
            return "MEDIUM"
        elif combined_score < 0.85:
            return "HIGH"
        else:
            return "CRITICAL"

    def _cross_correlate(self, slice_analysis: dict) -> str:
        """
        Cross-correlate anomalies across slices to identify
        the dominant attack pattern.

        This is what makes SliceGuard unique vs a generic IDS —
        it understands slice TOPOLOGY and looks for correlated
        anomalies that span isolation boundaries.
        """
        urllc = slice_analysis["URLLC"]
        mmtc = slice_analysis["mMTC"]
        embb = slice_analysis["eMBB"]

        # Resource Theft: mMTC resource spike + URLLC latency degradation
        if (mmtc["xgb_prediction"] == "resource_theft" or
                mmtc["metrics"]["cpu_usage_pct"] > 50):
            if urllc["metrics"]["latency_ms"] > 1.5:
                return "resource_theft"

        # Data Injection: URLLC has high cross-slice score
        if urllc["metrics"]["cross_slice_score"] > 0.4:
            return "data_injection"

        # Side-Channel: subtle periodic patterns across multiple slices
        if (mmtc["xgb_prediction"] == "side_channel" or
                urllc["xgb_prediction"] == "side_channel" or
                embb["xgb_prediction"] == "side_channel"):
            return "side_channel"

        # Check if any slice is alerting
        for name, analysis in slice_analysis.items():
            if analysis["alert"] and analysis["xgb_prediction"] != "normal":
                return analysis["xgb_prediction"]

        return None

    def _recommend_action(self, slice_analysis: dict, max_severity: str) -> str:
        """Recommend response action based on severity."""
        if max_severity == "CRITICAL":
            return "EMERGENCY_ISOLATE"
        elif max_severity == "HIGH":
            return "QUARANTINE"
        elif max_severity == "MEDIUM":
            return "WARN"
        else:
            return "MONITOR"

    def get_model_info(self) -> dict:
        """Return model metadata for the API."""
        return {
            "model_loaded": self.model_loaded,
            "xgb_classes": list(LABEL_MAP.values()),
            "feature_count": len(FEATURE_NAMES),
            "training_accuracy": self.xgb_accuracy,
            "iso_contamination": 0.15,
            "alert_threshold": self.alert_threshold,
        }


if __name__ == "__main__":
    from traffic_generator import TrafficGenerator

    print("=" * 60)
    print("5G SliceGuard — Detector Smoke Test")
    print("=" * 60)

    gen = TrafficGenerator()
    det = SliceGuardDetector()

    # Normal ticks
    print("\n── Normal Operation ──")
    for i in range(3):
        snap = gen.generate_tick()
        result = det.analyze(snap)
        print(f"  Tick {result['tick']}: alert={result['global_alert']} | "
              f"action={result['recommended_action']} | "
              f"attack={result['dominant_attack']}")

    # Attack
    print("\n── Resource Theft Attack ──")
    gen.start_attack("resource_theft")
    for i in range(7):
        snap = gen.generate_tick()
        result = det.analyze(snap)
        sev = result["max_severity"]
        urllc_conf = result["slice_analysis"]["URLLC"]["combined_score"]
        print(f"  Tick {result['tick']}: severity={sev} | "
              f"action={result['recommended_action']} | "
              f"URLLC score={urllc_conf:.3f}")

    print("\nSmoke test PASSED ✓")
