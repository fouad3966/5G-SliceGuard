"""
5G SliceGuard — Model Trainer
==============================
Trains two complementary ML models on the labeled traffic dataset:

1. XGBoost Classifier (supervised) — 4-class: normal + 3 attack types
   → High accuracy on KNOWN attack patterns

2. Isolation Forest (unsupervised) — trained on normal-only data
   → Catches UNKNOWN / zero-day attacks by flagging anything that
     doesn't look like normal traffic

Saves models to simulation/model/ directory.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

from feature_extractor import FeatureExtractor, FEATURE_NAMES

# ── Configuration ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "labeled_traffic.csv")
MODEL_DIR = os.path.join(SCRIPT_DIR, "model")

LABEL_MAP = {0: "normal", 1: "resource_theft", 2: "data_injection", 3: "side_channel"}


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Process the raw CSV through FeatureExtractor to create
    the same features that the real-time detector will use.
    This ensures training and inference use identical feature sets.
    """
    fe = FeatureExtractor(window_size=10)
    feature_rows = []

    # Sort by timestamp to simulate temporal order
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)

    for _, row in df_sorted.iterrows():
        metrics = {
            "slice_id": int(row["slice_id"]),
            "bandwidth_mbps": float(row["bandwidth_mbps"]),
            "latency_ms": float(row["latency_ms"]),
            "packet_rate_pps": float(row["packet_rate_pps"]),
            "cpu_usage_pct": float(row["cpu_usage_pct"]),
            "memory_usage_pct": float(row["memory_usage_pct"]),
            "jitter_ms": float(row["jitter_ms"]),
            "drop_rate_pct": float(row["drop_rate_pct"]),
            "cross_slice_score": float(row["cross_slice_score"]),
        }
        extracted = fe.extract(metrics)
        vector = fe.get_feature_vector(extracted)
        feature_rows.append(vector)

    X = np.array(feature_rows)
    y = df_sorted["label"].values
    return X, y


def train():
    """Train both models and save to disk."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Load dataset ───────────────────────────────────────────
    print("Loading dataset...")
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        print("Run generate_dataset.py first!")
        return

    df = pd.read_csv(DATASET_PATH)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # ── Extract features ───────────────────────────────────────
    print("\nExtracting features (running through FeatureExtractor)...")
    X, y = prepare_features(df)
    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Feature names: {FEATURE_NAMES}")

    # ── Train/test split ───────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")

    # ══════════════════════════════════════════════════════════
    # MODEL 1: XGBoost Classifier (supervised, 4-class)
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Training XGBoost Classifier...")
    print("=" * 60)

    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
    )
    xgb.fit(X_train, y_train)

    # Evaluate
    y_pred = xgb.predict(X_test)
    xgb_accuracy = np.mean(y_pred == y_test)

    print(f"\nXGBoost Accuracy: {xgb_accuracy:.4f}")
    print("\nClassification Report:")
    target_names = [LABEL_MAP[i] for i in sorted(LABEL_MAP.keys())]
    print(classification_report(y_test, y_pred, target_names=target_names))

    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Save XGBoost
    xgb_path = os.path.join(MODEL_DIR, "xgb_model.pkl")
    joblib.dump(xgb, xgb_path)
    print(f"\nXGBoost model saved to: {xgb_path}")

    # ══════════════════════════════════════════════════════════
    # MODEL 2: Isolation Forest (unsupervised, anomaly detection)
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Training Isolation Forest (on normal data only)...")
    print("=" * 60)

    # Train only on normal traffic — the model learns what "normal" looks like
    X_normal = X_train[y_train == 0]
    print(f"  Normal training samples: {len(X_normal)}")

    iso = IsolationForest(
        contamination=0.15,
        n_estimators=100,
        random_state=42,
    )
    iso.fit(X_normal)

    # Evaluate on test set
    iso_scores = iso.decision_function(X_test)
    iso_preds = iso.predict(X_test)  # 1 = normal, -1 = anomaly
    # Anomaly rate on actual attacks
    attack_mask = y_test != 0
    iso_anomaly_recall = np.mean(iso_preds[attack_mask] == -1)

    print(f"\nIsolation Forest anomaly recall on attacks: {iso_anomaly_recall:.4f}")
    print(f"  (Correctly flagged {iso_anomaly_recall*100:.1f}% of attack samples as anomalous)")

    # Save Isolation Forest
    iso_path = os.path.join(MODEL_DIR, "iso_forest.pkl")
    joblib.dump(iso, iso_path)
    print(f"\nIsolation Forest saved to: {iso_path}")

    # ── Save feature column order ──────────────────────────────
    columns_path = os.path.join(MODEL_DIR, "feature_columns.json")
    meta = {
        "feature_columns": FEATURE_NAMES,
        "label_map": LABEL_MAP,
        "xgb_accuracy": float(xgb_accuracy),
        "iso_anomaly_recall": float(iso_anomaly_recall),
        "training_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
    }
    with open(columns_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Feature columns & metadata saved to: {columns_path}")

    # ── Final summary ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"Training complete.")
    print(f"  XGB accuracy:         {xgb_accuracy:.4f}")
    print(f"  ISO anomaly recall:   {iso_anomaly_recall:.4f}")
    print(f"  Models saved to:      {MODEL_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    train()
