import json
import time

STATE_FILE = "slice_state.json"

def trigger_quarantine():
    print("\n[SMF INTEGRATION] 👉 Triggering Session Management Function (SMF) API...")
    time.sleep(0.5)
    print("[SMF INTEGRATION] 👉 Instructing UPF to install DROP rules for anomalous mMTC PDU sessions...")
    
    # Update state to reflect quarantine
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    except:
        state = {}
        
    state["quarantined"] = True
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
        
    time.sleep(0.5)
    print("[SUCCESS] ✅ Attacker traffic successfully blocked. Slices isolated.")
    print("[SUCCESS] ✅ System metrics should now return to normal.\n")

def run_ids():
    print("🛡️ 5G SliceGuard IDS Engine Started.")
    print("Observing UPF telemetry stream for cross-slice anomalies...")
    print("-" * 65)
    
    try:
        while True:
            time.sleep(1)
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            except FileNotFoundError:
                continue

            cpu = state.get("shared_cpu_usage", 0)
            urllc_latency = state.get("slices", {}).get("URLLC", {}).get("latency", 0)
            mmtc_bw = state.get("slices", {}).get("mMTC", {}).get("bandwidth", 0)
            is_quarantined = state.get("quarantined", False)

            if not is_quarantined:
                # Correlate: high CPU + high mMTC bandwidth + high URLLC latency
                if cpu > 85.0 and mmtc_bw > 500 and urllc_latency > 3.0:
                    print("\n" + "!" * 65)
                    print("⚠️ CRITICAL THREAT DETECTED: Cross-Slice Resource Contention")
                    print(f"   ► Cause: mMTC bandwidth spike ({mmtc_bw:.1f} Mbps)")
                    print(f"   ► Impact: URLLC latency degradation ({urllc_latency:.1f} ms)")
                    print("!" * 65)
                    
                    time.sleep(1) # Simulating ML processing time
                    trigger_quarantine()

    except KeyboardInterrupt:
        print("\n🛑 IDS Engine Stopped.")

if __name__ == "__main__":
    run_ids()
