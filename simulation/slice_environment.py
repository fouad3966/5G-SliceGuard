import time
import random
import json
import os

# State file to communicate between scripts
STATE_FILE = "slice_state.json"

class SliceEnvironment:
    """
    Simulates the shared 5G physical infrastructure hosting three virtual network slices.
    """
    def __init__(self):
        # Normal Operating Parameters
        self.slices = {
            "eMBB": {"bandwidth": 800, "latency": 4.0, "status": "NORMAL"},
            "URLLC": {"bandwidth": 100, "latency": 1.0, "status": "NORMAL"},
            "mMTC": {"bandwidth": 200, "latency": 10.0, "status": "NORMAL"}
        }
        self.shared_cpu_usage = 45.0 # percentage
        self.attacker_active = False
        self.quarantined = False

        self._save_state()

    def _save_state(self):
        state = {
            "slices": self.slices,
            "shared_cpu_usage": self.shared_cpu_usage,
            "attacker_active": self.attacker_active,
            "quarantined": self.quarantined
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)

    def _load_attack_state(self):
        """Check if an external script (attacker.py or ids.py) has modified the environment"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.attacker_active = state.get("attacker_active", False)
                    self.quarantined = state.get("quarantined", False)
            except:
                pass

    def run(self):
        print("🚀 5G Shared Infrastructure Simulator Started.")
        print("Monitoring UPF (User Plane Function) Telemetry across 3 slices...\n")
        print(f"{'Time':<10} | {'CPU %':<8} | {'eMBB (Mbps)':<12} | {'URLLC (ms)':<10} | {'mMTC (Mbps)':<12} | {'Status'}")
        print("-" * 75)

        try:
            while True:
                self._load_attack_state()

                # Simulate normal minor fluctuations
                noise = lambda: random.uniform(-0.5, 0.5)

                if self.attacker_active and not self.quarantined:
                    # Attack is active!
                    # mMTC consumes massive resources (Resource Theft)
                    self.shared_cpu_usage = min(98.5 + noise(), 100.0)
                    self.slices["mMTC"]["bandwidth"] = 950.0 + (noise() * 10)
                    
                    # This degrades other slices (Cross-slice impact)
                    self.slices["URLLC"]["latency"] = 15.0 + (noise() * 2) # Dangerous delay!
                    self.slices["eMBB"]["bandwidth"] = 300.0 + (noise() * 10)

                    status = "⚠️ ATTACK ACTIVE (Resource Contention)"
                
                else:
                    # Normal Operation (or Quarantined)
                    self.shared_cpu_usage = max(40.0, min(self.shared_cpu_usage - 10, 45.0 + noise()*2))
                    self.slices["mMTC"]["bandwidth"] = 200.0 + (noise() * 5)
                    self.slices["URLLC"]["latency"] = max(0.8, min(self.slices["URLLC"]["latency"] - 1, 1.0 + (noise()/5)))
                    self.slices["eMBB"]["bandwidth"] = 800.0 + (noise() * 10)

                    if self.quarantined and self.attacker_active:
                        self.slices["mMTC"]["bandwidth"] = 0.0 # Dropped
                        status = "🛡️ ATTACKER QUARANTINED (Restored)"
                    else:
                        status = "✅ NORMAL"

                self._save_state()

                # Output log
                t = time.strftime("%H:%M:%S")
                print(f"{t:<10} | {self.shared_cpu_usage:>5.1f}%   | {self.slices['eMBB']['bandwidth']:>6.1f} Mbps | {self.slices['URLLC']['latency']:>6.1f} ms  | {self.slices['mMTC']['bandwidth']:>6.1f} Mbps | {status}")
                
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Simulator Stopped.")

if __name__ == "__main__":
    env = SliceEnvironment()
    env.run()
