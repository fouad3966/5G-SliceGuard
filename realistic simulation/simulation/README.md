# 5G SliceGuard — Real Simulation Backend

## Quick Start (3 commands)

```bash
cd "realistic simulation/simulation"
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

- **Dashboard**: Click attack buttons in the UI
- **Terminal**: `curl -X POST http://localhost:5000/api/attack -d '{"type":"resource_theft"}'`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/slices` | GET | Full slice metrics + ML analysis |
| `/api/timeseries` | GET | Historical data for charts |
| `/api/alerts` | GET | Recent detection alerts |
| `/api/attack` | POST | Launch attack |
| `/api/attack/stop` | POST | Stop attack |
| `/api/quarantine` | POST | Manual quarantine control |
| `/api/model/info` | GET | ML model metadata |

## Model Performance (expected)

- XGBoost accuracy: ~94–97% on test set
- Isolation Forest anomaly detection: ~89% recall on unseen attacks

## Architecture

```
TrafficGenerator → FeatureExtractor → Detector (XGBoost + IsoForest)
                                          ↓
                                    QuarantineEngine → TrafficGenerator.stop_attack()
                                          ↓
Flask API ← Analyzer ← All components
   ↓
Frontend Dashboard (polls every 1s)
```
