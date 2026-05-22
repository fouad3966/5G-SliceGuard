# 5G SliceGuard 🛡️ — Intrusion Detection & Automated Response for Virtualized Network Slices

[![Live Presentation](https://img.shields.io/badge/View-Live_Presentation-blue?style=for-the-badge)](https://fouad3966.github.io/5G-SliceGuard/)

> 💡 **Note for Reviewers/Checkers**: If you are reviewing this repository, you can explore the complete presentation and interactive dashboard by clicking the link above, or simply by opening `website/index.html` locally in your browser.

---

## 📌 Project Overview

**5G SliceGuard** is a fully functional, interactive prototype simulating real-time, Machine Learning-based Intrusion Detection in a 5G network architecture. Designed specifically for the **5G Network Security** domain, it demonstrates how Virtualized Network Functions (VNFs) can be defended against cross-slice attacks using AI.

By combining an interactive frontend with an AI-driven backend, this project visualizes how modern 5G networks manage traffic across different logical network slices—and how an Intrusion Detection System (IDS) spots, tracks, and isolates threats.

## 🚀 Presentation & Live Demo

This project features a fully designed web presentation detailing the history, mechanics, and mitigation strategies of 5G network attacks.

- **Site Presentation Link**: [**View Project Presentation Here**](https://fouad3966.github.io/5G-SliceGuard/)
- **Local Access**: No server required for the basic presentation. Just open the [`website/index.html`](website/index.html) file locally in any web browser.

## ⚙️ What Was Done (Key Features)

1. **5G Network Slicing Simulation**: Emulates the core 5G network slices sharing the same physical hardware:
   - _mMTC (Massive Machine-Type Comms)_ — Millions of low-power IoT devices.
   - _URLLC (Ultra-Reliable Low Latency)_ — Mission-critical, zero-delay setups.
   - _eMBB (Enhanced Mobile Broadband)_ — High-bandwidth streaming.
2. **Dual-Model ML IDS (Backend)**: Implements state-of-the-art anomaly detection using:
   - **XGBoost (Supervised)** for recognizing known DDoS patterns and volumetric floods with high-confidence.
   - **Isolation Forest (Unsupervised)** acting as a safety net for detecting zero-day (unknown) anomalous behavior like low-and-slow cross-slice timing attacks.
3. **Automated Response (The Scalpel)**: Rather than shutting down an entire infected slice (causing a self-inflicted DoS), the IDS identifies corrupted flows at the individual PDU session level and explicitly quarantines malicious IPs/UEs while letting legitimate traffic continue securely.
4. **Interactive Dashboard**: A dynamic web dashboard demonstrating live telemetry, current active network slices, hypervisor resource distribution, and real-time security alerts.

## 🧠 How It Works

The architecture mimics real-world enterprise 5G security appliances (inspired by the 3GPP NWDAF standard):

1. **Traffic Generator (`traffic_generator.py`)**: Simulates continuous flow parameters for the different 5G slices.
2. **Feature Extractor (`feature_extractor.py`)**: Gathers per-flow volumetric, temporal, and QoS degradation metrics (e.g., packet rate, latency, jitter).
3. **IDS Core (`detector.py` & `slice_guard_ids.py`)**: Consumes the extracted telemetry and predicts anomaly status over a rolling time window using the pre-trained ML models.
4. **Decision Engine (`quarantine.py`)**: Identifies specifically compromised flow IP identifiers and generates "block/quarantine" actions without terminating the entire network slice.

## 💻 Quick Start (Running the Simulation Backend)

If you wish to test the active backend and see the dashboard populate with live metrics:

1. **Navigate to the simulation folder:**
   ```bash
   cd "realistic simulation/simulation"
   ```
2. **Install the dependencies:**
   _(Ensure you have Python installed)_
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the backend server:**
   ```bash
   python app.py
   ```
   > _Note: On the first run, the system will automatically generate 10,000 rows of labeled 5G traffic data and train the XGBoost + Isolation Forest ML models (takes ~10 seconds)._
4. **View the Live Dashboard/API:**
   - The Flask API will be available at `http://localhost:5000`
   - Open the primary dashboard at [`website/index.html`](website/index.html) to interact.

## 📁 Repository Structure

- 📂 **[`website/`](website/)**: The main site presentation and interactive dashboard frontend (`HTML/CSS/JS`).
- 📂 **[`realistic simulation/simulation/`](realistic simulation/simulation/)**: The Python, Flask, and ML backend simulation engine.
- 📄 **[`5G_IDS_Conceptual_Architecture.md`](5G_IDS_Conceptual_Architecture.md)**: Theoretical paper discussing the cross-slice threat landscape and feature engineering logic.
- 📄 **[`PRESENTATION_GUIDE.md`](PRESENTATION_GUIDE.md)**: A complete guide and speaking points for explaining this tool.

---

**Author**: Mohamed Fouad Rabahi  
**Topic**: 5G Network Security
