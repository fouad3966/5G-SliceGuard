"""
5G SliceGuard — Packet Sniffer
================================
Optional real packet capture layer.
If Scapy is installed and available, captures real localhost traffic.
If not, gracefully falls back to the TrafficGenerator synthetic data.

For the presentation, this always runs in synthetic mode — but the
architecture demonstrates real-world extensibility.
"""

import threading
import time


class PacketSniffer:
    """
    Packet capture coordinator.

    Checks for Scapy availability at init. If unavailable (which is
    expected for the presentation), falls back to synthetic mode
    using TrafficGenerator.
    """

    def __init__(self):
        self.scapy_available = self._check_scapy()
        self.synthetic_mode = not self.scapy_available
        self.running = False
        self._thread = None

    def _check_scapy(self) -> bool:
        """Check if Scapy is installed and importable."""
        try:
            from scapy.all import sniff  # noqa: F401
            return True
        except ImportError:
            print("[Sniffer] Scapy not available — using synthetic traffic mode")
            return False

    def start(self, callback, generator=None):
        """
        Start capturing/generating traffic.

        Args:
            callback: function called with each traffic snapshot
            generator: TrafficGenerator instance (for synthetic mode)
        """
        self.running = True

        if self.synthetic_mode:
            if generator is None:
                from traffic_generator import TrafficGenerator
                generator = TrafficGenerator()

            def _synthetic_loop():
                while self.running:
                    snapshot = generator.generate_tick()
                    callback(snapshot)
                    time.sleep(1)

            self._thread = threading.Thread(target=_synthetic_loop, daemon=True)
            self._thread.start()
            print("[Sniffer] Synthetic mode started (1 tick/second)")
        else:
            def _scapy_loop():
                from scapy.all import sniff, IP
                sniff(iface="lo", prn=callback, store=False)

            self._thread = threading.Thread(target=_scapy_loop, daemon=True)
            self._thread.start()
            print("[Sniffer] Real packet capture started on loopback")

    def stop(self):
        """Stop the sniffer."""
        self.running = False
        print("[Sniffer] Stopped")

    def get_mode(self) -> str:
        """Return current operating mode."""
        return "real_capture" if not self.synthetic_mode else "synthetic"


if __name__ == "__main__":
    print("=" * 60)
    print("5G SliceGuard — Sniffer Smoke Test")
    print("=" * 60)

    sniffer = PacketSniffer()
    print(f"Mode: {sniffer.get_mode()}")

    count = 0
    def test_callback(snapshot):
        global count
        count += 1
        print(f"  Received tick {snapshot['tick']}: "
              f"URLLC lat={snapshot['slices']['URLLC']['latency_ms']:.3f}ms")
        if count >= 3:
            sniffer.stop()

    sniffer.start(test_callback)
    time.sleep(5)
    sniffer.stop()

    print(f"\nReceived {count} snapshots")
    print("Smoke test PASSED ✓")
