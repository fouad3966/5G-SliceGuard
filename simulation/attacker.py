import json
import time

STATE_FILE = "slice_state.json"

def launch_attack():
    print("😈 MALICIOUS AGENT INITIATED")
    print("Targeting: mMTC Slice (IoT Sensors)")
    print("Objective: Resource Contention (Bandwidth/CPU theft to degrade URLLC)")
    print("-" * 65)
    
    print("[*] Compromising 500 simulated IoT devices...")
    time.sleep(1)
    print("[*] Establishing botnet command & control access...")
    time.sleep(1)
    print("[*] Launching volumetric data flood across mMTC boundary...")
    
    # Update the environment state to trigger attack
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}

    state["attacker_active"] = True
    state["quarantined"] = False
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

    print("\n🚨 ATTACK SUCCESSFUL: Massive traffic spike initiated.")
    print("Check the Slice Environment terminal to see the impact on URLLC latency!")
    print("\n(Press Ctrl+C to stop the attack manually, or wait for SliceGuard to quarantine it)")

    try:
        while True:
            time.sleep(2)
            # Check if quarantined
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                if state.get("quarantined", False):
                    print("\n❌ CONNECTION DROPPED: We have been quarantined by SliceGuard!")
                    break
    except KeyboardInterrupt:
        # Reset on exit
        state["attacker_active"] = False
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        print("\nAttack stopped.")

if __name__ == "__main__":
    launch_attack()
