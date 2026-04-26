# PROMPT FOR CLAUDE OPUS — 5G SliceGuard Real Simulation

---

## YOUR MISSION

You are building **5G SliceGuard** — a real, working intrusion detection and automated
response system for virtualized 5G network slices. This is a university final-year
project presentation for a Computer Networks Security course.

The goal is to replace a fake JavaScript-only simulation with a **real Python ML
backend + Flask API + connected frontend dashboard**. Every number shown on screen must
come from a real Python process, not a random number generator.

Build EVERYTHING below from scratch, with full working code in every file.

---

## PROJECT CONTEXT

**5G Network Slicing** divides one physical 5G network into isolated virtual networks:
- **eMBB** (enhanced Mobile Broadband) — high throughput ~800 Mbps, latency ~4ms
- **URLLC** (Ultra-Reliable Low Latency) — critical latency <1ms, throughput ~200 Mbps
- **mMTC** (massive Machine Type Comms) — IoT, ~200 Mbps, latency ~10ms

**The threat**: Cross-slice attacks where a compromised slice steals resources from others.
Three attack types:
1. **Resource Theft** — mMTC floods CPU/bandwidth, URLLC latency spikes to 3–5ms (deadly for autonomous vehicles)
2. **Data Injection** — malicious packets injected across slice boundaries into URLLC data plane
3. **Side-Channel** — attacker infers data from shared cache timing patterns (subtle, hardest to detect)

**SliceGuard IDS pipeline**:
1. Monitor → 2. Detect (ML) → 3. Cross-Correlate → 4. Quarantine → 5. Restore

---

## COMPLETE FILE STRUCTURE TO BUILD

```
5G-SliceGuard/
├── simulation/
│   ├── traffic_generator.py     # Simulates realistic per-slice traffic (normal + attacks)
│   ├── feature_extractor.py     # Extracts ML features from raw traffic metrics
│   ├── train_model.py           # Trains XGBoost + Isolation Forest on labeled data
│   ├── detector.py              # Real-time anomaly detection engine
│   ├── quarantine.py            # Automated response logic
│   ├── sniffer.py               # Packet capture coordinator (uses Scapy if available)
│   ├── analyzer.py              # Aggregates metrics per slice per time window
│   ├── app.py                   # Flask API server exposing real-time data
│   ├── generate_dataset.py      # Generates labeled_traffic.csv from scratch
│   ├── labeled_traffic.csv      # Generated training dataset (auto-created)
│   └── model/
│       ├── xgb_model.pkl        # Trained XGBoost classifier
│       └── iso_forest.pkl       # Trained Isolation Forest (unsupervised fallback)
├── website/
│   ├── index.html               # Main dashboard (connects to Flask API)
│   ├── css/
│   │   └── style.css            # Full design system
│   └── js/
│       └── app.js               # Dashboard engine — reads from real API, NOT fake data
└── PRESENTATION_GUIDE.md        # Already exists — do not modify
```

---

## FILE 1: `simulation/generate_dataset.py`

**Purpose**: Generate a realistic labeled CSV dataset of 5G slice traffic.
Produces `labeled_traffic.csv` with 10,000 rows.

**Columns to generate**:
- `timestamp` — Unix time
- `slice_id` — 0=eMBB, 1=URLLC, 2=mMTC
- `bandwidth_mbps` — bandwidth consumed by slice
- `latency_ms` — end-to-end latency
- `packet_rate_pps` — packets per second
- `cpu_usage_pct` — % of shared CPU used by this slice
- `memory_usage_pct` — % of shared memory used
- `jitter_ms` — latency variation (std dev over last 10 packets)
- `drop_rate_pct` — packet drop rate
- `cross_slice_score` — rate of anomalous inter-slice traffic (0–1 float)
- `label` — 0=normal, 1=resource_theft, 2=data_injection, 3=side_channel

**Distribution rules**:

Normal traffic (70% of rows):
- eMBB: bandwidth=Gauss(800,30), latency=Gauss(4,0.3), cpu=Gauss(35,5), packet_rate=Gauss(5000,200)
- URLLC: bandwidth=Gauss(200,10), latency=Gauss(0.8,0.05), cpu=Gauss(20,3), packet_rate=Gauss(1000,50)
- mMTC: bandwidth=Gauss(200,15), latency=Gauss(10,1), cpu=Gauss(15,2), packet_rate=Gauss(500,30)

Resource Theft attack (10% of rows, mMTC slice attacker):
- mMTC: bandwidth=Gauss(1800,100), cpu=Gauss(85,5), packet_rate=Gauss(15000,500)
- URLLC (victim): latency spikes to Gauss(4.5,0.5), cpu=Gauss(60,8) (resource-starved)

Data Injection attack (10% of rows):
- cross_slice_score=Uniform(0.7,1.0) on URLLC
- URLLC: drop_rate=Gauss(12,2), jitter=Gauss(3,0.5)

Side-Channel attack (10% of rows):
- All metrics near-normal but: jitter=Gauss(0.15,0.02) microsecond patterns
- cpu_usage has subtle periodic pattern: cpu + sin(t * 0.5) * 3
- cross_slice_score=Uniform(0.1,0.3) — very subtle

All values clipped to realistic ranges (no negative bandwidth etc.)

Save to `simulation/labeled_traffic.csv`.
Print: "Dataset generated: 10000 rows, columns: [list], class distribution: [counts]"

---

## FILE 2: `simulation/feature_extractor.py`

**Purpose**: Given a dict of raw slice metrics, extract ML-ready feature vector.

**Class `FeatureExtractor`**:

```
__init__(self, window_size=10)
    - keeps rolling window of last N readings per slice
    - initializes per-slice history deques

extract(self, slice_metrics: dict) -> dict
    Input: {"slice_id": int, "bandwidth_mbps": float, "latency_ms": float, 
            "packet_rate_pps": float, "cpu_usage_pct": float,
            "memory_usage_pct": float, "jitter_ms": float,
            "drop_rate_pct": float, "cross_slice_score": float}
    
    Output: dict with:
    - All raw features
    - bandwidth_mean_10, bandwidth_std_10 (rolling stats)
    - latency_mean_10, latency_std_10
    - cpu_mean_10, cpu_std_10
    - bandwidth_delta (change from previous reading)
    - latency_delta
    - cpu_delta
    - latency_bandwidth_ratio (latency / bandwidth — useful anomaly indicator)
    - resource_pressure (cpu * memory / 10000)

get_feature_vector(self, extracted: dict) -> list
    Returns ordered list of all numeric features for model input
    (same order every time — important for model consistency)
```

---

## FILE 3: `simulation/train_model.py`

**Purpose**: Load `labeled_traffic.csv`, train TWO models, save both.

**Model 1 — XGBoost Classifier** (supervised, 4-class: normal + 3 attacks):
```python
from xgboost import XGBClassifier
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric='mlogloss',
    random_state=42
)
```
- Train/test split: 80/20
- Print classification report with precision/recall/f1 per class
- Print confusion matrix
- Save to `simulation/model/xgb_model.pkl`

**Model 2 — Isolation Forest** (unsupervised, for zero-day / unknown attacks):
```python
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.15, n_estimators=100, random_state=42)
```
- Train on NORMAL rows only (label=0)
- Save to `simulation/model/iso_forest.pkl`
- Save feature column order to `simulation/model/feature_columns.json`

Print: "Training complete. XGB accuracy: X.XX | ISO anomaly rate on test: X.XX"

---

## FILE 4: `simulation/traffic_generator.py`

**Purpose**: Continuously generates realistic traffic metrics for all 3 slices.
Runs in a background thread. Supports injecting attacks on-demand.

**Class `TrafficGenerator`**:

```
__init__(self)
    - current_state: dict per slice (eMBB, URLLC, mMTC)
    - attack_active: None or "resource_theft" / "data_injection" / "side_channel"
    - attack_target: which slice is being attacked
    - attack_intensity: float 0–1 (ramps up over 5 ticks, ramps down after quarantine)
    - tick_count: int
    - history: deque(maxlen=100) of snapshots

generate_tick(self) -> dict
    Returns current metrics for ALL 3 slices as:
    {
      "timestamp": float,
      "tick": int,
      "slices": {
        "eMBB":  {"bandwidth_mbps": ..., "latency_ms": ..., "cpu_usage_pct": ...,
                  "packet_rate_pps": ..., "memory_usage_pct": ...,
                  "jitter_ms": ..., "drop_rate_pct": ..., "cross_slice_score": ...},
        "URLLC": {...},
        "mMTC":  {...}
      },
      "attack_active": str or None,
      "attack_intensity": float
    }

start_attack(self, attack_type: str)
    Sets attack_active and begins ramping intensity

stop_attack(self)
    Immediately zeros attack_intensity (simulates quarantine response)

_generate_normal(self, slice_name: str) -> dict
    Uses Gaussian noise around slice baselines

_apply_attack_effects(self, slices: dict) -> dict
    Modifies victim and attacker slice metrics based on attack_type + intensity:
    
    resource_theft:
      - mMTC: bandwidth *= (1 + 1.5 * intensity), cpu *= (1 + 2 * intensity)
      - URLLC: latency *= (1 + 4 * intensity), cpu += 30 * intensity
      - eMBB: bandwidth *= (1 - 0.3 * intensity)
    
    data_injection:
      - URLLC: drop_rate += 15 * intensity, jitter += 3 * intensity
      - URLLC: cross_slice_score = min(1.0, 0.3 + 0.7 * intensity)
    
    side_channel:
      - All slices: jitter += sin(tick * 0.5) * 0.1 * intensity (subtle periodic)
      - mMTC: cpu has tiny periodic ripple
      - cross_slice_score = 0.1 + 0.2 * intensity (subtle)
```

Also expose a module-level singleton: `generator = TrafficGenerator()`

---

## FILE 5: `simulation/detector.py`

**Purpose**: Real-time detection engine. Takes a traffic snapshot, runs both ML models,
returns verdict + confidence.

**Class `SliceGuardDetector`**:

```
__init__(self)
    Load xgb_model.pkl, iso_forest.pkl, feature_columns.json
    Initialize FeatureExtractor()
    Initialize per-slice alert history (deque maxlen=20)
    alert_threshold: float = 0.65 (confidence needed to trigger alert)
    
analyze(self, snapshot: dict) -> dict
    Input: one tick from TrafficGenerator.generate_tick()
    
    For each slice:
      1. Extract features via FeatureExtractor
      2. XGBoost: predict_proba → get class + confidence
      3. IsoForest: decision_function → anomaly score (-1 to 1, lower = more anomalous)
      4. Combined score = 0.7 * xgb_confidence + 0.3 * iso_normalized
      5. If combined score > threshold AND xgb class != 0: fire alert
    
    Returns:
    {
      "timestamp": float,
      "tick": int,
      "slice_analysis": {
        "eMBB":  {
          "metrics": {...},
          "xgb_prediction": "normal"|"resource_theft"|"data_injection"|"side_channel",
          "xgb_confidence": float,
          "iso_score": float,       # normalized 0-1, higher = more anomalous
          "combined_score": float,
          "alert": bool,
          "severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
        },
        ... same for URLLC, mMTC
      },
      "global_alert": bool,
      "dominant_attack": str or None,
      "recommended_action": "MONITOR"|"WARN"|"QUARANTINE"|"EMERGENCY_ISOLATE"
    }

_get_severity(self, combined_score: float) -> str
    < 0.4  → "LOW"
    < 0.65 → "MEDIUM"  
    < 0.85 → "HIGH"
    >= 0.85 → "CRITICAL"

_cross_correlate(self, slice_analysis: dict) -> str or None
    If mMTC shows resource anomaly AND URLLC shows latency spike → "resource_theft"
    If URLLC shows high cross_slice_score → "data_injection"
    If all slices show subtle periodic jitter → "side_channel"
```

---

## FILE 6: `simulation/quarantine.py`

**Purpose**: Automated response engine. Decides and executes the defense action.

**Class `QuarantineEngine`**:

```
__init__(self, generator: TrafficGenerator, detector: SliceGuardDetector)
    - response_log: list of response events
    - quarantine_active: bool
    - quarantine_start_time: float
    - restoration_countdown: int (ticks until restoration)
    - auto_respond: bool = True (can be toggled)

respond(self, analysis: dict) -> dict
    Called after each detector.analyze()
    
    If recommended_action == "QUARANTINE" or "EMERGENCY_ISOLATE":
      - Call generator.stop_attack()
      - Set quarantine_active = True
      - Log the response event with timestamp, attack type, confidence
      - Start restoration_countdown = 10
    
    If quarantine_active and restoration_countdown > 0:
      - Decrement countdown
      - Return status "RESTORING"
    
    If restoration_countdown == 0:
      - Set quarantine_active = False
      - Log restoration complete
      - Return status "RESTORED"
    
    Returns:
    {
      "action_taken": "NONE"|"QUARANTINE"|"RESTORING"|"RESTORED",
      "quarantine_active": bool,
      "restoration_progress_pct": float,  # 0-100
      "log": list of last 10 events
    }

manual_quarantine(self)
    Force quarantine regardless of ML verdict

manual_release(self)
    Force release quarantine
```

---

## FILE 7: `simulation/analyzer.py`

**Purpose**: Aggregates per-slice statistics over time windows for the dashboard.

**Class `SliceAnalyzer`**:

```
__init__(self, window_sizes=[10, 50, 100])
    Per-slice history buffers

update(self, snapshot: dict)
    Add new tick data to buffers

get_summary(self) -> dict
    Returns for each slice:
    {
      "current": latest metrics,
      "avg_10": rolling 10-tick averages,
      "avg_50": rolling 50-tick averages,
      "trend": "STABLE"|"DEGRADING"|"RECOVERING" (based on last 10 vs last 50 latency)
      "sla_status": {
        "eMBB":  "OK" if bandwidth > 600, else "DEGRADED",
        "URLLC": "OK" if latency < 2.0, else "CRITICAL",
        "mMTC":  "OK" if packet_rate > 300, else "DEGRADED"
      }
    }

get_time_series(self, slice_name: str, metric: str, n=50) -> list
    Returns last N values of a specific metric for a specific slice
    (Used by frontend charts)
```

---

## FILE 8: `simulation/app.py`

**Purpose**: Flask REST API server. The brain connecting all components.
Runs on `localhost:5000`. Frontend polls this every 1 second.

**Setup**:
```python
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading, time

app = Flask(__name__)
CORS(app)  # Required for browser to call localhost API

# Initialize components
generator = TrafficGenerator()
extractor = FeatureExtractor()
detector = SliceGuardDetector()
analyzer = SliceAnalyzer()
quarantine_engine = QuarantineEngine(generator, detector)

# Shared state
latest_analysis = {}
latest_quarantine = {}
alert_log = []  # last 100 alerts
tick_lock = threading.Lock()
```

**Background simulation loop** (runs in daemon thread, ticks every 1 second):
```python
def simulation_loop():
    while True:
        snapshot = generator.generate_tick()
        analysis = detector.analyze(snapshot)
        analyzer.update(snapshot)
        q_response = quarantine_engine.respond(analysis)
        
        with tick_lock:
            latest_analysis = analysis
            latest_quarantine = q_response
            if analysis["global_alert"]:
                alert_log.append({
                    "timestamp": analysis["timestamp"],
                    "attack": analysis["dominant_attack"],
                    "action": q_response["action_taken"],
                    "severity": max severity from slice_analysis
                })
                if len(alert_log) > 100:
                    alert_log.pop(0)
        time.sleep(1)
```

**API Endpoints**:

```
GET /api/status
Returns: {
  "running": bool,
  "tick": int,
  "uptime_seconds": float,
  "attack_active": str or None,
  "quarantine_active": bool
}

GET /api/slices
Returns full slice metrics + analysis for all 3 slices (latest tick)
{
  "timestamp": float,
  "slices": {
    "eMBB":  { "metrics": {...}, "analysis": {...}, "trend": str, "sla_status": str },
    "URLLC": {...},
    "mMTC":  {...}
  },
  "global_alert": bool,
  "dominant_attack": str or None,
  "recommended_action": str,
  "quarantine": { "active": bool, "restoration_progress_pct": float }
}

GET /api/timeseries?slice=eMBB&metric=bandwidth_mbps&n=50
Returns: { "slice": str, "metric": str, "values": [float, ...], "timestamps": [...] }

GET /api/alerts?limit=20
Returns: { "alerts": [...last N alerts...], "total_count": int }

POST /api/attack
Body: { "type": "resource_theft" | "data_injection" | "side_channel" }
Returns: { "status": "attack_started", "type": str }

POST /api/attack/stop
Returns: { "status": "attack_stopped" }

POST /api/quarantine
Body: { "action": "force" | "release" }
Returns: { "status": str }

GET /api/model/info
Returns: { "xgb_classes": [...], "feature_count": int, "training_accuracy": float,
           "iso_contamination": float, "model_loaded": bool }
```

**Startup sequence**:
```python
if __name__ == "__main__":
    # 1. Check if dataset exists, if not generate it
    # 2. Check if model exists, if not train it
    # 3. Start simulation loop in background thread
    # 4. Start Flask on port 5000
    print("SliceGuard IDS running on http://localhost:5000")
    print("Dashboard: open website/index.html in your browser")
    app.run(port=5000, debug=False, threaded=True)
```

---

## FILE 9: `website/js/app.js` — COMPLETE REWRITE

**Purpose**: Replace ALL fake `Math.random()` data with real API calls.

**Architecture**:
```javascript
const API_BASE = "http://localhost:5000/api";
const POLL_INTERVAL = 1000; // 1 second

// State
let charts = {};           // Chart.js instances
let alertLog = [];
let isConnected = false;
let simulationRunning = false;
```

**Main polling loop**:
```javascript
async function pollData() {
    try {
        const [slicesRes, alertsRes] = await Promise.all([
            fetch(`${API_BASE}/slices`),
            fetch(`${API_BASE}/alerts?limit=20`)
        ]);
        const slices = await slicesRes.json();
        const alerts = await alertsRes.json();
        
        updateSliceCards(slices);
        updateCharts(slices);
        updateAlertLog(alerts.alerts);
        updateAttackIndicator(slices);
        updateQuarantinePanel(slices.quarantine);
        isConnected = true;
    } catch(e) {
        showConnectionError();
        isConnected = false;
    }
}
setInterval(pollData, POLL_INTERVAL);
```

**Chart data**: Use `GET /api/timeseries` for historical chart lines. Charts needed:
- eMBB bandwidth over time (line chart)
- URLLC latency over time (line chart — most dramatic during attacks!)
- mMTC packet rate over time
- Combined anomaly score over time (all 3 slices)
- CPU usage per slice (stacked area or grouped bar)

**Attack controls** (call real API):
```javascript
async function launchAttack(type) {
    await fetch(`${API_BASE}/attack`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({type})
    });
}

async function stopAttack() {
    await fetch(`${API_BASE}/attack/stop`, {method: "POST"});
}
```

**SLA Status indicator**: Show colored badge per slice:
- URLLC latency > 2ms → RED "CRITICAL — SLA BREACH"
- URLLC latency 1–2ms → ORANGE "WARNING"
- URLLC latency < 1ms → GREEN "NOMINAL"

**Alert log**: Each alert shows: timestamp, attack type icon, affected slice,
severity badge (color-coded), action taken, confidence %.

**Connection banner**: Show "⚡ LIVE — Connected to SliceGuard IDS Backend" when API
is reachable, "⚠ OFFLINE — Showing last known state" when not.

---

## FILE 10: `website/index.html` + `website/css/style.css` — FULL REDESIGN

**Aesthetic direction**: Dark cyberpunk / SOC (Security Operations Center) terminal.
Think real network operations center: dark background (#0a0e1a), electric blue (#00d4ff),
alert red (#ff3b3b), safe green (#00ff88), warning amber (#ffaa00).

**Layout** (single page, no frameworks needed, pure HTML/CSS/JS):

```
┌─────────────────────────────────────────────────────┐
│  HEADER: Logo + "LIVE" indicator + connection badge  │
├──────────────┬──────────────┬───────────────────────┤
│  SLICE CARDS (3 columns — eMBB / URLLC / mMTC)      │
│  Each card: slice name, key metric, SLA badge,       │
│             mini sparkline (SVG), status ring         │
├──────────────┴──────────────┴───────────────────────┤
│  MAIN CHART AREA: URLLC Latency (large, prominent)   │
│  + Anomaly Score timeline on the right               │
├─────────────────┬───────────────────────────────────┤
│  ATTACK PANEL   │  ALERT LOG                         │
│  3 attack btns  │  Scrolling live event feed          │
│  + Stop btn     │  with severity colors               │
│  + ML confidence│                                     │
├─────────────────┴───────────────────────────────────┤
│  QUARANTINE STATUS: progress bar + countdown         │
└─────────────────────────────────────────────────────┘
```

**Typography**: Use Google Fonts — `Share Tech Mono` for values/numbers (monospace,
tech feel), `Orbitron` for headers (futuristic), `Inter` for body text only.

**Animations**:
- Slice cards pulse with a subtle glow border when under attack
- Alert log items slide in from the right
- Quarantine activation triggers a full-screen flash (red overlay 200ms) then fade
- Anomaly score chart line glows bright red when > 0.65 threshold
- "CRITICAL" badge pulses

**IMPORTANT**: The HTML must include `<script>` tag pointing to Chart.js CDN
and must load `js/app.js`. No build tools, no bundlers, just static files.

---

## FILE 11: `simulation/sniffer.py`

**Purpose**: Optional real packet capture layer. If Scapy is available and script is
run with sudo, capture real localhost traffic. If not, gracefully fall back to
TrafficGenerator synthetic data.

```python
class PacketSniffer:
    def __init__(self):
        self.scapy_available = self._check_scapy()
        self.synthetic_mode = not self.scapy_available
    
    def _check_scapy(self) -> bool:
        try:
            from scapy.all import sniff
            return True
        except ImportError:
            print("[Sniffer] Scapy not available — using synthetic traffic mode")
            return False
    
    def start(self, callback):
        if self.synthetic_mode:
            # Just call callback with synthetic data from TrafficGenerator
            # every 1 second
            pass
        else:
            # Real packet capture on loopback interface
            from scapy.all import sniff, IP
            sniff(iface="lo", prn=callback, store=False)
```

---

## REQUIREMENTS FILE

Create `simulation/requirements.txt`:
```
flask==3.0.0
flask-cors==4.0.0
xgboost==2.0.3
scikit-learn==1.4.0
pandas==2.1.4
numpy==1.26.3
joblib==1.3.2
scapy==2.5.0
```

---

## README / HOW TO RUN

Create `simulation/README.md`:
```markdown
# 5G SliceGuard — Real Simulation Backend

## Quick Start (3 commands)

```bash
cd simulation
pip install -r requirements.txt
python app.py
```

Then open `website/index.html` in your browser.

## What happens on first run
1. `generate_dataset.py` creates 10,000 rows of labeled 5G traffic data
2. `train_model.py` trains XGBoost + Isolation Forest (~10 seconds)
3. Simulation loop starts ticking every 1 second
4. Flask API available at http://localhost:5000

## Running attacks (via API or dashboard)
- Dashboard: click attack buttons in the UI
- Terminal: `curl -X POST http://localhost:5000/api/attack -d '{"type":"resource_theft"}'`

## Model performance (expected)
- XGBoost accuracy: ~94–97% on test set
- Isolation Forest anomaly detection: ~89% recall on unseen attacks
```

---

## CRITICAL IMPLEMENTATION NOTES FOR CLAUDE

1. **No broken imports** — every file must import only from the files listed above
   and from pip packages in requirements.txt. No circular imports.

2. **Thread safety** — `app.py` uses threading. Use `threading.Lock()` around all
   shared state (`latest_analysis`, `alert_log`, etc.)

3. **Graceful degradation** — if model files don't exist yet, `detector.py` should
   raise a clear error message: "Run train_model.py first"

4. **The frontend must work offline too** — if Flask is not running, `app.js` must
   show a "Backend offline" banner and display the LAST received data (don't crash).

5. **Chart.js version**: Use Chart.js 4.x from CDN:
   `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`

6. **CORS**: Flask-CORS must be applied so browser can call `localhost:5000` from
   `file://` origin (opening index.html directly).

7. **Dataset generation is deterministic** — use `random.seed(42)` and
   `numpy.random.seed(42)` so dataset is reproducible.

8. **XGBoost label encoding**: Classes are integers 0,1,2,3. Map them to strings:
   `{0: "normal", 1: "resource_theft", 2: "data_injection", 3: "side_channel"}`

9. **All Python files must be runnable standalone** for testing:
   Each file should have `if __name__ == "__main__": ...` with a quick smoke test.

10. **Port conflict handling**: If port 5000 is busy, try 5001, 5002. Print the
    actual port so user knows where to look.

---

## DELIVERABLE CHECKLIST

When done, the following must all work:

- [ ] `python simulation/generate_dataset.py` creates CSV with correct columns
- [ ] `python simulation/train_model.py` trains and saves both model files
- [ ] `python simulation/app.py` starts with no errors, prints port
- [ ] `GET http://localhost:5000/api/slices` returns valid JSON
- [ ] `POST http://localhost:5000/api/attack` with body `{"type":"resource_theft"}` triggers attack
- [ ] Opening `website/index.html` shows live data updating every second
- [ ] URLLC latency chart spikes visibly during resource_theft attack
- [ ] Alert log populates with real ML-generated events during attacks
- [ ] Quarantine button stops the attack and shows restoration countdown
- [ ] All 3 attack types produce visually distinct chart behaviors

---

## FINAL NOTE

This is a **university final-year project presentation** for a Computer Networks
Security course at École Supérieure d'Informatique (Algeria). The student has prior
ML experience (XGBoost fraud detection with 1.8M transactions at GTC internship) and
strong Python skills. The code must be clean, well-commented, and impressive to
professors who understand both 5G networking and machine learning. Every number on
the screen must be real.
