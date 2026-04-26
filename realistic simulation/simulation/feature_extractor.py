"""
5G SliceGuard — Feature Extractor
===================================
Extracts ML-ready feature vectors from raw slice metrics.
Maintains a rolling window per slice to compute temporal features
like rolling means, standard deviations, and deltas.
"""

from collections import deque
import numpy as np


# Ordered list of feature names — MUST match training column order
FEATURE_NAMES = [
    "slice_id",
    "bandwidth_mbps", "latency_ms", "packet_rate_pps",
    "cpu_usage_pct", "memory_usage_pct",
    "jitter_ms", "drop_rate_pct", "cross_slice_score",
    # Rolling statistics
    "bandwidth_mean_10", "bandwidth_std_10",
    "latency_mean_10", "latency_std_10",
    "cpu_mean_10", "cpu_std_10",
    # Deltas (change from previous reading)
    "bandwidth_delta", "latency_delta", "cpu_delta",
    # Composite features
    "latency_bandwidth_ratio",
    "resource_pressure",
]


class FeatureExtractor:
    """
    Extracts ML features from raw slice metrics.

    Maintains per-slice rolling windows to compute temporal statistics.
    These temporal features are critical for detecting attacks that
    manifest as sudden changes rather than absolute value anomalies.
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        # Per-slice rolling history buffers
        self.history = {
            0: {"bandwidth": deque(maxlen=window_size),
                "latency": deque(maxlen=window_size),
                "cpu": deque(maxlen=window_size)},
            1: {"bandwidth": deque(maxlen=window_size),
                "latency": deque(maxlen=window_size),
                "cpu": deque(maxlen=window_size)},
            2: {"bandwidth": deque(maxlen=window_size),
                "latency": deque(maxlen=window_size),
                "cpu": deque(maxlen=window_size)},
        }
        # Previous reading per slice (for delta computation)
        self.prev = {0: {}, 1: {}, 2: {}}

    def extract(self, slice_metrics: dict) -> dict:
        """
        Extract feature dict from raw slice metrics.

        Args:
            slice_metrics: dict with keys like bandwidth_mbps, latency_ms, etc.

        Returns:
            dict with all raw features plus derived temporal/composite features.
        """
        sid = int(slice_metrics.get("slice_id", 0))
        hist = self.history[sid]

        bw = slice_metrics.get("bandwidth_mbps", 0)
        lat = slice_metrics.get("latency_ms", 0)
        cpu = slice_metrics.get("cpu_usage_pct", 0)

        # Update rolling windows
        hist["bandwidth"].append(bw)
        hist["latency"].append(lat)
        hist["cpu"].append(cpu)

        # Compute rolling statistics
        bw_arr = np.array(hist["bandwidth"])
        lat_arr = np.array(hist["latency"])
        cpu_arr = np.array(hist["cpu"])

        features = {
            # Raw features
            "slice_id": sid,
            "bandwidth_mbps": bw,
            "latency_ms": lat,
            "packet_rate_pps": slice_metrics.get("packet_rate_pps", 0),
            "cpu_usage_pct": cpu,
            "memory_usage_pct": slice_metrics.get("memory_usage_pct", 0),
            "jitter_ms": slice_metrics.get("jitter_ms", 0),
            "drop_rate_pct": slice_metrics.get("drop_rate_pct", 0),
            "cross_slice_score": slice_metrics.get("cross_slice_score", 0),

            # Rolling window statistics (10-tick window)
            "bandwidth_mean_10": float(np.mean(bw_arr)),
            "bandwidth_std_10": float(np.std(bw_arr)) if len(bw_arr) > 1 else 0.0,
            "latency_mean_10": float(np.mean(lat_arr)),
            "latency_std_10": float(np.std(lat_arr)) if len(lat_arr) > 1 else 0.0,
            "cpu_mean_10": float(np.mean(cpu_arr)),
            "cpu_std_10": float(np.std(cpu_arr)) if len(cpu_arr) > 1 else 0.0,

            # Deltas (rate of change)
            "bandwidth_delta": bw - self.prev[sid].get("bandwidth", bw),
            "latency_delta": lat - self.prev[sid].get("latency", lat),
            "cpu_delta": cpu - self.prev[sid].get("cpu", cpu),

            # Composite anomaly indicators
            "latency_bandwidth_ratio": (lat / bw) if bw > 0 else 0,
            "resource_pressure": (cpu * slice_metrics.get("memory_usage_pct", 0)) / 10000.0,
        }

        # Store current values for next delta computation
        self.prev[sid] = {"bandwidth": bw, "latency": lat, "cpu": cpu}

        return features

    def get_feature_vector(self, extracted: dict) -> list:
        """
        Convert extracted feature dict to ordered numeric list.
        Order MUST match FEATURE_NAMES and training column order.
        """
        return [float(extracted.get(name, 0)) for name in FEATURE_NAMES]

    def reset(self):
        """Clear all history buffers."""
        for sid in self.history:
            for key in self.history[sid]:
                self.history[sid][key].clear()
            self.prev[sid] = {}


if __name__ == "__main__":
    # Quick smoke test
    print("=" * 60)
    print("5G SliceGuard — Feature Extractor Smoke Test")
    print("=" * 60)

    fe = FeatureExtractor(window_size=10)

    # Simulate 15 ticks of eMBB traffic
    for i in range(15):
        sample = {
            "slice_id": 0,
            "bandwidth_mbps": 800 + np.random.normal(0, 30),
            "latency_ms": 4 + np.random.normal(0, 0.3),
            "packet_rate_pps": 5000 + np.random.normal(0, 200),
            "cpu_usage_pct": 35 + np.random.normal(0, 5),
            "memory_usage_pct": 40 + np.random.normal(0, 5),
            "jitter_ms": 0.5 + np.random.normal(0, 0.1),
            "drop_rate_pct": 0.1 + np.random.normal(0, 0.05),
            "cross_slice_score": 0.02 + np.random.normal(0, 0.01),
        }
        features = fe.extract(sample)
        vector = fe.get_feature_vector(features)

        if i == 14:
            print(f"\nTick {i+1} — Extracted {len(FEATURE_NAMES)} features:")
            for name, val in zip(FEATURE_NAMES, vector):
                print(f"  {name:30s} = {val:.4f}")

    print(f"\nFeature vector length: {len(FEATURE_NAMES)}")
    print("Smoke test PASSED ✓")
