"""
5G SliceGuard — Slice Analyzer
================================
Aggregates per-slice statistics over configurable time windows.
Provides rolling averages, trends, SLA status, and time series
data for the dashboard charts.
"""

from collections import deque
import numpy as np


class SliceAnalyzer:
    """
    Aggregates slice metrics over multiple time windows and provides
    trend analysis, SLA monitoring, and chart-ready time series data.
    """

    METRIC_KEYS = [
        "bandwidth_mbps", "latency_ms", "packet_rate_pps",
        "cpu_usage_pct", "memory_usage_pct",
        "jitter_ms", "drop_rate_pct", "cross_slice_score",
    ]

    SLICE_NAMES = ["eMBB", "URLLC", "mMTC"]

    # SLA thresholds per slice
    SLA_RULES = {
        "eMBB":  {"metric": "bandwidth_mbps", "threshold": 600, "direction": "above", "label": "DEGRADED"},
        "URLLC": {"metric": "latency_ms",     "threshold": 2.0, "direction": "below", "label": "CRITICAL"},
        "mMTC":  {"metric": "packet_rate_pps", "threshold": 300, "direction": "above", "label": "DEGRADED"},
    }

    def __init__(self, window_sizes=None):
        if window_sizes is None:
            window_sizes = [10, 50, 100]
        self.window_sizes = window_sizes
        self.max_window = max(window_sizes)

        # Per-slice, per-metric history buffers
        self.buffers = {}
        for name in self.SLICE_NAMES:
            self.buffers[name] = {}
            for metric in self.METRIC_KEYS:
                self.buffers[name][metric] = deque(maxlen=self.max_window)

        # Timestamp buffer
        self.timestamps = deque(maxlen=self.max_window)
        self.tick_count = 0

    def update(self, snapshot: dict):
        """
        Add a new tick's data to all buffers.

        Args:
            snapshot: output from TrafficGenerator.generate_tick()
        """
        self.tick_count += 1
        self.timestamps.append(snapshot.get("timestamp", 0))

        for name in self.SLICE_NAMES:
            slice_data = snapshot["slices"].get(name, {})
            for metric in self.METRIC_KEYS:
                value = slice_data.get(metric, 0)
                self.buffers[name][metric].append(float(value))

    def get_summary(self) -> dict:
        """
        Get aggregated summary for all slices.

        Returns per-slice:
          - current: latest metric values
          - avg_10, avg_50: rolling averages
          - trend: STABLE / DEGRADING / RECOVERING
          - sla_status: OK / DEGRADED / CRITICAL
        """
        summary = {}

        for name in self.SLICE_NAMES:
            current = {}
            avg_10 = {}
            avg_50 = {}

            for metric in self.METRIC_KEYS:
                buf = list(self.buffers[name][metric])
                current[metric] = buf[-1] if buf else 0

                last_10 = buf[-10:] if len(buf) >= 10 else buf
                last_50 = buf[-50:] if len(buf) >= 50 else buf

                avg_10[metric] = float(np.mean(last_10)) if last_10 else 0
                avg_50[metric] = float(np.mean(last_50)) if last_50 else 0

            # Trend detection (based on latency for URLLC, bandwidth for others)
            trend_metric = "latency_ms" if name == "URLLC" else "bandwidth_mbps"
            trend = self._compute_trend(name, trend_metric)

            # SLA status
            sla = self._check_sla(name, current)

            summary[name] = {
                "current": current,
                "avg_10": avg_10,
                "avg_50": avg_50,
                "trend": trend,
                "sla_status": sla,
            }

        return summary

    def get_time_series(self, slice_name: str, metric: str, n: int = 50) -> list:
        """
        Get last N values of a specific metric for chart rendering.

        Args:
            slice_name: "eMBB", "URLLC", or "mMTC"
            metric: one of METRIC_KEYS
            n: number of values to return

        Returns:
            List of float values (most recent last)
        """
        if slice_name not in self.buffers:
            return []
        if metric not in self.buffers[slice_name]:
            return []

        buf = list(self.buffers[slice_name][metric])
        return buf[-n:]

    def get_timestamps(self, n: int = 50) -> list:
        """Get last N timestamps for chart x-axis."""
        return list(self.timestamps)[-n:]

    def _compute_trend(self, slice_name: str, metric: str) -> str:
        """
        Determine if a slice's key metric is stable, degrading, or recovering.
        Compares last-10 average to last-50 average.
        """
        buf = list(self.buffers[slice_name][metric])
        if len(buf) < 20:
            return "STABLE"

        avg_recent = np.mean(buf[-10:])
        avg_long = np.mean(buf[-50:]) if len(buf) >= 50 else np.mean(buf)

        # For latency: higher recent = degrading
        # For bandwidth: lower recent = degrading
        if metric == "latency_ms":
            ratio = avg_recent / avg_long if avg_long > 0 else 1
            if ratio > 1.3:
                return "DEGRADING"
            elif ratio < 0.8:
                return "RECOVERING"
        else:
            ratio = avg_recent / avg_long if avg_long > 0 else 1
            if ratio < 0.7:
                return "DEGRADING"
            elif ratio > 1.2:
                return "RECOVERING"

        return "STABLE"

    def _check_sla(self, slice_name: str, current: dict) -> str:
        """Check if a slice meets its SLA requirements."""
        rule = self.SLA_RULES.get(slice_name)
        if not rule:
            return "OK"

        value = current.get(rule["metric"], 0)

        if rule["direction"] == "above":
            return "OK" if value > rule["threshold"] else rule["label"]
        else:  # "below"
            return "OK" if value < rule["threshold"] else rule["label"]


if __name__ == "__main__":
    from traffic_generator import TrafficGenerator

    print("=" * 60)
    print("5G SliceGuard — Analyzer Smoke Test")
    print("=" * 60)

    gen = TrafficGenerator()
    analyzer = SliceAnalyzer()

    # Feed 20 ticks
    for i in range(20):
        snap = gen.generate_tick()
        analyzer.update(snap)

    summary = analyzer.get_summary()
    for name in ["eMBB", "URLLC", "mMTC"]:
        s = summary[name]
        print(f"\n{name}:")
        print(f"  Trend: {s['trend']} | SLA: {s['sla_status']}")
        print(f"  Current latency:   {s['current']['latency_ms']:.3f}ms")
        print(f"  Avg-10 latency:    {s['avg_10']['latency_ms']:.3f}ms")
        print(f"  Current bandwidth: {s['current']['bandwidth_mbps']:.1f}Mbps")

    ts = analyzer.get_time_series("URLLC", "latency_ms", n=10)
    print(f"\nURLLC latency time series (last 10): {[f'{v:.3f}' for v in ts]}")

    print("\nSmoke test PASSED ✓")
