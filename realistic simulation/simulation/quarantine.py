"""
5G SliceGuard — Quarantine Engine
===================================
Automated response engine that executes defense actions based on
the detector's verdicts.

When a high-confidence attack is detected:
  1. Instantly stops the attack (calls generator.stop_attack())
  2. Enters quarantine state with a 10-tick restoration countdown
  3. Reports status each tick (QUARANTINE → RESTORING → RESTORED)

This simulates the real-world SMF (Session Management Function)
terminating the compromised device's PDU session.
"""

import time


class QuarantineEngine:
    """
    Automated quarantine and restoration engine.

    Receives analysis results from SliceGuardDetector and executes
    the appropriate response action. Manages the full lifecycle:
    attack detection → quarantine → restoration.
    """

    def __init__(self, generator, detector):
        self.generator = generator
        self.detector = detector
        self.response_log = []          # History of all response events
        self.quarantine_active = False
        self.quarantine_start_time = None
        self.restoration_countdown = 0  # Ticks until full restoration
        self.auto_respond = True        # Toggle for auto vs manual mode

    def respond(self, analysis: dict) -> dict:
        """
        Process detector analysis and take appropriate action.

        Called once per tick after detector.analyze().

        Args:
            analysis: output from SliceGuardDetector.analyze()

        Returns:
            Response dict with action taken, quarantine state, and log.
        """
        action = analysis.get("recommended_action", "MONITOR")
        current_time = time.time()

        # ── Active quarantine: count down to restoration ──
        if self.quarantine_active and self.restoration_countdown > 0:
            self.restoration_countdown -= 1
            progress = ((10 - self.restoration_countdown) / 10.0) * 100

            if self.restoration_countdown == 0:
                # Restoration complete
                self.quarantine_active = False
                self._log_event("RESTORED", analysis, current_time)
                return self._build_response("RESTORED", progress=100)

            return self._build_response("RESTORING", progress=progress)

        # ── Quarantine just finished (edge case: already at 0) ──
        if self.quarantine_active and self.restoration_countdown == 0:
            self.quarantine_active = False
            return self._build_response("RESTORED", progress=100)

        # ── Check if we need to quarantine ──
        if self.auto_respond and action in ("QUARANTINE", "EMERGENCY_ISOLATE"):
            self._execute_quarantine(analysis, current_time)
            return self._build_response("QUARANTINE", progress=0)

        # ── Normal operation ──
        return self._build_response("NONE", progress=0)

    def manual_quarantine(self):
        """Force quarantine regardless of ML verdict."""
        current_time = time.time()
        self.generator.stop_attack()
        self.quarantine_active = True
        self.quarantine_start_time = current_time
        self.restoration_countdown = 10
        self._log_event("MANUAL_QUARANTINE", {}, current_time)

    def manual_release(self):
        """Force release quarantine."""
        self.quarantine_active = False
        self.restoration_countdown = 0
        self._log_event("MANUAL_RELEASE", {}, time.time())

    def _execute_quarantine(self, analysis: dict, current_time: float):
        """Execute the quarantine: stop attack, begin countdown."""
        # This is where the IDS sends the API trigger to the SMF
        # to terminate the compromised device's PDU session
        self.generator.stop_attack()
        self.quarantine_active = True
        self.quarantine_start_time = current_time
        self.restoration_countdown = 10
        self._log_event("QUARANTINE", analysis, current_time)

    def _log_event(self, action: str, analysis: dict, timestamp: float):
        """Record a response event."""
        event = {
            "timestamp": timestamp,
            "action": action,
            "attack_type": analysis.get("dominant_attack"),
            "severity": analysis.get("max_severity"),
            "recommended": analysis.get("recommended_action"),
        }
        self.response_log.append(event)
        # Keep last 100 events
        if len(self.response_log) > 100:
            self.response_log = self.response_log[-100:]

    def _build_response(self, action_taken: str, progress: float) -> dict:
        """Build the response dict."""
        return {
            "action_taken": action_taken,
            "quarantine_active": self.quarantine_active,
            "restoration_progress_pct": round(progress, 1),
            "restoration_countdown": self.restoration_countdown,
            "log": self.response_log[-10:],  # Last 10 events
        }


if __name__ == "__main__":
    print("=" * 60)
    print("5G SliceGuard — Quarantine Engine Smoke Test")
    print("=" * 60)

    # Quick test with mock objects
    class MockGenerator:
        def stop_attack(self):
            print("  [MockGen] Attack stopped!")

    class MockDetector:
        pass

    gen = MockGenerator()
    det = MockDetector()
    qe = QuarantineEngine(gen, det)

    # Simulate quarantine trigger
    fake_analysis = {
        "recommended_action": "QUARANTINE",
        "dominant_attack": "resource_theft",
        "max_severity": "HIGH",
    }

    print("\n── Triggering quarantine ──")
    resp = qe.respond(fake_analysis)
    print(f"  Action: {resp['action_taken']} | Active: {resp['quarantine_active']}")

    print("\n── Restoration countdown ──")
    for i in range(12):
        resp = qe.respond({"recommended_action": "MONITOR"})
        print(f"  Tick: action={resp['action_taken']} | "
              f"progress={resp['restoration_progress_pct']}% | "
              f"active={resp['quarantine_active']}")

    print("\nSmoke test PASSED ✓")
