/**
 * 5G SliceGuard — Dashboard Engine
 * ==================================
 * Connects to the real Flask ML backend via REST API.
 * Every number on this dashboard comes from actual Python ML models.
 * NO fake Math.random() data — everything is real.
 * 
 * Architecture:
 *   - Polls /api/slices every 1 second for live metrics + ML analysis
 *   - Polls /api/alerts for detection events
 *   - Fetches /api/timeseries for chart history
 *   - POSTs to /api/attack and /api/quarantine for controls
 */

// ══════════════════════════════════════════════════════════════
// Configuration
// ══════════════════════════════════════════════════════════════

const API_BASE = "http://localhost:5000/api";
const POLL_INTERVAL = 1000; // 1 second
const CHART_HISTORY = 50; // data points shown on charts

// ══════════════════════════════════════════════════════════════
// State
// ══════════════════════════════════════════════════════════════

let charts = {};
let isConnected = false;
let lastData = null;
let activeAttack = null;
let pollTimer = null;
let previousQuarantineActive = false;

// ══════════════════════════════════════════════════════════════
// Initialization
// ══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    checkModelInfo();
    startPolling();
});

function startPolling() {
    pollData(); // Immediate first poll
    pollTimer = setInterval(pollData, POLL_INTERVAL);
}

// ══════════════════════════════════════════════════════════════
// Main Polling Loop
// ══════════════════════════════════════════════════════════════

async function pollData() {
    try {
        const [slicesRes, alertsRes] = await Promise.all([
            fetch(`${API_BASE}/slices`),
            fetch(`${API_BASE}/alerts?limit=20`)
        ]);

        if (!slicesRes.ok) throw new Error(`API returned ${slicesRes.status}`);

        const slices = await slicesRes.json();
        const alerts = await alertsRes.json();

        lastData = slices;

        // Update all dashboard sections
        updateConnectionBadge(true);
        updateTickCounter(slices);
        updateSliceCards(slices);
        updateAttackIndicator(slices);
        updateQuarantinePanel(slices.quarantine);
        updateAlertLog(alerts.alerts);

        // Fetch time series for charts
        await updateChartsFromAPI();

        isConnected = true;
    } catch (e) {
        console.error("[SliceGuard] API error:", e.message);
        updateConnectionBadge(false);
        isConnected = false;
    }
}

// ══════════════════════════════════════════════════════════════
// Connection Badge
// ══════════════════════════════════════════════════════════════

function updateConnectionBadge(online) {
    const badge = document.getElementById("connection-badge");
    const text = badge.querySelector(".connection-text");

    if (online) {
        badge.className = "connection-badge online";
        text.textContent = "⚡ LIVE — Connected to SliceGuard IDS Backend";
    } else {
        badge.className = "connection-badge offline";
        text.textContent = "⚠ OFFLINE — Start python simulation/app.py";
    }
}

function updateTickCounter(data) {
    document.getElementById("tick-count").textContent = data.tick || 0;

    // Calculate uptime from first connection
    const uptimeEl = document.getElementById("uptime");
    const tick = data.tick || 0;
    const mins = Math.floor(tick / 60);
    const secs = tick % 60;
    uptimeEl.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

async function checkModelInfo() {
    try {
        const res = await fetch(`${API_BASE}/model/info`);
        const info = await res.json();
        const el = document.getElementById("model-status");
        if (info.model_loaded) {
            el.textContent = `✓ ${(info.training_accuracy * 100).toFixed(1)}%`;
            el.className = "stat-value stat-ok";
        } else {
            el.textContent = "NOT LOADED";
            el.className = "stat-value";
            el.style.color = "var(--alert-red)";
        }
    } catch (e) {
        document.getElementById("model-status").textContent = "—";
    }
}

// ══════════════════════════════════════════════════════════════
// Slice Cards Update
// ══════════════════════════════════════════════════════════════

function updateSliceCards(data) {
    if (!data.slices) return;

    // ── eMBB ──
    const embb = data.slices.eMBB;
    if (embb) {
        setText("embb-bandwidth", embb.metrics.bandwidth_mbps.toFixed(0));
        setText("embb-latency", embb.metrics.latency_ms.toFixed(2));
        setText("embb-cpu", embb.metrics.cpu_usage_pct.toFixed(1));
        setText("embb-packets", embb.metrics.packet_rate_pps.toFixed(0));
        updateCardAnalysis("embb", embb.analysis);
        updateSLABadge("sla-eMBB", embb.sla_status);
        updateCardAttackState("card-eMBB", embb.analysis);
    }

    // ── URLLC ──
    const urllc = data.slices.URLLC;
    if (urllc) {
        setText("urllc-latency-big", urllc.metrics.latency_ms.toFixed(3));
        setText("urllc-bandwidth", urllc.metrics.bandwidth_mbps.toFixed(0));
        setText("urllc-cpu", urllc.metrics.cpu_usage_pct.toFixed(1));
        setText("urllc-drop", urllc.metrics.drop_rate_pct.toFixed(2));
        updateCardAnalysis("urllc", urllc.analysis);
        updateSLABadge("sla-URLLC", urllc.sla_status);
        updateCardAttackState("card-URLLC", urllc.analysis);

        // Color URLLC latency value based on SLA
        const latEl = document.getElementById("urllc-latency-big");
        if (urllc.metrics.latency_ms > 2.0) {
            latEl.style.color = "var(--alert-red)";
            latEl.style.textShadow = "0 0 10px var(--alert-red)";
        } else if (urllc.metrics.latency_ms > 1.0) {
            latEl.style.color = "var(--warning-amber)";
            latEl.style.textShadow = "0 0 10px var(--warning-amber)";
        } else {
            latEl.style.color = "var(--safe-green)";
            latEl.style.textShadow = "0 0 10px var(--safe-green)";
        }
    }

    // ── mMTC ──
    const mmtc = data.slices.mMTC;
    if (mmtc) {
        setText("mmtc-packets-big", mmtc.metrics.packet_rate_pps.toFixed(0));
        setText("mmtc-bandwidth", mmtc.metrics.bandwidth_mbps.toFixed(0));
        setText("mmtc-cpu", mmtc.metrics.cpu_usage_pct.toFixed(1));
        setText("mmtc-latency", mmtc.metrics.latency_ms.toFixed(1));
        updateCardAnalysis("mmtc", mmtc.analysis);
        updateSLABadge("sla-mMTC", mmtc.sla_status);
        updateCardAttackState("card-mMTC", mmtc.analysis);
    }
}

function updateCardAnalysis(prefix, analysis) {
    if (!analysis) return;

    const verdict = document.getElementById(`${prefix}-verdict`);
    const bar = document.getElementById(`${prefix}-bar`);
    const score = document.getElementById(`${prefix}-score`);

    const pred = analysis.xgb_prediction || "normal";
    const conf = (analysis.combined_score || 0) * 100;

    // Verdict label
    verdict.textContent = pred.replace(/_/g, " ").toUpperCase();
    if (pred === "normal") {
        verdict.className = "analysis-verdict normal";
    } else {
        verdict.className = "analysis-verdict attack";
    }

    // Confidence bar
    bar.style.width = conf + "%";
    if (conf > 70) {
        bar.className = "analysis-bar danger";
    } else if (conf > 40) {
        bar.className = "analysis-bar elevated";
    } else {
        bar.className = "analysis-bar";
    }

    // Score text
    score.textContent = conf.toFixed(1) + "%";
}

function updateSLABadge(elementId, status) {
    const el = document.getElementById(elementId);
    if (!el) return;

    el.textContent = status || "OK";
    if (status === "CRITICAL") {
        el.className = "sla-badge critical";
    } else if (status === "DEGRADED") {
        el.className = "sla-badge degraded";
    } else {
        el.className = "sla-badge ok";
    }
}

function updateCardAttackState(cardId, analysis) {
    const card = document.getElementById(cardId);
    if (!card) return;

    if (analysis && analysis.alert) {
        card.classList.add("under-attack");
    } else {
        card.classList.remove("under-attack");
    }
}

// ══════════════════════════════════════════════════════════════
// Attack Controls
// ══════════════════════════════════════════════════════════════

async function launchAttack(type) {
    try {
        const res = await fetch(`${API_BASE}/attack`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type })
        });
        const data = await res.json();
        activeAttack = type;

        // Highlight active button
        document.querySelectorAll(".attack-btn").forEach(b => b.classList.remove("active"));
        const btnId = `btn-${type.replace(/_/g, "-")}`;
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.add("active");

        console.log(`[SliceGuard] Attack launched: ${type}`);
    } catch (e) {
        console.error("[SliceGuard] Failed to launch attack:", e);
    }
}

async function stopAttack() {
    try {
        await fetch(`${API_BASE}/attack/stop`, { method: "POST" });
        activeAttack = null;
        document.querySelectorAll(".attack-btn").forEach(b => b.classList.remove("active"));
    } catch (e) {
        console.error("[SliceGuard] Failed to stop attack:", e);
    }
}

async function manualQuarantine() {
    try {
        await fetch(`${API_BASE}/quarantine`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "force" })
        });
    } catch (e) {
        console.error("[SliceGuard] Quarantine failed:", e);
    }
}

async function manualRelease() {
    try {
        await fetch(`${API_BASE}/quarantine`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "release" })
        });
    } catch (e) {
        console.error("[SliceGuard] Release failed:", e);
    }
}

function updateAttackIndicator(data) {
    const statusText = document.getElementById("attack-status-text");
    const intensityWrap = document.getElementById("intensity-wrap");
    const intensityBar = document.getElementById("intensity-bar");
    const intensityValue = document.getElementById("intensity-value");

    if (data.attack_active) {
        const name = data.attack_active.replace(/_/g, " ").toUpperCase();
        statusText.textContent = `🔴 ${name} IN PROGRESS`;
        statusText.className = "status-value attacking";
        intensityWrap.style.display = "flex";
        const pct = (data.attack_intensity || 0) * 100;
        intensityBar.style.width = pct + "%";
        intensityValue.textContent = pct.toFixed(0) + "%";
    } else if (data.quarantine && data.quarantine.active) {
        statusText.textContent = "🛡️ QUARANTINE ACTIVE — Threat neutralized";
        statusText.className = "status-value defended";
        intensityWrap.style.display = "none";
    } else {
        statusText.textContent = "No attack active";
        statusText.className = "status-value";
        intensityWrap.style.display = "none";
    }
}

// ══════════════════════════════════════════════════════════════
// Quarantine Panel
// ══════════════════════════════════════════════════════════════

function updateQuarantinePanel(quarantine) {
    const section = document.getElementById("quarantine-section");
    if (!quarantine) {
        section.style.display = "none";
        return;
    }

    const isActive = quarantine.active;
    const progress = quarantine.restoration_progress_pct || 0;
    const action = quarantine.action_taken || "NONE";

    if (isActive || action === "RESTORING" || action === "QUARANTINE") {
        section.style.display = "block";

        // Trigger flash on first quarantine detection
        if (isActive && !previousQuarantineActive) {
            triggerQuarantineFlash();
        }

        const title = document.getElementById("quarantine-title");
        const detail = document.getElementById("quarantine-detail");
        const progressBar = document.getElementById("quarantine-progress");
        const pctText = document.getElementById("quarantine-pct");
        const bar = document.getElementById("quarantine-section");

        if (action === "RESTORING" || progress > 0) {
            title.textContent = "RESTORING — Slice Isolation";
            detail.textContent = `Re-establishing normal isolation boundaries... ${quarantine.countdown || 0} ticks remaining`;
            bar.className = "quarantine-bar restoring";
        } else {
            title.textContent = "⚠️ QUARANTINE ACTIVE";
            detail.textContent = "Compromised slice boundary isolated. SMF session terminated.";
            bar.className = "quarantine-bar";
        }

        progressBar.style.width = progress + "%";
        pctText.textContent = progress.toFixed(0) + "%";
    } else if (action === "RESTORED") {
        // Show briefly then hide
        section.style.display = "block";
        document.getElementById("quarantine-title").textContent = "✅ RESTORED";
        document.getElementById("quarantine-detail").textContent = "All slices operating normally. Isolation boundaries intact.";
        document.getElementById("quarantine-progress").style.width = "100%";
        document.getElementById("quarantine-pct").textContent = "100%";
        document.getElementById("quarantine-section").className = "quarantine-bar restoring";

        setTimeout(() => { section.style.display = "none"; }, 5000);
    } else {
        section.style.display = "none";
    }

    previousQuarantineActive = isActive;
}

function triggerQuarantineFlash() {
    const flash = document.getElementById("quarantine-flash");
    flash.classList.add("active");
    setTimeout(() => flash.classList.remove("active"), 600);
}

// ══════════════════════════════════════════════════════════════
// Alert Log
// ══════════════════════════════════════════════════════════════

function updateAlertLog(alerts) {
    const log = document.getElementById("alert-log");
    const countEl = document.getElementById("alert-count");

    if (!alerts || alerts.length === 0) {
        log.innerHTML = '<div class="alert-empty">No threats detected — all slices nominal</div>';
        countEl.textContent = "0 alerts";
        return;
    }

    countEl.textContent = `${alerts.length} alerts`;

    // Build alert items (most recent first)
    const items = alerts.reverse().map(alert => {
        const time = new Date(alert.timestamp * 1000);
        const timeStr = time.toLocaleTimeString();
        const icon = getAttackIcon(alert.attack);
        const typeName = (alert.attack || "unknown").replace(/_/g, " ");
        const severity = alert.severity || "LOW";

        return `
            <div class="alert-item ${severity}">
                <span class="alert-time">${timeStr}</span>
                <span class="alert-icon">${icon}</span>
                <span class="alert-type">${typeName}</span>
                <span class="alert-severity ${severity}">${severity}</span>
                <span class="alert-action">${alert.action || "—"}</span>
            </div>
        `;
    }).join("");

    log.innerHTML = items;
}

function getAttackIcon(type) {
    switch (type) {
        case "resource_theft": return "💥";
        case "data_injection": return "💉";
        case "side_channel": return "👁️";
        default: return "⚠️";
    }
}

// ══════════════════════════════════════════════════════════════
// Charts
// ══════════════════════════════════════════════════════════════

function initCharts() {
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: {
                labels: {
                    color: "#94a3b8",
                    font: { family: "'Share Tech Mono', monospace", size: 10 }
                }
            }
        },
        scales: {
            x: {
                display: false,
                grid: { color: "rgba(255,255,255,0.03)" }
            },
            y: {
                grid: { color: "rgba(255,255,255,0.05)" },
                ticks: {
                    color: "#475569",
                    font: { family: "'Share Tech Mono', monospace", size: 10 }
                }
            }
        }
    };

    // URLLC Latency Chart (main chart)
    charts.latency = new Chart(document.getElementById("chart-latency"), {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "URLLC Latency (ms)",
                data: [],
                borderColor: "#ef4444",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
            }, {
                label: "SLA Threshold (1ms)",
                data: [],
                borderColor: "rgba(255, 170, 0, 0.5)",
                borderWidth: 1,
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false,
            }]
        },
        options: { ...baseOptions }
    });

    // Anomaly Score Chart
    charts.anomaly = new Chart(document.getElementById("chart-anomaly"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "eMBB", data: [], borderColor: "#3b82f6", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                { label: "URLLC", data: [], borderColor: "#ef4444", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                { label: "mMTC", data: [], borderColor: "#22c55e", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                { label: "Threshold", data: [], borderColor: "rgba(255,170,0,0.4)", borderWidth: 1, borderDash: [4,4], pointRadius: 0, fill: false },
            ]
        },
        options: {
            ...baseOptions,
            scales: {
                ...baseOptions.scales,
                y: { ...baseOptions.scales.y, min: 0, max: 1 }
            }
        }
    });

    // eMBB Bandwidth
    charts.bandwidth = new Chart(document.getElementById("chart-bandwidth"), {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Bandwidth (Mbps)",
                data: [],
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
            }]
        },
        options: baseOptions
    });

    // CPU Usage per slice
    charts.cpu = new Chart(document.getElementById("chart-cpu"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "eMBB", data: [], borderColor: "#3b82f6", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                { label: "URLLC", data: [], borderColor: "#ef4444", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                { label: "mMTC", data: [], borderColor: "#22c55e", borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
            ]
        },
        options: {
            ...baseOptions,
            scales: {
                ...baseOptions.scales,
                y: { ...baseOptions.scales.y, min: 0, max: 100 }
            }
        }
    });

    // mMTC Packet Rate
    charts.packets = new Chart(document.getElementById("chart-packets"), {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Packet Rate (pps)",
                data: [],
                borderColor: "#22c55e",
                backgroundColor: "rgba(34, 197, 94, 0.1)",
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
            }]
        },
        options: baseOptions
    });
}

async function updateChartsFromAPI() {
    try {
        const [latRes, bwRes, cpuEmbbRes, cpuUrllcRes, cpuMmtcRes, pktRes] = await Promise.all([
            fetch(`${API_BASE}/timeseries?slice=URLLC&metric=latency_ms&n=${CHART_HISTORY}`),
            fetch(`${API_BASE}/timeseries?slice=eMBB&metric=bandwidth_mbps&n=${CHART_HISTORY}`),
            fetch(`${API_BASE}/timeseries?slice=eMBB&metric=cpu_usage_pct&n=${CHART_HISTORY}`),
            fetch(`${API_BASE}/timeseries?slice=URLLC&metric=cpu_usage_pct&n=${CHART_HISTORY}`),
            fetch(`${API_BASE}/timeseries?slice=mMTC&metric=cpu_usage_pct&n=${CHART_HISTORY}`),
            fetch(`${API_BASE}/timeseries?slice=mMTC&metric=packet_rate_pps&n=${CHART_HISTORY}`),
        ]);

        const latData = await latRes.json();
        const bwData = await bwRes.json();
        const cpuEmbb = await cpuEmbbRes.json();
        const cpuUrllc = await cpuUrllcRes.json();
        const cpuMmtc = await cpuMmtcRes.json();
        const pktData = await pktRes.json();

        const labels = latData.values.map((_, i) => i);

        // URLLC Latency
        charts.latency.data.labels = labels;
        charts.latency.data.datasets[0].data = latData.values;
        charts.latency.data.datasets[1].data = latData.values.map(() => 1.0); // SLA line
        charts.latency.update("none");

        // Update latency badge
        const maxLat = Math.max(...(latData.values || [0]));
        const latBadge = document.getElementById("latency-badge");
        if (maxLat > 2.0) {
            latBadge.textContent = "CRITICAL";
            latBadge.className = "chart-badge critical";
        } else if (maxLat > 1.0) {
            latBadge.textContent = "WARNING";
            latBadge.className = "chart-badge warning";
        } else {
            latBadge.textContent = "NOMINAL";
            latBadge.className = "chart-badge nominal";
        }

        // eMBB Bandwidth
        charts.bandwidth.data.labels = labels;
        charts.bandwidth.data.datasets[0].data = bwData.values;
        charts.bandwidth.update("none");

        // CPU usage
        charts.cpu.data.labels = labels;
        charts.cpu.data.datasets[0].data = cpuEmbb.values;
        charts.cpu.data.datasets[1].data = cpuUrllc.values;
        charts.cpu.data.datasets[2].data = cpuMmtc.values;
        charts.cpu.update("none");

        // mMTC Packets
        charts.packets.data.labels = labels;
        charts.packets.data.datasets[0].data = pktData.values;
        charts.packets.update("none");

        // Anomaly scores from latest slice data
        updateAnomalyChart();

    } catch (e) {
        console.error("[Charts] Failed to fetch time series:", e);
    }
}

// Anomaly score history
const anomalyHistory = {
    eMBB: [], URLLC: [], mMTC: []
};

function updateAnomalyChart() {
    if (!lastData || !lastData.slices) return;

    for (const name of ["eMBB", "URLLC", "mMTC"]) {
        const score = lastData.slices[name]?.analysis?.combined_score || 0;
        anomalyHistory[name].push(score);
        if (anomalyHistory[name].length > CHART_HISTORY) {
            anomalyHistory[name].shift();
        }
    }

    const labels = anomalyHistory.eMBB.map((_, i) => i);
    charts.anomaly.data.labels = labels;
    charts.anomaly.data.datasets[0].data = [...anomalyHistory.eMBB];
    charts.anomaly.data.datasets[1].data = [...anomalyHistory.URLLC];
    charts.anomaly.data.datasets[2].data = [...anomalyHistory.mMTC];
    charts.anomaly.data.datasets[3].data = labels.map(() => 0.65); // threshold
    charts.anomaly.update("none");

    // Anomaly badge
    const maxAnomaly = Math.max(
        anomalyHistory.eMBB[anomalyHistory.eMBB.length - 1] || 0,
        anomalyHistory.URLLC[anomalyHistory.URLLC.length - 1] || 0,
        anomalyHistory.mMTC[anomalyHistory.mMTC.length - 1] || 0
    );
    const anomBadge = document.getElementById("anomaly-badge");
    if (maxAnomaly > 0.65) {
        anomBadge.textContent = "HIGH THREAT";
        anomBadge.className = "chart-badge critical";
    } else if (maxAnomaly > 0.4) {
        anomBadge.textContent = "ELEVATED";
        anomBadge.className = "chart-badge warning";
    } else {
        anomBadge.textContent = "LOW";
        anomBadge.className = "chart-badge nominal";
    }
}

// ══════════════════════════════════════════════════════════════
// Utility
// ══════════════════════════════════════════════════════════════

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}
