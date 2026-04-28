# Theoretical Architecture & Logic: 5G Network Slice IDS
*A comprehensive guide to the real-world deployment, detection, and automated quarantine logic of a Machine Learning Intrusion Detection System in a 5G architecture.*

---

## 1. The Threat Landscape: Network Slicing & Hypervisor Vulnerabilities
5G networks utilize **Network Function Virtualization (NFV)** to create isolated, logical networks called "Slices" over the same physical hardware. The standard slices are:
* **eMBB (Enhanced Mobile Broadband):** High bandwidth (e.g., streaming).
* **URLLC (Ultra-Reliable Low Latency):** Mission-critical, zero-delay (e.g., remote surgery, autonomous driving).
* **mMTC (Massive Machine-Type Comms):** Millions of low-power IoT devices.

**The Core Vulnerability:**
Because these slices share the same physical server (CPU/RAM/NIC) managed by a Hypervisor, **Cross-Slice Attacks** are possible. If an attacker compromises thousands of IoT devices in the mMTC slice and commands them to flood the network with junk packets, the hypervisor's CPU resources will be exhausted. Consequently, packets in the URLLC slice will be delayed or dropped, leading to catastrophic physical world consequences (e.g., a delayed braking signal for an autonomous car).

---

## 2. IDS Positioning: Flow-Level Visibility
To protect against these threats, the IDS must be positioned at the core of the 5G network, typically integrated with or constantly analyzing telemetry from the **UPF (User Plane Function)**.

Contrary to looking at a slice as one giant opaque pipe, the 5G Core performs Deep Packet Inspection and Flow Analysis. 
* Inside a massive slice, every individual device (UE) communicates via its own **PDU (Packet Data Unit) Session** (encapsulated in a GTP-U tunnel). 
* The IDS monitors traffic statistics on a **per-flow basis**, tracking the specific IP addresses and SUPI/SUCI device identifiers belonging to every individual PDU session.

---

## 3. Machine Learning Feature Engineering (How it "sees" an attack)
A standard firewall only inspects ports and IP destinations. An AI-powered IDS continuously analyzes statistical "vital signs" across the network. The detection logic relies on four major feature groupings:

### A. Volumetric Features (The Traffic Size)
Identifies brute-force floods and classic DDoS indicators.
* **Bandwidth:** Total Mbps consumed by the flow.
* **Packet Rate:** Packets Per Second (pps) injected into the core.

### B. Infrastructure Features (The Server Health)
Monitors the virtualization layer for resource starvation.
* **CPU Usage:** The percentage of virtual CPU time consumed by the slice's Virtual Network Functions (VNFs).
* **Memory Usage:** RAM consumption indicating potential buffer overflows.

### C. QoS Degradation Features (The User Experience)
Critical for ensuring SLAs (Service Level Agreements) are met, especially in URLLC.
* **Latency:** Packet delay in milliseconds.
* **Drop Rate:** Percentage of packets dropped due to full queues.
* **Jitter:** Unstable packet delay variance (the primary indicator of stealthy covert timing attacks or side-channels).

### D. Temporal & Cross-Slice Features (The "Secret Sauce")
The ML model calculates data continuously over a **rolling time window** (e.g., the last 10 seconds).
* **Standard Deviation & Deltas:** By measuring sudden mathematical changes (rate of change), it spots "Low and Slow" stealth attacks that don't trigger flat volume alarms.
* **Cross-Slice Correlation:** The most advanced logic. The IDS calculates the statistical correlation between an anomaly in Slice A (mMTC CPU spikes) and the degradation of Slice B (URLLC latency increases). This proves a physical virtualization layer attack is occurring rather than a normal traffic surge.

---

## 4. The Dual-Model ML Engine (Detection Logic)
To accurately classify threats and catch zero-day attacks without human intervention, the detection logic employs a hybrid Machine Learning approach:

1. **XGBoost (Supervised Learning):** 
   Trained on massive datasets of known cyberattacks vector profiles (Resource Theft, Data Plane Injections). It operates as an extremely fast classifier, recognizing complex non-linear signatures with high confidence.
2. **Isolation Forest (Unsupervised Learning):**
   Acts as the ultimate safety net for "Zero-Day" (unknown) attacks. It does not look for specific attacks; instead, it mathematically isolates any behavior that deviates from the established norm. If an attacker invents a brand new method to crash a 5G slice, the overall anomaly score will suddenly trigger an alert.

---

## 5. Automated Quarantine (Neutralizing the Threat)
In a URLLC environment, human reaction time is fundamentally too slow. If an attack is detected with High/Critical confidence (e.g., >65% combined ML certainty), the IDS instantly executes an automated response cycle.

### The Scalpel (Device Isolation)
In the event of an IoT botnet flood, the IDS does *not* shut down the entire mMTC slice, as this would result in a self-inflicted Denial of Service against legitimate users. Instead, it acts like a scalpel:
1. **Identify Corrupted Flows:** The IDS pinpoints the specific statistical outlier IPs/UEs that are acting like "zombies."
2. **SBA Integration:** The IDS sends an urgent REST API HTTP POST request over the 5G Service-Based Architecture management bus to the **SMF (Session Management Function)**.
3. **Terminate PDU Sessions:** It commands the SMF to forcefully terminate the PDU sessions of exclusively those malicious identifiers — not the physical devices themselves. 
4. **Result:** The UPF immediately blocks the malicious traffic. Dropping an entire session is instantaneous and highly secure. While any legitimate "clean" background packets mixed in that specific session are also dropped (a harsh but necessary measure), avoiding slow packet-by-packet filtering is the only way to save the critical URLLC slice from crashing. Meanwhile, the other 9,900 legitimate devices in the exact same slice experience zero interruption because they have their own independent PDU sessions.

### System Restoration
Because the malicious PDU sessions are dropped at the SMF level, the flood physically stops entering the core. The hypervisor CPU buffers drain, and the URLLC slice instantly restores to sub-1ms latency. The devices are now disconnected from the data plane. Afterward, the network operator can evaluate whether to permanently blacklist the device's SUPI, or place it in a remediation pool. Once verified clean, the device is allowed to establish a brand new, clean PDU session.

### The Filter & The Shield (Fallback Logic)
If the attack uses spoofed IPs (making individual identification impossible), the system relies on fallback logic:
* **The Filter (Dynamic Firewalling):** The IDS instructs the UPF to drop specific classes of traffic (e.g., "Drop all UDP packets targeting port 80").
* **The Shield (Strict Isolation):** As a last resort, the orchestrator physically locks the affected slice into a rigid resource cage. It instructs the hypervisor to hard-cap the mMTC slice to exactly its SLA limits so that, even if it chokes on its own malicious traffic, it is physically incapable of stealing CPUs required by the URLLC slice.
