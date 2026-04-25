# 5G SliceGuard Terminal Simulation Guide

This folder contains a fully functional backend terminal simulation of the 5G SliceGuard Intrusion Detection System. It runs directly in your terminal using Python and visually demonstrates the lifecycle of a cross-slice attack and the automated defense response.

## Prerequisites
- Python 3.x installed

## How to Run the Presentation Demo

To demonstrate this effectively, you should open **three separate terminal/command prompt windows** side-by-side.

### Terminal 1: The 5G Network Environment
This script simulates the hardware of the 5G Core, displaying the real-time telemetry of the three network slices (eMBB, URLLC, mMTC) and shared CPU.
```bash
python slice_environment.py
```
*Wait a few seconds for it to establish a baseline. You will see metrics stabilizing.*

---

### Terminal 2: The SliceGuard IDS
This represents the ML-powered Intrusion Detection System observing the telemetry from the first terminal.
```bash
python slice_guard_ids.py
```
*It will output that it is observing the UPF telemetry stream for anomalies.*

---

### Terminal 3: The Attacker
This script acts as the malicious agent compromising IoT devices on the mMTC slice to cause a resource-contention attack.
```bash
python attacker.py
```

### 🍿 What Happens Next (The Demo Workflow)

1. Once you run `attacker.py` in Terminal 3, look back at **Terminal 1**. 
2. You will instantly see the CPU usage skyrocket to ~99% and mMTC bandwidth jump over 900 Mbps.
3. Because the slices share physical resources, the **URLLC latency** will spike dangerously (from ~1ms to >15ms). In real life, this latency spike would cause autonomous vehicle failures.
4. Almost immediately, **Terminal 2 (SliceGuard)** will detect this cross-slice correlation. It will print a red-alert threat detection.
5. SliceGuard will simulate an API call to the SMF (Session Management Function) to quarantine the attacker.
6. Check **Terminal 1** again. You will see the attacker quarantined and URLLC latency immediately drop back down to safe sub-1ms levels.

### Terminating
You can press `Ctrl+C` in all three terminals when you are finished to stop the scripts. 
(Any residual state is overwritten automatically on the next run).
