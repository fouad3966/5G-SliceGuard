"""
5G SliceGuard — Traffic Generator
===================================
Continuously generates realistic per-slice traffic metrics.
Supports injecting attacks on-demand with gradual intensity ramping.

This is the "heartbeat" of the simulation — every tick produces
metrics for all 3 slices (eMBB, URLLC, mMTC) with realistic
Gaussian noise around documented 5G baselines.

Attack effects are applied as multipliers/offsets that ramp up
over 5 ticks and ramp down instantly on quarantine.
"""

import time
import math
from collections import deque
import numpy as np


class TrafficGenerator:
    """
    Generates realistic 5G slice traffic metrics.

    Normal operation produces metrics around 3GPP-documented baselines.
    When an attack is triggered, the affected slices' metrics degrade
    proportionally to the attack intensity (0→1 ramp over 5 ticks).
    """

    # Slice baselines: (mean, std) for Gaussian generation
    BASELINES = {
        "eMBB": {
            "bandwidth_mbps": (800, 30),
            "latency_ms": (4.0, 0.3),
            "packet_rate_pps": (5000, 200),
            "cpu_usage_pct": (35, 5),
            "memory_usage_pct": (40, 5),
            "jitter_ms": (0.5, 0.1),
            "drop_rate_pct": (0.1, 0.05),
            "cross_slice_score": (0.02, 0.01),
        },
        "URLLC": {
            "bandwidth_mbps": (200, 10),
            "latency_ms": (0.8, 0.05),
            "packet_rate_pps": (1000, 50),
            "cpu_usage_pct": (20, 3),
            "memory_usage_pct": (25, 3),
            "jitter_ms": (0.05, 0.01),
            "drop_rate_pct": (0.01, 0.005),
            "cross_slice_score": (0.01, 0.005),
        },
        "mMTC": {
            "bandwidth_mbps": (200, 15),
            "latency_ms": (10.0, 1.0),
            "packet_rate_pps": (500, 30),
            "cpu_usage_pct": (15, 2),
            "memory_usage_pct": (20, 3),
            "jitter_ms": (1.0, 0.2),
            "drop_rate_pct": (0.5, 0.1),
            "cross_slice_score": (0.03, 0.01),
        },
    }

    SLICE_NAMES = ["eMBB", "URLLC", "mMTC"]

    def __init__(self):
        self.attack_active = None       # None or "resource_theft" / "data_injection" / "side_channel"
        self.attack_target = None       # Which slice is primary target
        self.attack_intensity = 0.0     # 0–1, ramps up over 5 ticks
        self.tick_count = 0
        self.start_time = time.time()
        self.history = deque(maxlen=100)
        self._attack_tick = 0           # Ticks since attack started

    def generate_tick(self) -> dict:
        """
        Generate one tick of traffic data for all 3 slices.

        Returns a snapshot dict with timestamp, tick number,
        per-slice metrics, and current attack state.
        """
        self.tick_count += 1

        # Generate base metrics per slice
        slices = {}
        for name in self.SLICE_NAMES:
            slices[name] = self._generate_normal(name)

        # If an attack is active, ramp intensity and apply effects
        if self.attack_active:
            self._attack_tick += 1
            # Ramp up over 5 ticks (0.2 per tick)
            self.attack_intensity = min(1.0, self._attack_tick * 0.2)
            slices = self._apply_attack_effects(slices)

        # Clip all values to physical bounds
        for name in self.SLICE_NAMES:
            slices[name] = self._clip(slices[name])

        snapshot = {
            "timestamp": time.time(),
            "tick": self.tick_count,
            "slices": slices,
            "attack_active": self.attack_active,
            "attack_intensity": self.attack_intensity,
        }

        self.history.append(snapshot)
        return snapshot

    def start_attack(self, attack_type: str):
        """Begin an attack. Intensity ramps up gradually over 5 ticks."""
        valid_types = ["resource_theft", "data_injection", "side_channel"]
        if attack_type not in valid_types:
            raise ValueError(f"Unknown attack type: {attack_type}. Valid: {valid_types}")

        self.attack_active = attack_type
        self.attack_intensity = 0.0
        self._attack_tick = 0

        if attack_type == "resource_theft":
            self.attack_target = "mMTC"  # Attacker slice
        elif attack_type == "data_injection":
            self.attack_target = "URLLC"  # Victim slice
        else:
            self.attack_target = "mMTC"  # Side-channel observer

    def stop_attack(self):
        """Immediately stop the attack (quarantine response)."""
        self.attack_active = None
        self.attack_target = None
        self.attack_intensity = 0.0
        self._attack_tick = 0

    def _generate_normal(self, slice_name: str) -> dict:
        """Generate normal traffic metrics with Gaussian noise."""
        profile = self.BASELINES[slice_name]
        metrics = {}
        for metric, (mean, std) in profile.items():
            metrics[metric] = np.random.normal(mean, std)
        return metrics

    def _apply_attack_effects(self, slices: dict) -> dict:
        """
        Modify slice metrics based on active attack type and intensity.

        Attack effects are multiplicative/additive modifiers proportional
        to the current intensity (0–1). This simulates the gradual
        degradation that real cross-slice attacks produce.
        """
        intensity = self.attack_intensity

        if self.attack_active == "resource_theft":
            # ── Resource Theft ──────────────────────────────────
            # Attacker (mMTC) floods CPU/bandwidth (matches dataset: bw~1800, cpu~85, pps~15000)
            slices["mMTC"]["bandwidth_mbps"] *= (1 + 8.0 * intensity)  # 200 * 9 = 1800
            slices["mMTC"]["cpu_usage_pct"] += 70.0 * intensity        # 15 + 70 = 85
            slices["mMTC"]["packet_rate_pps"] *= (1 + 29.0 * intensity)# 500 * 30 = 15000
            slices["mMTC"]["memory_usage_pct"] += 50.0 * intensity     # 20 + 50 = 70
            slices["mMTC"]["cross_slice_score"] += 0.4 * intensity

            # Victim (URLLC) — resource starvation → latency spike (matches dataset: lat~4.5, cpu~60)
            slices["URLLC"]["bandwidth_mbps"] *= (1 - 0.25 * intensity)# 200 * 0.75 = 150
            slices["URLLC"]["latency_ms"] += 3.7 * intensity           # 0.8 + 3.7 = ~4.5
            slices["URLLC"]["cpu_usage_pct"] += 40.0 * intensity       # 20 + 40 = 60
            slices["URLLC"]["jitter_ms"] += 1.45 * intensity           # 0.05 + 1.45 = 1.5
            slices["URLLC"]["drop_rate_pct"] += 3.0 * intensity        # 0.01 + 3.0 = ~3.0
            slices["URLLC"]["cross_slice_score"] += 0.3 * intensity

            # Secondary victim (eMBB) — bandwidth starved
            slices["eMBB"]["bandwidth_mbps"] *= (1 - 0.3 * intensity)
            slices["eMBB"]["latency_ms"] *= (1 + 0.5 * intensity)

        elif self.attack_active == "data_injection":
            # ── Data Injection ──────────────────────────────────
            # Malicious packets injected directly into URLLC data plane
            slices["URLLC"]["drop_rate_pct"] += 15 * intensity
            slices["URLLC"]["jitter_ms"] += 3.0 * intensity
            slices["URLLC"]["cross_slice_score"] = min(1.0, 0.3 + 0.7 * intensity)
            slices["URLLC"]["latency_ms"] *= (1 + 1.5 * intensity)

            # mMTC shows slight anomaly (injection source)
            slices["mMTC"]["cross_slice_score"] = min(1.0, 0.1 + 0.4 * intensity)

        elif self.attack_active == "side_channel":
            # ── Side-Channel ────────────────────────────────────
            # Subtle: periodic jitter + CPU ripple across all slices
            tick = self.tick_count
            for name in self.SLICE_NAMES:
                slices[name]["jitter_ms"] += math.sin(tick * 0.5) * 0.1 * intensity

            # mMTC: tiny periodic CPU ripple (covert channel signature)
            slices["mMTC"]["cpu_usage_pct"] += math.sin(tick * 0.5) * 3.0 * intensity
            # Subtle cross-slice correlation
            slices["mMTC"]["cross_slice_score"] = 0.1 + 0.2 * intensity
            slices["URLLC"]["cross_slice_score"] = 0.05 + 0.1 * intensity

        return slices

    def _clip(self, metrics: dict) -> dict:
        """Clip metrics to physically realistic ranges."""
        metrics["bandwidth_mbps"] = max(0, metrics["bandwidth_mbps"])
        metrics["latency_ms"] = max(0.01, metrics["latency_ms"])
        metrics["packet_rate_pps"] = max(0, metrics["packet_rate_pps"])
        metrics["cpu_usage_pct"] = np.clip(metrics["cpu_usage_pct"], 0, 100)
        metrics["memory_usage_pct"] = np.clip(metrics["memory_usage_pct"], 0, 100)
        metrics["jitter_ms"] = max(0, metrics["jitter_ms"])
        metrics["drop_rate_pct"] = np.clip(metrics["drop_rate_pct"], 0, 100)
        metrics["cross_slice_score"] = np.clip(metrics["cross_slice_score"], 0, 1)
        return metrics


# Module-level singleton for import convenience
generator = TrafficGenerator()


if __name__ == "__main__":
    print("=" * 60)
    print("5G SliceGuard — Traffic Generator Smoke Test")
    print("=" * 60)

    gen = TrafficGenerator()

    # Normal ticks
    print("\n── Normal Operation (5 ticks) ──")
    for i in range(5):
        snap = gen.generate_tick()
        urllc_lat = snap["slices"]["URLLC"]["latency_ms"]
        mmtc_cpu = snap["slices"]["mMTC"]["cpu_usage_pct"]
        print(f"  Tick {snap['tick']}: URLLC lat={urllc_lat:.3f}ms | mMTC CPU={mmtc_cpu:.1f}%")

    # Launch resource theft
    print("\n── Resource Theft Attack (5 ticks) ──")
    gen.start_attack("resource_theft")
    for i in range(5):
        snap = gen.generate_tick()
        urllc_lat = snap["slices"]["URLLC"]["latency_ms"]
        mmtc_cpu = snap["slices"]["mMTC"]["cpu_usage_pct"]
        intensity = snap["attack_intensity"]
        print(f"  Tick {snap['tick']}: URLLC lat={urllc_lat:.3f}ms | mMTC CPU={mmtc_cpu:.1f}% | intensity={intensity:.1f}")

    # Quarantine
    print("\n── Quarantine (3 ticks) ──")
    gen.stop_attack()
    for i in range(3):
        snap = gen.generate_tick()
        urllc_lat = snap["slices"]["URLLC"]["latency_ms"]
        mmtc_cpu = snap["slices"]["mMTC"]["cpu_usage_pct"]
        print(f"  Tick {snap['tick']}: URLLC lat={urllc_lat:.3f}ms | mMTC CPU={mmtc_cpu:.1f}% | RESTORED")

    print("\nSmoke test PASSED ✓")
