"""
5G SliceGuard — Flask API Server
==================================
The brain connecting all simulation components.
Exposes a REST API on localhost:5000 that the frontend dashboard
polls every second for live data.

Startup sequence:
  1. Check if dataset exists → generate if missing
  2. Check if models exist → train if missing
  3. Start simulation loop in background thread (1 tick/second)
  4. Start Flask on port 5000 (or next available)

All state mutations are protected by threading.Lock() for safety.
"""

import os
import sys
import time
import threading
import subprocess

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ── Path setup ─────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "website", "dashboard")
sys.path.insert(0, SCRIPT_DIR)

from traffic_generator import TrafficGenerator
from feature_extractor import FeatureExtractor
from detector import SliceGuardDetector
from analyzer import SliceAnalyzer
from quarantine import QuarantineEngine

# ── Flask app ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
CORS(app)  # Allow browser to call localhost API from file:// origin


@app.route("/")
def serve_index():
    """Serve the dashboard at root URL."""
    return send_from_directory(WEBSITE_DIR, "index.html")

# ── Shared state (protected by lock) ──────────────────────────────
latest_snapshot = {}
latest_analysis = {}
latest_quarantine = {}
alert_log = []  # Last 100 alerts
tick_lock = threading.Lock()
sim_running = False
start_time = time.time()

# ── Components (initialized after model check) ────────────────────
generator = None
detector = None
analyzer = None
quarantine_engine = None


def ensure_dataset():
    """Generate the training dataset if it doesn't exist."""
    csv_path = os.path.join(SCRIPT_DIR, "labeled_traffic.csv")
    if os.path.exists(csv_path):
        print(f"[Setup] Dataset found: {csv_path}")
        return True

    print("[Setup] Dataset not found — generating...")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "generate_dataset.py")],
        cwd=SCRIPT_DIR,
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] Dataset generation failed:\n{result.stderr}")
        return False
    return True


def ensure_models():
    """Train models if they don't exist."""
    model_dir = os.path.join(SCRIPT_DIR, "model")
    xgb_path = os.path.join(model_dir, "xgb_model.pkl")
    iso_path = os.path.join(model_dir, "iso_forest.pkl")

    if os.path.exists(xgb_path) and os.path.exists(iso_path):
        print(f"[Setup] Models found in {model_dir}/")
        return True

    print("[Setup] Models not found — training...")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "train_model.py")],
        cwd=SCRIPT_DIR,
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] Model training failed:\n{result.stderr}")
        return False
    return True


def init_components():
    """Initialize all simulation components."""
    global generator, detector, analyzer, quarantine_engine
    generator = TrafficGenerator()
    detector = SliceGuardDetector()
    analyzer = SliceAnalyzer()
    quarantine_engine = QuarantineEngine(generator, detector)
    print("[Setup] All components initialized")


# ══════════════════════════════════════════════════════════════════
# Background simulation loop
# ══════════════════════════════════════════════════════════════════

def simulation_loop():
    """
    Main simulation loop — runs in a daemon thread.
    Every second:
      1. Generate traffic tick
      2. Run ML detection
      3. Update analyzer
      4. Execute quarantine response
      5. Update shared state
    """
    global latest_snapshot, latest_analysis, latest_quarantine
    global alert_log, sim_running

    sim_running = True
    print("[Simulation] Loop started — ticking every 1 second")

    while sim_running:
        try:
            # 1. Generate traffic
            snapshot = generator.generate_tick()

            # 2. ML detection
            analysis = detector.analyze(snapshot)

            # 3. Update analyzer
            analyzer.update(snapshot)

            # 4. Quarantine response
            q_response = quarantine_engine.respond(analysis)

            # 5. Update shared state (thread-safe)
            with tick_lock:
                latest_snapshot = snapshot
                latest_analysis = analysis
                latest_quarantine = q_response

                # Log alerts
                if analysis["global_alert"]:
                    severities = [
                        sa["severity"]
                        for sa in analysis["slice_analysis"].values()
                    ]
                    severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
                    max_sev = max(severities, key=lambda s: severity_order.get(s, 0))

                    alert_log.append({
                        "timestamp": analysis["timestamp"],
                        "tick": analysis["tick"],
                        "attack": analysis["dominant_attack"],
                        "action": q_response["action_taken"],
                        "severity": max_sev,
                        "slices": {
                            name: {
                                "prediction": sa["xgb_prediction"],
                                "confidence": sa["combined_score"],
                            }
                            for name, sa in analysis["slice_analysis"].items()
                        },
                    })
                    if len(alert_log) > 100:
                        alert_log.pop(0)

        except Exception as e:
            print(f"[Simulation] Error in tick: {e}")

        time.sleep(1)


# ══════════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════════

@app.route("/api/status")
def api_status():
    """System status overview."""
    with tick_lock:
        tick = latest_analysis.get("tick", 0)
        attack = latest_snapshot.get("attack_active")
        q_active = latest_quarantine.get("quarantine_active", False)

    return jsonify({
        "running": sim_running,
        "tick": tick,
        "uptime_seconds": round(time.time() - start_time, 1),
        "attack_active": attack,
        "quarantine_active": q_active,
    })


@app.route("/api/slices")
def api_slices():
    """Full slice metrics + ML analysis for all 3 slices (latest tick)."""
    with tick_lock:
        if not latest_analysis:
            return jsonify({"error": "No data yet — simulation starting..."}), 503

        # Get analyzer summary
        summary = analyzer.get_summary()

        slices = {}
        for name in ["eMBB", "URLLC", "mMTC"]:
            sa = latest_analysis["slice_analysis"][name]
            sm = summary.get(name, {})
            slices[name] = {
                "metrics": sa["metrics"],
                "analysis": {
                    "xgb_prediction": sa["xgb_prediction"],
                    "xgb_confidence": sa["xgb_confidence"],
                    "xgb_probabilities": sa.get("xgb_probabilities", {}),
                    "iso_score": sa["iso_score"],
                    "combined_score": sa["combined_score"],
                    "alert": sa["alert"],
                    "severity": sa["severity"],
                },
                "trend": sm.get("trend", "STABLE"),
                "sla_status": sm.get("sla_status", "OK"),
                "avg_10": sm.get("avg_10", {}),
            }

        return jsonify({
            "timestamp": latest_analysis["timestamp"],
            "tick": latest_analysis["tick"],
            "slices": slices,
            "global_alert": latest_analysis["global_alert"],
            "dominant_attack": latest_analysis["dominant_attack"],
            "recommended_action": latest_analysis["recommended_action"],
            "quarantine": {
                "active": latest_quarantine.get("quarantine_active", False),
                "restoration_progress_pct": latest_quarantine.get("restoration_progress_pct", 0),
                "action_taken": latest_quarantine.get("action_taken", "NONE"),
                "countdown": latest_quarantine.get("restoration_countdown", 0),
            },
            "attack_active": latest_snapshot.get("attack_active"),
            "attack_intensity": latest_snapshot.get("attack_intensity", 0),
        })


@app.route("/api/timeseries")
def api_timeseries():
    """Historical time series for a specific slice/metric."""
    slice_name = request.args.get("slice", "URLLC")
    metric = request.args.get("metric", "latency_ms")
    n = int(request.args.get("n", 50))

    values = analyzer.get_time_series(slice_name, metric, n)
    timestamps = analyzer.get_timestamps(n)

    return jsonify({
        "slice": slice_name,
        "metric": metric,
        "values": [round(v, 4) for v in values],
        "timestamps": timestamps,
        "count": len(values),
    })


@app.route("/api/alerts")
def api_alerts():
    """Recent alert log."""
    limit = int(request.args.get("limit", 20))
    with tick_lock:
        recent = alert_log[-limit:]
    return jsonify({
        "alerts": recent,
        "total_count": len(alert_log),
    })


@app.route("/api/attack", methods=["POST"])
def api_attack():
    """Launch an attack."""
    data = request.get_json(force=True, silent=True) or {}
    attack_type = data.get("type", "resource_theft")

    valid_types = ["resource_theft", "data_injection", "side_channel"]
    if attack_type not in valid_types:
        return jsonify({"error": f"Invalid type. Valid: {valid_types}"}), 400

    generator.start_attack(attack_type)
    return jsonify({
        "status": "attack_started",
        "type": attack_type,
    })


@app.route("/api/attack/stop", methods=["POST"])
def api_attack_stop():
    """Stop the current attack."""
    generator.stop_attack()
    detector.reset_warmup(generator.tick_count)
    return jsonify({"status": "attack_stopped"})


@app.route("/api/quarantine", methods=["POST"])
def api_quarantine():
    """Manual quarantine control."""
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "force")

    if action == "force":
        quarantine_engine.manual_quarantine()
        return jsonify({"status": "quarantine_forced"})
    elif action == "release":
        quarantine_engine.manual_release()
        return jsonify({"status": "quarantine_released"})
    else:
        return jsonify({"error": "Invalid action. Use 'force' or 'release'"}), 400


@app.route("/api/model/info")
def api_model_info():
    """ML model metadata."""
    if detector:
        return jsonify(detector.get_model_info())
    return jsonify({"model_loaded": False})


# ══════════════════════════════════════════════════════════════════
# Startup
# ══════════════════════════════════════════════════════════════════

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result != 0:
                return port
        except Exception:
            return port
    return start_port


if __name__ == "__main__":
    print("=" * 60)
    print("5G SliceGuard — Intrusion Detection System")
    print("Real ML Backend + Flask API")
    print("=" * 60)

    # Step 1: Ensure dataset
    print("\n[Step 1/4] Checking dataset...")
    if not ensure_dataset():
        print("FATAL: Could not generate dataset. Exiting.")
        sys.exit(1)

    # Step 2: Ensure models
    print("\n[Step 2/4] Checking ML models...")
    if not ensure_models():
        print("FATAL: Could not train models. Exiting.")
        sys.exit(1)

    # Step 3: Initialize components
    print("\n[Step 3/4] Initializing components...")
    init_components()

    # Step 4: Start simulation + API
    print("\n[Step 4/4] Starting simulation loop...")
    sim_thread = threading.Thread(target=simulation_loop, daemon=True)
    sim_thread.start()

    # Find available port
    port = find_available_port(5000)

    print("\n" + "=" * 60)
    print(f"  SliceGuard IDS running on http://localhost:{port}")
    print(f"  Dashboard: open website/index.html in your browser")
    print(f"  API docs:  GET /api/status, /api/slices, /api/alerts")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
