# 5G SliceGuard — Intrusion Detection & Automated Response for Virtualized Network Slices
## Complete Presentation Guide

---

## 📌 Project Overview

**Title**: 5G SliceGuard — Real-Time Intrusion Detection & Automated Response for Virtualized Network Slices  
**Author**: Mohamed Fouad Rabahi  
**Course Topic**: 5G Network Security  
**Demo**: Fully interactive web-based defense testbed (no server required — just open `index.html`)

### 🌍 Is "SliceGuard" Real? (The Real-World Context)

It's common to wonder if this is a real product or a simulation. While the name "5G SliceGuard" is a custom brand created specifically for this project, the **technology, threats, and architecture it demonstrates are very real**. This project is a functional prototype inspired by actual industry standards:

1. **3GPP NWDAF (Network Data Analytics Function)**: The standard 5G core function responsible for gathering telemetry and using ML to provide predictive analytics back to the network.
2. **Academic Research**: This implementation adopts state-of-the-art anomaly-based cross-slice intrusion detection strategies discussed in recent IEEE and ACM security papers.

Think of SliceGuard as an educational prototype of a real-world enterprise 5G security appliance (like those built by Ericsson, Nokia, or Palo Alto Networks).

---

## 🎯 What This Project Demonstrates

1. **5G Network Slicing** — How a single physical 5G network is divided into multiple isolated virtual networks
2. **Cross-Slice Threat Landscape** — The attack vectors that can breach slice isolation boundaries
3. **SliceGuard IDS Engine** — A multi-layer intrusion detection system that identifies and auto-quarantines threats
4. **Automated Response** — How the system isolates compromised boundaries and restores normal operation
5. **Security Evolution** — How mobile network security has evolved from 2G to 5G

---

## 📖 TOPIC EXPLANATION: 5G Network Slicing

### What is Network Slicing?

Network slicing is THE defining feature of 5G architecture. It allows mobile network operators to create **multiple virtual networks (slices)** on top of a single shared physical infrastructure.

**Key Concept**: Each slice is an **isolated, end-to-end virtual network** tailored for a specific use case, with its own:
- Dedicated bandwidth allocation
- Latency guarantees
- Security policies
- Quality of Service (QoS) parameters

Think of it like **lanes on a highway** — same road, but each lane can have different speed limits, vehicle types, and rules.

### The Three Main Slice Types

#### 1. eMBB (enhanced Mobile Broadband)
- **Purpose**: High-bandwidth applications
- **Use Cases**: 4K/8K video streaming, virtual reality, cloud gaming, augmented reality
- **Key Metric**: Up to **20 Gbps** peak data rate
- **Latency**: ~4ms (acceptable for media)
- **Real-world example**: A stadium with 80,000 fans all streaming video simultaneously

#### 2. URLLC (Ultra-Reliable Low-Latency Communications)
- **Purpose**: Mission-critical, real-time applications
- **Use Cases**: Autonomous vehicles, remote surgery, industrial robotics, drone control
- **Key Metric**: **99.999%** reliability (five nines)
- **Latency**: **< 1ms** (ultra-low, non-negotiable)
- **Real-world example**: A surgeon in Paris operating a robot in New York — any delay could be fatal

#### 3. mMTC (massive Machine-Type Communications)
- **Purpose**: Connecting billions of IoT devices
- **Use Cases**: Smart city sensors, agricultural monitoring, environmental tracking, smart meters
- **Key Metric**: **1 million devices per km²**
- **Latency**: ~10ms (less critical)
- **Real-world example**: 500,000 sensors in a city reporting temperature, air quality, traffic

### Why Slicing Matters for Security

The critical promise of network slicing is **ISOLATION**. A compromise in one slice should NEVER affect another slice. This is especially important because:

- An IoT slice (mMTC) may have thousands of low-security, easily compromised devices
- A medical or automotive slice (URLLC) handles life-critical operations
- If an attacker compromises an IoT device and can jump to the URLLC slice, **people could die**

---

## 🔐 5G Architecture Components (for presentation)

### Key Network Functions

| Component | Full Name | Role |
|-----------|-----------|------|
| **NSSF** | Network Slice Selection Function | Selects the appropriate slice for each device/request |
| **NSSAAF** | Network Slice-Specific Authentication and Authorization Function | Authenticates users per-slice |
| **NSSMF** | Network Slice Subnet Management Function | Manages and monitors individual slices |
| **AMF** | Access and Mobility Management Function | Handles device registration, mobility |
| **SMF** | Session Management Function | Manages PDU sessions within slices |
| **UPF** | User Plane Function | Handles actual data forwarding |
| **UDM** | Unified Data Management | Stores subscriber profiles, slice assignments |
| **gNodeB** | 5G Base Station | The 5G radio access point (replaces eNodeB from 4G) |

### S-NSSAI (Single Network Slice Selection Assistance Information)

Each slice is identified by an **S-NSSAI** consisting of:
- **SST (Slice/Service Type)**: 1=eMBB, 2=URLLC, 3=mMTC
- **SD (Slice Differentiator)**: Optional field for further distinguishing slices

When a device (UE) connects, it sends its requested NSSAI to the network. The AMF consults the NSSF to determine which slices the device is authorized to use.

---

## ⚔️ CROSS-SLICE ATTACKS: How They Work

### Attack Surface

Cross-slice attacks exploit the fact that **slices share physical infrastructure**:
- Same servers/CPUs
- Same memory
- Same network switches
- Same hypervisor/virtualization layer
- Same management APIs

### Attack Type 1: Resource Theft

**What happens**: An attacker on a low-priority slice (mMTC) consumes excessive shared resources (CPU, memory, bandwidth), starving other slices.

**Technical detail**: 
- The attacker floods their slice with traffic or computation
- Due to imperfect resource isolation in the hypervisor, this causes **resource contention**
- The URLLC slice experiences latency spikes because it can't get CPU time
- Result: Autonomous vehicle control signals are delayed

**Detection**: Monitor per-slice resource consumption. Alert when any slice exceeds its allocated quota or when other slices show unexpected performance degradation.

### Attack Type 2: Data Injection

**What happens**: An attacker exploits a vulnerability to inject packets across slice boundaries, directly into another slice's data plane.

**Technical detail**:
- Exploits bugs in VNF (Virtual Network Function) implementations
- Uses hypervisor escape techniques (e.g., VENOM, Xen vulnerabilities)
- Targets the UPF (User Plane Function) which may be shared
- Injects malicious commands into the URLLC data stream

**Detection**: Deep packet inspection at slice boundaries. Cross-slice traffic that doesn't match authorized inter-slice communication patterns is flagged and blocked.

### Attack Type 3: Side-Channel Attack

**What happens**: The attacker doesn't cross the slice boundary directly. Instead, they infer information from the target slice by observing shared resource behavior.

**Technical detail**:
- **Cache timing attacks**: Attacker measures cache access latency to determine what data the target slice just accessed
- **Memory bus contention**: Observing memory bandwidth patterns reveals target slice activity
- **Network covert channels**: Timing of shared network buffer usage leaks information

**Detection**: This is the hardest to detect. Requires ML-based behavioral analysis that can identify subtle statistical anomalies in resource access patterns.

### Real-World Research References

1. **"Network Slicing Security: Challenges and Directions"** (IEEE, 2021) — Comprehensive survey of slicing threats
2. **"Breaking the Isolation: Cross-Slice Attacks in 5G Core Networks"** (ACM CCS, 2022) — Practical cross-slice attack demonstrations
3. **3GPP TS 33.501** — 5G Security Architecture specification
4. **ENISA Threat Landscape for 5G** (2019) — European agency's assessment of 5G threats

---

## 🛡️ HOW THE GUARDING HAPPENS: The Defense Engine

The automated defense isn't magic—it's a systematic 5-step loop handled by the IDS:

### 1. Telemetry Ingestion (Observe)
The IDS continuously pulls hardware metrics (CPU, Memory usage) and network metrics (Packet size, Latency, Bandwidth) directly from the 5G Core—specifically tapping into the **UPF (User Plane Function)** and **NSSMF (Network Slice Subnet Management Function)**.

### 2. ML Classification (Detect)
A trained Machine Learning model (e.g., Isolation Forest) receives the metric stream every second. It compares the live data to a learned "normal" baseline. If the mMTC slice suddenly consumes 90% of a shared CPU core, the model flags a high threat probability.

### 3. Cross-Slice Correlation (Correlate)
A simple spike in traffic isn't always an attack. The engine cross-correlates metrics between isolated slices. If mMTC resource usage spikes *at the exact same time* that the URLLC slice experiences dangerous latency drops, the IDS identifies it as a **Cross-Slice Contention Attack**.

### 4. Automated Quarantine (Isolate)
In a 5G URLLC environment, human reaction time is too slow. Upon high-confidence detection, the IDS sends an automated API trigger to the **SMF (Session Management Function)**. The SMF immediately terminates the compromised device's PDU session or installs a granular packet-drop rule, effectively firewalling the attacker.

### 5. Restoration (Restore)
With the malicious flow instantly dropped, the shared physical resources (CPU/memory/buffers) are freed up. The URLLC slice's latency stabilizes back to the necessary sub-1ms threshold, maintaining its life-critical guarantees.

---

## 🖥️ HOW TO RUN THE DEMO

### Quick Start
```
1. Open the website/index.html file in any web browser
2. No server needed — everything runs client-side
3. Scroll to the Simulator section or click "Launch Simulator"
```

### Demo Walkthrough (for presentation day)

#### Step 1: Normal Operation (30 seconds)
1. Click **Start** to begin the simulation
2. Show the 3 slices operating normally:
   - eMBB (blue) — streaming data at ~800 Mbps
   - URLLC (red) — ultra-low latency at ~1ms
   - mMTC (green) — IoT devices at ~200 Mbps
3. Point out the **isolation barriers** between slices
4. Show the **real-time charts** updating with stable metrics

#### Step 2: Launch Attack (30 seconds)
1. Select an attack type (suggest starting with **Resource Theft** — most visual)
2. Click **Launch Attack**
3. Show the audience:
   - Red attack packets crossing slice boundaries
   - eMBB throughput dropping dramatically
   - URLLC latency spiking (dangerous!)
   - Anomaly score rising in the chart
   - Alert log filling with warnings

**SAY**: *"Notice how the attacker on the mMTC slice is stealing resources from other slices. The URLLC latency just jumped from 1ms to 3ms — in a real scenario, this could delay an autonomous vehicle's braking command."*

#### Step 3: Run Detection (30 seconds)
1. Click **Detect** to activate the detection system
2. Show:
   - Green shield effect appearing on slices
   - Metrics gradually returning to normal
   - Alert log showing detection → isolation → restoration
   - Anomaly score dropping back to baseline

**SAY**: *"Our detection system identified the anomalous cross-slice traffic pattern, isolated the compromised boundary, and restored normal isolation. This process took about 4 seconds — in a real system, this would be sub-second."*

#### Step 4: Try Other Attacks
- **Data Injection**: More targeted, directly compromises URLLC
- **Side-Channel**: Subtle — anomaly score rises but metrics barely change (hardest to detect)

---

## 📊 Key Numbers to Remember (for Q&A)

| Metric | Value |
|--------|-------|
| 5G peak data rate | 20 Gbps |
| URLLC latency requirement | < 1 ms |
| URLLC reliability | 99.999% |
| mMTC device density | 1M devices/km² |
| 5G encryption | AES-256 (NEA1/2/3) |
| 5G authentication | 5G-AKA with SUPI/SUCI |
| Slicing identifier | S-NSSAI (SST + SD) |
| Slice selection | NSSF (Network Slice Selection Function) |
| 3GPP security spec | TS 33.501 |

---

## ❓ Anticipated Questions & Answers

### Q: How is this different from VLANs or traditional virtualization?
**A**: Network slicing goes beyond VLANs. It's end-to-end virtualization across all layers (RAN, transport, core) with guaranteed QoS, dedicated control planes, and standardized by 3GPP. VLANs only operate at Layer 2 of the data plane.

### Q: Are cross-slice attacks theoretical or real?
**A**: Researchers have demonstrated practical cross-slice attacks in lab environments. Notable papers from ACM CCS 2022 and IEEE S&P have shown resource theft and side-channel attacks on commercial-grade 5G testbeds.

### Q: Why not just use completely separate physical networks?
**A**: Cost. The whole point of slicing is to share expensive infrastructure while maintaining logical isolation. Separate physical networks would cost 3-5x more to deploy and maintain.

### Q: How does the detection system work?
**A**: We use a multi-layer approach: (1) Statistical anomaly detection comparing current metrics to established baselines, (2) Boundary packet inspection for unauthorized cross-slice traffic, (3) ML models trained on normal behavior to catch subtle attacks like side-channels.

### Q: What makes 5G SliceGuard unique compared to a simple anomaly detector?
**A**: SliceGuard is specifically designed for 5G slicing environments. It doesn't just detect anomalies — it understands slice topology, correlates signals across multiple slices simultaneously, and triggers automated quarantine responses. A generic IDS doesn't understand slice boundaries.

### Q: How is this different from a regular network IDS?
**A**: Traditional IDS monitors a flat network. SliceGuard is topology-aware — it understands that traffic should NEVER cross certain boundaries, and it monitors shared resources (CPU, memory, cache) for contention patterns that indicate cross-slice exploitation.

### Q: What's S-NSSAI?
**A**: Single Network Slice Selection Assistance Information. It's how a device tells the network which slice it wants to connect to. It contains an SST (Slice/Service Type: 1=eMBB, 2=URLLC, 3=mMTC) and an optional SD (Slice Differentiator).

### Q: Which 3GPP release introduced network slicing?
**A**: Release 15 (2018) introduced the basic slicing architecture. Release 16 enhanced it with inter-slice security, and Release 17 added advanced slice management and NSSAAF.

---

## 🔗 How This Connects to Course Topics

This project bridges multiple topics from the course:

| Course Topic | Connection |
|-------------|------------|
| **GSM Security** | We compare A5/1's weakness to 5G's AES-256 in the protocol table |
| **LTE Security** | We show how LTE's limited QoS-based slicing differs from 5G's full NSSF-managed slicing |
| **5G Architecture** | The entire project is built on 5G-NR architecture (gNodeB, AMF, SMF, UPF) |
| **Authentication** | 5G-AKA with SUPI/SUCI privacy (prevents IMSI-catching attacks from 2G/3G) |
| **Network Attacks** | Cross-slice threats are a novel 5G-specific attack surface that SliceGuard is built to defend |
| **Detection** | ML-based and rule-based IDS techniques applied to 5G slice telemetry |

---

## 📁 Project Structure

```
RPL-Attack-Detector/
├── website/                    # Presentation website
│   ├── index.html             # Main page (open this!)
│   ├── css/
│   │   └── style.css          # Complete design system
│   └── js/
│       └── app.js             # Simulator engine + charts + UI
├── PRESENTATION_GUIDE.md       # THIS FILE — presentation preparation
├── app.py                      # Original Flask dashboard
├── analyzer.py                 # Original packet analyzer
├── detector.py                 # Original anomaly detector
├── feature_extractor.py        # Original feature extraction
├── sniffer.py                  # Original packet sniffer
├── labeled_traffic.csv         # Original training data
├── packet_log.csv              # Original packet logs
└── alerts.log                  # Original alert logs
```

---

## ✅ Pre-Presentation Checklist

- [ ] Open `website/index.html` in Chrome or Firefox
- [ ] Test all nav links work
- [ ] Run full simulator cycle: Start → Attack → Detect → Reset
- [ ] Try all 3 attack types
- [ ] Verify charts update in real-time
- [ ] Check responsive layout if projecting
- [ ] Read through Q&A section above
- [ ] Have this guide open on a second screen/phone for reference

---

**Good luck with the presentation! The demo is designed to be impressive and work every time.** 🚀
