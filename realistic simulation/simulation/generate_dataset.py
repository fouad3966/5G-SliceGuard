"""
5G SliceGuard — Dataset Generator
==================================
Generates a realistic labeled CSV dataset of 5G network slice traffic.
Produces 10,000 rows with Gaussian-distributed metrics per slice type,
including normal traffic and three attack classes.

Classes:
  0 = normal
  1 = resource_theft
  2 = data_injection
  3 = side_channel
"""

import os
import random
import math
import numpy as np
import pandas as pd

# ── Reproducibility ────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# ── Configuration ──────────────────────────────────────────────────
NUM_ROWS = 10_000
NORMAL_RATIO = 0.70
ATTACK_RATIOS = {1: 0.10, 2: 0.10, 3: 0.10}  # resource_theft, data_injection, side_channel

LABEL_MAP = {0: "normal", 1: "resource_theft", 2: "data_injection", 3: "side_channel"}

# Slice baselines (mean, std) for normal traffic
SLICE_PROFILES = {
    0: {  # eMBB — high bandwidth, moderate latency
        "bandwidth_mbps": (800, 30),
        "latency_ms": (4, 0.3),
        "packet_rate_pps": (5000, 200),
        "cpu_usage_pct": (35, 5),
        "memory_usage_pct": (40, 5),
        "jitter_ms": (0.5, 0.1),
        "drop_rate_pct": (0.1, 0.05),
        "cross_slice_score": (0.02, 0.01),
    },
    1: {  # URLLC — low latency critical
        "bandwidth_mbps": (200, 10),
        "latency_ms": (0.8, 0.05),
        "packet_rate_pps": (1000, 50),
        "cpu_usage_pct": (20, 3),
        "memory_usage_pct": (25, 3),
        "jitter_ms": (0.05, 0.01),
        "drop_rate_pct": (0.01, 0.005),
        "cross_slice_score": (0.01, 0.005),
    },
    2: {  # mMTC — IoT, many devices
        "bandwidth_mbps": (200, 15),
        "latency_ms": (10, 1),
        "packet_rate_pps": (500, 30),
        "cpu_usage_pct": (15, 2),
        "memory_usage_pct": (20, 3),
        "jitter_ms": (1.0, 0.2),
        "drop_rate_pct": (0.5, 0.1),
        "cross_slice_score": (0.03, 0.01),
    },
}


def clip_metrics(row: dict) -> dict:
    """Clip all values to realistic physical ranges."""
    row["bandwidth_mbps"] = max(0, row["bandwidth_mbps"])
    row["latency_ms"] = max(0.01, row["latency_ms"])
    row["packet_rate_pps"] = max(0, row["packet_rate_pps"])
    row["cpu_usage_pct"] = np.clip(row["cpu_usage_pct"], 0, 100)
    row["memory_usage_pct"] = np.clip(row["memory_usage_pct"], 0, 100)
    row["jitter_ms"] = max(0, row["jitter_ms"])
    row["drop_rate_pct"] = np.clip(row["drop_rate_pct"], 0, 100)
    row["cross_slice_score"] = np.clip(row["cross_slice_score"], 0, 1)
    return row


def generate_normal(slice_id: int, t: float) -> dict:
    """Generate one row of normal traffic for a given slice."""
    profile = SLICE_PROFILES[slice_id]
    row = {"slice_id": slice_id}
    for metric, (mean, std) in profile.items():
        row[metric] = np.random.normal(mean, std)
    return clip_metrics(row)


def generate_resource_theft(t: float) -> dict:
    """
    Resource theft: mMTC slice floods resources.
    Attacker (mMTC) consumes excessive bandwidth/CPU.
    Victim (URLLC) suffers latency spikes from resource starvation.
    """
    # Randomly pick whether this row is the attacker or victim perspective
    if np.random.random() < 0.5:
        # Attacker slice (mMTC) — inflated resource usage
        row = {"slice_id": 2}
        row["bandwidth_mbps"] = np.random.normal(1800, 100)
        row["latency_ms"] = np.random.normal(10, 1)
        row["packet_rate_pps"] = np.random.normal(15000, 500)
        row["cpu_usage_pct"] = np.random.normal(85, 5)
        row["memory_usage_pct"] = np.random.normal(70, 8)
        row["jitter_ms"] = np.random.normal(2.0, 0.3)
        row["drop_rate_pct"] = np.random.normal(1.0, 0.3)
        row["cross_slice_score"] = np.random.uniform(0.3, 0.6)
    else:
        # Victim slice (URLLC) — resource-starved
        row = {"slice_id": 1}
        row["bandwidth_mbps"] = np.random.normal(150, 20)
        row["latency_ms"] = np.random.normal(4.5, 0.5)
        row["packet_rate_pps"] = np.random.normal(800, 100)
        row["cpu_usage_pct"] = np.random.normal(60, 8)
        row["memory_usage_pct"] = np.random.normal(55, 8)
        row["jitter_ms"] = np.random.normal(1.5, 0.3)
        row["drop_rate_pct"] = np.random.normal(3.0, 0.5)
        row["cross_slice_score"] = np.random.uniform(0.2, 0.5)

    return clip_metrics(row)


def generate_data_injection(t: float) -> dict:
    """
    Data injection: malicious packets injected into URLLC data plane.
    URLLC sees high cross-slice score, packet drops, jitter spikes.
    """
    row = {"slice_id": 1}  # URLLC is always the victim
    row["bandwidth_mbps"] = np.random.normal(180, 15)
    row["latency_ms"] = np.random.normal(1.5, 0.3)
    row["packet_rate_pps"] = np.random.normal(1200, 100)
    row["cpu_usage_pct"] = np.random.normal(30, 5)
    row["memory_usage_pct"] = np.random.normal(35, 5)
    row["jitter_ms"] = np.random.normal(3.0, 0.5)
    row["drop_rate_pct"] = np.random.normal(12, 2)
    row["cross_slice_score"] = np.random.uniform(0.7, 1.0)
    return clip_metrics(row)


def generate_side_channel(t: float) -> dict:
    """
    Side-channel: subtle cache timing / covert channel attack.
    Metrics are near-normal but jitter has micro-patterns and
    CPU shows a subtle periodic sinusoidal signature.
    """
    # Can affect any slice — pick randomly
    slice_id = np.random.choice([0, 1, 2])
    row = generate_normal(slice_id, t)

    # Subtle jitter micro-pattern
    row["jitter_ms"] = np.random.normal(0.15, 0.02)
    # CPU has periodic signature
    row["cpu_usage_pct"] += math.sin(t * 0.5) * 3.0
    # Slightly elevated cross-slice score
    row["cross_slice_score"] = np.random.uniform(0.1, 0.3)

    return clip_metrics(row)


def generate_dataset() -> pd.DataFrame:
    """Generate the full labeled dataset."""
    rows = []
    base_time = 1700000000.0  # Fixed starting Unix timestamp

    n_normal = int(NUM_ROWS * NORMAL_RATIO)
    n_resource = int(NUM_ROWS * ATTACK_RATIOS[1])
    n_injection = int(NUM_ROWS * ATTACK_RATIOS[2])
    n_sidechan = NUM_ROWS - n_normal - n_resource - n_injection

    # ── Normal traffic ──
    for i in range(n_normal):
        t = base_time + i
        slice_id = np.random.choice([0, 1, 2], p=[0.4, 0.3, 0.3])
        row = generate_normal(slice_id, t)
        row["timestamp"] = t
        row["label"] = 0
        rows.append(row)

    # ── Resource Theft ──
    for i in range(n_resource):
        t = base_time + n_normal + i
        row = generate_resource_theft(t)
        row["timestamp"] = t
        row["label"] = 1
        rows.append(row)

    # ── Data Injection ──
    for i in range(n_injection):
        t = base_time + n_normal + n_resource + i
        row = generate_data_injection(t)
        row["timestamp"] = t
        row["label"] = 2
        rows.append(row)

    # ── Side-Channel ──
    for i in range(n_sidechan):
        t = base_time + n_normal + n_resource + n_injection + i
        row = generate_side_channel(t)
        row["timestamp"] = t
        row["label"] = 3
        rows.append(row)

    df = pd.DataFrame(rows)
    # Shuffle rows (deterministic with seed)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Reorder columns
    col_order = [
        "timestamp", "slice_id",
        "bandwidth_mbps", "latency_ms", "packet_rate_pps",
        "cpu_usage_pct", "memory_usage_pct",
        "jitter_ms", "drop_rate_pct", "cross_slice_score",
        "label"
    ]
    df = df[col_order]
    return df


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "labeled_traffic.csv")

    print("=" * 60)
    print("5G SliceGuard — Dataset Generator")
    print("=" * 60)

    df = generate_dataset()
    df.to_csv(output_path, index=False)

    print(f"\nDataset generated: {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nClass distribution:")
    for label_id, count in df["label"].value_counts().sort_index().items():
        print(f"  {label_id} ({LABEL_MAP[label_id]}): {count} rows ({count/len(df)*100:.1f}%)")
    print(f"\nSaved to: {output_path}")
    print("=" * 60)
