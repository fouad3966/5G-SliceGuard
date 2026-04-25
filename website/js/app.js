/* ========================================
   5G SliceGuard — Intrusion Detection & Automated Response
   Main Application Logic
   ======================================== */

// ========== NAVBAR ==========
const navbar = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
});

hamburger?.addEventListener('click', () => {
    navLinks.classList.toggle('open');
});

// Close mobile menu on link click
navLinks?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// ========== SCROLL REVEAL ==========
const revealElements = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

revealElements.forEach(el => revealObserver.observe(el));

// ========== HERO BACKGROUND CANVAS ==========
(function initHeroCanvas() {
    const canvas = document.getElementById('heroBgCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    const PARTICLE_COUNT = 80;
    const COLORS = ['#00b4d8', '#ff006e', '#39ff14', '#7b61ff'];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.radius = Math.random() * 2 + 0.5;
            this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
            this.alpha = Math.random() * 0.4 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.alpha;
            ctx.fill();
            ctx.globalAlpha = 1;
        }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }

    function drawConnections() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = particles[i].color;
                    ctx.globalAlpha = (1 - dist / 150) * 0.08;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        drawConnections();
        requestAnimationFrame(animate);
    }
    animate();
})();

// ========== ATTACK TYPE SELECTOR ==========
document.querySelectorAll('.attack-option').forEach(option => {
    option.addEventListener('click', () => {
        document.querySelectorAll('.attack-option').forEach(o => o.classList.remove('selected'));
        option.classList.add('selected');
        option.querySelector('input').checked = true;
    });
});

// ========== CHARTS ==========
const chartColors = {
    embb: { main: '#00b4d8', bg: 'rgba(0, 180, 216, 0.15)' },
    urllc: { main: '#ff006e', bg: 'rgba(255, 0, 110, 0.15)' },
    mmtc: { main: '#39ff14', bg: 'rgba(57, 255, 20, 0.15)' },
    danger: { main: '#ff3860', bg: 'rgba(255, 56, 96, 0.15)' },
};

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    scales: {
        x: {
            display: true,
            grid: { color: 'rgba(255,255,255,0.03)' },
            ticks: { color: 'rgba(255,255,255,0.25)', font: { size: 9, family: 'JetBrains Mono' }, maxTicksLimit: 6 }
        },
        y: {
            display: true,
            grid: { color: 'rgba(255,255,255,0.03)' },
            ticks: { color: 'rgba(255,255,255,0.25)', font: { size: 9, family: 'JetBrains Mono' }, maxTicksLimit: 5 }
        }
    },
    plugins: {
        legend: { display: true, labels: { color: 'rgba(255,255,255,0.4)', font: { size: 10 }, boxWidth: 8, padding: 8 } }
    }
};

const MAX_DATA_POINTS = 30;
const labels = [];
for (let i = 0; i < MAX_DATA_POINTS; i++) labels.push('');

// Throughput Chart
const throughputChart = new Chart(document.getElementById('chartThroughput'), {
    type: 'line',
    data: {
        labels: [...labels],
        datasets: [
            { label: 'eMBB', data: [], borderColor: chartColors.embb.main, backgroundColor: chartColors.embb.bg, fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 },
            { label: 'URLLC', data: [], borderColor: chartColors.urllc.main, backgroundColor: chartColors.urllc.bg, fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 },
            { label: 'mMTC', data: [], borderColor: chartColors.mmtc.main, backgroundColor: chartColors.mmtc.bg, fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 },
        ]
    },
    options: { ...chartDefaults }
});

// Latency Chart
const latencyChart = new Chart(document.getElementById('chartLatency'), {
    type: 'line',
    data: {
        labels: [...labels],
        datasets: [
            { label: 'eMBB', data: [], borderColor: chartColors.embb.main, tension: 0.4, borderWidth: 2, pointRadius: 0 },
            { label: 'URLLC', data: [], borderColor: chartColors.urllc.main, tension: 0.4, borderWidth: 2, pointRadius: 0 },
            { label: 'mMTC', data: [], borderColor: chartColors.mmtc.main, tension: 0.4, borderWidth: 2, pointRadius: 0 },
        ]
    },
    options: { ...chartDefaults }
});

// Anomaly Chart
const anomalyChart = new Chart(document.getElementById('chartAnomaly'), {
    type: 'line',
    data: {
        labels: [...labels],
        datasets: [
            { label: 'Threat Level', data: [], borderColor: chartColors.danger.main, backgroundColor: chartColors.danger.bg, fill: true, tension: 0.3, borderWidth: 2, pointRadius: 0 }
        ]
    },
    options: {
        ...chartDefaults,
        scales: {
            ...chartDefaults.scales,
            y: { ...chartDefaults.scales.y, min: 0, max: 100 }
        }
    }
});

// Distribution Chart (Pie)
const distributionChart = new Chart(document.getElementById('chartDistribution'), {
    type: 'doughnut',
    data: {
        labels: ['eMBB', 'URLLC', 'mMTC'],
        datasets: [{
            data: [55, 25, 20],
            backgroundColor: [chartColors.embb.main, chartColors.urllc.main, chartColors.mmtc.main],
            borderColor: 'transparent',
            borderWidth: 0,
            hoverOffset: 8
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
            legend: { display: true, position: 'bottom', labels: { color: 'rgba(255,255,255,0.4)', font: { size: 10 }, boxWidth: 8, padding: 10 } }
        }
    }
});

// ========== SIMULATOR ENGINE ==========
class SliceSimulator {
    constructor() {
        this.canvas = document.getElementById('simCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.statusBadge = document.getElementById('simStatusBadge');
        this.timerEl = document.getElementById('simTimer');
        
        this.state = 'idle'; // idle, running, attack, detected
        this.startTime = 0;
        this.elapsedSeconds = 0;
        this.animationId = null;
        this.dataInterval = null;
        
        // Slices
        this.slices = [
            { name: 'eMBB', color: '#00b4d8', icon: '📹', packets: [], throughput: 800, latency: 4, baseThru: 800, baseLat: 4 },
            { name: 'URLLC', color: '#ff006e', icon: '🚗', packets: [], throughput: 400, latency: 1, baseThru: 400, baseLat: 1 },
            { name: 'mMTC', color: '#39ff14', icon: '📡', packets: [], throughput: 200, latency: 10, baseThru: 200, baseLat: 10 }
        ];
        
        // Attack state
        this.attackActive = false;
        this.attackType = 'resource_theft';
        this.attackPackets = [];
        this.detectionActive = false;
        this.anomalyScore = 0;
        this.shieldPulse = 0;
        
        // Data history
        this.dataHistory = { embbThru: [], urllcThru: [], mmtcThru: [], embbLat: [], urllcLat: [], mmtcLat: [], anomaly: [] };
        
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        this.drawIdleState();
    }
    
    resizeCanvas() {
        const container = document.getElementById('simCanvasContainer');
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.sliceHeight = (this.canvas.height - 100) / 3;
        this.sliceStartY = 50;
    }
    
    getAttackType() {
        const selected = document.querySelector('input[name="attackType"]:checked');
        return selected ? selected.value : 'resource_theft';
    }
    
    setStatus(state, text) {
        this.state = state;
        const badge = this.statusBadge;
        badge.className = 'sim-status-badge ' + state;
        badge.querySelector('span').textContent = text;
    }
    
    updateTimer() {
        this.elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);
        const mins = String(Math.floor(this.elapsedSeconds / 60)).padStart(2, '0');
        const secs = String(this.elapsedSeconds % 60).padStart(2, '0');
        this.timerEl.textContent = `${mins}:${secs}`;
    }
    
    addAlert(message, type = 'danger') {
        const log = document.getElementById('alertLog');
        const now = new Date();
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        const entry = document.createElement('div');
        entry.className = `alert-entry ${type}`;
        
        const iconMap = { danger: 'fa-skull-crossbones', warning: 'fa-triangle-exclamation', success: 'fa-shield-halved', info: 'fa-info-circle' };
        const colorMap = { danger: 'var(--danger)', warning: 'var(--warning)', success: 'var(--success)', info: 'var(--text-secondary)' };
        
        entry.innerHTML = `
            <span class="alert-time">${time}</span>
            <i class="fas ${iconMap[type] || iconMap.info}" style="color:${colorMap[type]}"></i>
            <span>${message}</span>
        `;
        
        // Remove "waiting" message
        const waiting = log.querySelector('.alert-entry:first-child');
        if (waiting && waiting.textContent.includes('Waiting')) {
            log.removeChild(waiting);
        }
        
        log.prepend(entry);
        
        // Keep only last 50 entries
        while (log.children.length > 50) {
            log.removeChild(log.lastChild);
        }
    }
    
    updateMetrics() {
        const embb = this.slices[0];
        const urllc = this.slices[1];
        const mmtc = this.slices[2];
        
        document.getElementById('metricEmbb').textContent = `${Math.round(embb.throughput)} Mbps`;
        document.getElementById('metricUrllc').textContent = `${urllc.latency.toFixed(1)} ms`;
        document.getElementById('metricMmtc').textContent = `${Math.round(mmtc.throughput * 5)} dev`;
        document.getElementById('metricAnomaly').textContent = `${Math.round(this.anomalyScore)}%`;
        
        // Color anomaly based on value
        const anomalyEl = document.getElementById('metricAnomaly');
        if (this.anomalyScore > 60) anomalyEl.style.color = 'var(--danger)';
        else if (this.anomalyScore > 30) anomalyEl.style.color = 'var(--warning)';
        else anomalyEl.style.color = 'var(--success)';
    }
    
    pushChartData() {
        const embb = this.slices[0];
        const urllc = this.slices[1];
        const mmtc = this.slices[2];
        
        // Add noise for realism
        const noise = () => (Math.random() - 0.5) * 20;
        const noiseSmall = () => (Math.random() - 0.5) * 0.5;
        
        // Throughput
        this.dataHistory.embbThru.push(embb.throughput + noise());
        this.dataHistory.urllcThru.push(urllc.throughput + noise() * 0.5);
        this.dataHistory.mmtcThru.push(mmtc.throughput + noise() * 0.3);
        
        // Latency
        this.dataHistory.embbLat.push(embb.latency + noiseSmall());
        this.dataHistory.urllcLat.push(urllc.latency + noiseSmall() * 0.2);
        this.dataHistory.mmtcLat.push(mmtc.latency + noiseSmall());
        
        // Anomaly
        this.dataHistory.anomaly.push(this.anomalyScore);
        
        // Trim to max
        Object.keys(this.dataHistory).forEach(key => {
            if (this.dataHistory[key].length > MAX_DATA_POINTS) {
                this.dataHistory[key].shift();
            }
        });
        
        // Update charts
        throughputChart.data.datasets[0].data = [...this.dataHistory.embbThru];
        throughputChart.data.datasets[1].data = [...this.dataHistory.urllcThru];
        throughputChart.data.datasets[2].data = [...this.dataHistory.mmtcThru];
        throughputChart.update('none');
        
        latencyChart.data.datasets[0].data = [...this.dataHistory.embbLat];
        latencyChart.data.datasets[1].data = [...this.dataHistory.urllcLat];
        latencyChart.data.datasets[2].data = [...this.dataHistory.mmtcLat];
        latencyChart.update('none');
        
        anomalyChart.data.datasets[0].data = [...this.dataHistory.anomaly];
        anomalyChart.update('none');
        
        // Update distribution
        const total = embb.throughput + urllc.throughput + mmtc.throughput;
        distributionChart.data.datasets[0].data = [
            Math.round(embb.throughput / total * 100),
            Math.round(urllc.throughput / total * 100),
            Math.round(mmtc.throughput / total * 100)
        ];
        distributionChart.update('none');
    }
    
    // ========== DRAWING ==========
    drawIdleState() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        ctx.clearRect(0, 0, w, h);
        
        // Draw grid
        ctx.strokeStyle = 'rgba(255,255,255,0.03)';
        ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }
        for (let y = 0; y < h; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }
        
        // Centered text
        ctx.fillStyle = 'rgba(255,255,255,0.15)';
        ctx.font = '600 18px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Press START to begin simulation', w / 2, h / 2);
        ctx.font = '400 13px Inter';
        ctx.fillStyle = 'rgba(255,255,255,0.08)';
        ctx.fillText('5G SliceGuard · Defense Validation Testbed', w / 2, h / 2 + 30);
        ctx.textAlign = 'left';
    }
    
    drawFrame() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        ctx.clearRect(0, 0, w, h);
        
        // Grid background
        ctx.strokeStyle = 'rgba(255,255,255,0.02)';
        ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 40) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = 0; y < h; y += 40) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
        
        // Draw each slice lane
        this.slices.forEach((slice, i) => {
            const y = this.sliceStartY + i * this.sliceHeight;
            const laneH = this.sliceHeight - 12;
            
            // Lane background
            const grad = ctx.createLinearGradient(0, y, 0, y + laneH);
            grad.addColorStop(0, this.hexToRGBA(slice.color, 0.06));
            grad.addColorStop(1, this.hexToRGBA(slice.color, 0.02));
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.roundRect(20, y, w - 40, laneH, 12);
            ctx.fill();
            
            // Lane border
            let borderAlpha = 0.15;
            if (this.attackActive && !this.detectionActive) {
                // Make attacked slices pulse
                borderAlpha = 0.15 + Math.sin(Date.now() / 200) * 0.1;
            }
            if (this.detectionActive) {
                borderAlpha = 0.3;
                ctx.strokeStyle = '#23d160';
            } else {
                ctx.strokeStyle = this.hexToRGBA(slice.color, borderAlpha);
            }
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(20, y, w - 40, laneH, 12);
            ctx.stroke();
            
            // Slice label
            ctx.fillStyle = slice.color;
            ctx.font = '700 13px Inter';
            ctx.fillText(`${slice.icon} ${slice.name}`, 36, y + 24);
            
            // Slice stats in lane
            ctx.font = '500 11px JetBrains Mono';
            ctx.fillStyle = this.hexToRGBA(slice.color, 0.6);
            ctx.fillText(`THR: ${Math.round(slice.throughput)}Mbps  LAT: ${slice.latency.toFixed(1)}ms`, 36, y + laneH - 12);
            
            // Draw packets
            slice.packets.forEach(pkt => {
                const px = pkt.x;
                const py = y + pkt.yOffset;
                
                // Packet glow
                const glow = ctx.createRadialGradient(px, py, 0, px, py, 12);
                glow.addColorStop(0, this.hexToRGBA(pkt.color || slice.color, 0.4));
                glow.addColorStop(1, 'transparent');
                ctx.fillStyle = glow;
                ctx.beginPath();
                ctx.arc(px, py, 12, 0, Math.PI * 2);
                ctx.fill();
                
                // Packet dot
                ctx.fillStyle = pkt.color || slice.color;
                ctx.beginPath();
                ctx.arc(px, py, pkt.size || 4, 0, Math.PI * 2);
                ctx.fill();
            });
            
            // Isolation barrier lines between slices
            if (i < this.slices.length - 1) {
                const barrierY = y + laneH + 6;
                ctx.setLineDash([8, 8]);
                
                if (this.attackActive && !this.detectionActive) {
                    ctx.strokeStyle = 'rgba(255, 56, 96, 0.4)';
                    ctx.lineWidth = 2;
                } else if (this.detectionActive) {
                    ctx.strokeStyle = 'rgba(35, 209, 96, 0.5)';
                    ctx.lineWidth = 2;
                } else {
                    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
                    ctx.lineWidth = 1;
                }
                
                ctx.beginPath();
                ctx.moveTo(30, barrierY);
                ctx.lineTo(w - 30, barrierY);
                ctx.stroke();
                ctx.setLineDash([]);
                
                // Barrier label
                ctx.fillStyle = 'rgba(255,255,255,0.1)';
                ctx.font = '500 9px Inter';
                ctx.fillText('ISOLATION BARRIER', w / 2 - 45, barrierY - 2);
            }
        });
        
        // Draw attack packets crossing slices
        this.attackPackets.forEach(ap => {
            // Trail
            ctx.strokeStyle = this.hexToRGBA('#ff3860', 0.3);
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(ap.sx, ap.sy);
            ctx.lineTo(ap.x, ap.y);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Glow
            const glow = ctx.createRadialGradient(ap.x, ap.y, 0, ap.x, ap.y, 16);
            glow.addColorStop(0, 'rgba(255, 56, 96, 0.6)');
            glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(ap.x, ap.y, 16, 0, Math.PI * 2);
            ctx.fill();
            
            // Attack packet (triangle)
            ctx.fillStyle = '#ff3860';
            ctx.beginPath();
            ctx.moveTo(ap.x, ap.y - 6);
            ctx.lineTo(ap.x - 5, ap.y + 4);
            ctx.lineTo(ap.x + 5, ap.y + 4);
            ctx.closePath();
            ctx.fill();
        });
        
        // Detection shield effect
        if (this.detectionActive && this.shieldPulse > 0) {
            this.slices.forEach((slice, i) => {
                const y = this.sliceStartY + i * this.sliceHeight;
                const laneH = this.sliceHeight - 12;
                
                ctx.strokeStyle = `rgba(35, 209, 96, ${this.shieldPulse * 0.3})`;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.roundRect(18, y - 2, w - 36, laneH + 4, 14);
                ctx.stroke();
            });
            
            // Shield icon in center
            ctx.fillStyle = `rgba(35, 209, 96, ${this.shieldPulse * 0.8})`;
            ctx.font = '600 14px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('🛡️ SLICEGUARD IDS ACTIVE — THREAT QUARANTINED', w / 2, h - 16);
            ctx.textAlign = 'left';
            
            this.shieldPulse = Math.max(0, this.shieldPulse - 0.002);
        }
        
        // Attack warning overlay
        if (this.attackActive && !this.detectionActive) {
            const flash = Math.sin(Date.now() / 300) * 0.5 + 0.5;
            ctx.fillStyle = `rgba(255, 56, 96, ${flash * 0.03})`;
            ctx.fillRect(0, 0, w, h);
            
            ctx.fillStyle = `rgba(255, 56, 96, ${0.5 + flash * 0.5})`;
            ctx.font = '700 12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('⚠️ THREAT DETECTED — ISOLATION BREACH IN PROGRESS', w / 2, h - 16);
            ctx.textAlign = 'left';
        }
    }
    
    // ========== PACKET MANAGEMENT ==========
    spawnPackets() {
        this.slices.forEach((slice, i) => {
            const y = this.sliceStartY + i * this.sliceHeight;
            const laneH = this.sliceHeight - 12;
            
            // Spawn rate based on throughput
            const rate = Math.floor(slice.throughput / 200) + 1;
            
            if (Math.random() < rate * 0.15) {
                slice.packets.push({
                    x: 30,
                    yOffset: 30 + Math.random() * (laneH - 50),
                    speed: 1.5 + Math.random() * 2.5,
                    size: 3 + Math.random() * 3,
                    color: null // Use slice color
                });
            }
        });
    }
    
    updatePackets() {
        const w = this.canvas.width;
        
        this.slices.forEach(slice => {
            slice.packets = slice.packets.filter(pkt => {
                pkt.x += pkt.speed;
                return pkt.x < w - 20;
            });
        });
        
        // Update attack packets
        this.attackPackets = this.attackPackets.filter(ap => {
            ap.x += ap.vx;
            ap.y += ap.vy;
            ap.life--;
            return ap.life > 0 && ap.x > 0 && ap.x < w;
        });
    }
    
    // ========== ATTACK LOGIC ==========
    launchAttack() {
        if (this.state !== 'running') return;
        
        this.attackType = this.getAttackType();
        this.attackActive = true;
        this.detectionActive = false;
        this.shieldPulse = 0;
        this.setStatus('attack', `THREAT: ${this.attackType.replace('_', ' ').toUpperCase()}`);
        
        document.getElementById('btnDetect').disabled = false;
        
        const attackNames = {
            'resource_theft': 'Resource Theft',
            'data_injection': 'Data Injection',
            'side_channel': 'Side-Channel'
        };
        
        this.addAlert(`${attackNames[this.attackType]} threat injected into network`, 'danger');
        this.addAlert('SliceGuard monitoring isolation boundaries...', 'warning');
        
        // Set attack-specific narration
        const narrations = {
            'resource_theft': {
                title: '⚠️ Threat: Resource Theft Attack',
                text: `An attacker on the <strong style="color: var(--mmtc-color)">mMTC slice</strong> (IoT — low security) is ` +
                    `<strong style="color: var(--danger)">stealing bandwidth</strong> from the <strong style="color: var(--embb-color)">eMBB slice</strong>. ` +
                    `<br><br><strong>How:</strong> The attacker exploits shared UPF (User Plane Function) resources. By flooding the shared data plane, ` +
                    `they consume bandwidth allocated to eMBB, causing its throughput to <strong>drop from 800→320 Mbps</strong>. ` +
                    `The URLLC slice's latency also spikes because the same physical CPU/memory is used by all slices. ` +
                    `<br><br><strong>Watch the charts:</strong> See eMBB throughput crash and URLLC latency spike. The red triangles crossing the isolation barriers represent unauthorized cross-slice traffic.`
            },
            'data_injection': {
                title: '⚠️ Threat: Cross-Slice Data Injection',
                text: `An attacker is <strong style="color: var(--danger)">injecting malicious packets</strong> from the mMTC slice directly ` +
                    `into the <strong style="color: var(--urllc-color)">URLLC slice</strong> (autonomous vehicles, remote surgery). ` +
                    `<br><br><strong>How:</strong> By exploiting a vulnerability in the hypervisor or shared VNF (Virtual Network Function), ` +
                    `the attacker crafts packets that bypass the slice boundary. These rogue packets corrupt URLLC data — ` +
                    `potentially sending <strong>false commands to autonomous vehicles</strong> or disrupting surgical robot telemetry. ` +
                    `<br><br><strong>Watch:</strong> URLLC latency jumps 5x (from 1ms to 5ms) and throughput drops. The red triangles show malicious packets crossing the isolation barrier.`
            },
            'side_channel': {
                title: '⚠️ Threat: Side-Channel Information Leakage',
                text: `This is the <strong>most subtle attack</strong>. The attacker doesn't directly steal resources — instead they ` +
                    `<strong style="color: var(--danger)">infer sensitive data</strong> from the URLLC slice by monitoring shared hardware behavior. ` +
                    `<br><br><strong>How:</strong> By measuring cache-timing patterns and memory access latencies on the shared physical server, ` +
                    `the attacker can deduce what the URLLC slice is processing (e.g., patient medical data, vehicle routes). ` +
                    `Metrics barely change — latency increases only slightly (~20%) — making this <strong>nearly invisible to simple rule-based detectors</strong>. ` +
                    `<br><br><strong>Watch:</strong> The threat level still rises because SliceGuard's ML classifier detects the subtle timing anomalies that rule-based systems miss.`
            }
        };
        const narr = narrations[this.attackType];
        this.setNarration(narr.title, narr.text, 'fa-skull-crossbones', 'danger');
        
        // Modify slice metrics based on attack type
        this.applyAttackEffects();
        
        // Spawn cross-slice attack packets
        this.attackPacketInterval = setInterval(() => {
            if (!this.attackActive) return;
            this.spawnAttackPacket();
        }, 300);
    }
    
    applyAttackEffects() {
        const embb = this.slices[0];
        const urllc = this.slices[1];
        const mmtc = this.slices[2];
        
        switch (this.attackType) {
            case 'resource_theft':
                // Attacker on mMTC steals bandwidth from eMBB
                embb.throughput = embb.baseThru * 0.4;
                urllc.latency = urllc.baseLat * 3;
                mmtc.throughput = mmtc.baseThru * 2.5;
                this.addAlert('eMBB throughput dropping — bandwidth stolen', 'danger');
                this.addAlert('URLLC latency spiking — resource contention', 'danger');
                break;
            case 'data_injection':
                urllc.latency = urllc.baseLat * 5;
                urllc.throughput = urllc.baseThru * 0.6;
                this.addAlert('Malicious packets injected into URLLC slice', 'danger');
                this.addAlert('URLLC integrity compromised', 'danger');
                break;
            case 'side_channel':
                // Subtle — metrics barely change but anomaly score rises
                embb.latency = embb.baseLat * 1.3;
                urllc.latency = urllc.baseLat * 1.2;
                this.addAlert('Side-channel timing attack detected on shared cache', 'danger');
                this.addAlert('Information leakage through resource timing', 'warning');
                break;
        }
    }
    
    spawnAttackPacket() {
        const w = this.canvas.width;
        const fromSlice = 2; // mMTC (attacker)
        const toSlice = Math.random() > 0.5 ? 0 : 1; // Target eMBB or URLLC
        
        const fromY = this.sliceStartY + fromSlice * this.sliceHeight + this.sliceHeight / 2;
        const toY = this.sliceStartY + toSlice * this.sliceHeight + this.sliceHeight / 2;
        
        const sx = 100 + Math.random() * (w - 200);
        
        this.attackPackets.push({
            x: sx, y: fromY,
            sx: sx, sy: fromY,
            vx: (Math.random() - 0.5) * 2,
            vy: (toY - fromY) / 60,
            life: 80
        });
    }
    
    // ========== DETECTION LOGIC ==========
    runDetection() {
        if (!this.attackActive) return;
        
        this.detectionActive = true;
        this.shieldPulse = 1;
        this.setStatus('detected', 'IDS: QUARANTINED');
        
        this.addAlert('SliceGuard IDS engaged — correlating threat signals', 'success');
        
        // Set detection narration
        this.setNarration(
            '🛡️ SliceGuard IDS — Automated Response',
            `SliceGuard's multi-layer IDS has engaged. Here's what's happening in sequence:` +
            `<br><br><strong>1. Behavioral Baseline Engine</strong> — Compares current metrics to established baselines. ` +
            `Detects the throughput/latency deviations as anomalous (Z-score > 3σ).` +
            `<br><strong>2. Boundary Violation Detector</strong> — DPI probes detect unauthorized packets crossing the isolation barrier.` +
            `<br><strong>3. ML Classifier</strong> — Isolation Forest model confirms the threat signature.` +
            `<br><strong>4. Auto-Quarantine</strong> — The compromised slice boundary is hardened. Malicious flows are blocked. ` +
            `Metrics will restore to normal within seconds.` +
            `<br><br><strong>Watch:</strong> The barriers turn <strong style="color: var(--success)">green</strong> (hardened), ` +
            `attack packets disappear, and all metrics return to baseline. The threat level drops back to ~5%.`,
            'fa-shield-halved', 'success'
        );
        
        // Gradually restore metrics
        setTimeout(() => {
            this.addAlert('Threat classified: cross-slice isolation violation', 'success');
        }, 800);
        
        setTimeout(() => {
            this.addAlert('Auto-quarantine: isolating compromised boundary', 'success');
        }, 1600);
        
        setTimeout(() => {
            this.addAlert('Slice isolation restored — boundaries hardened', 'success');
            this.restoreNormalMetrics();
        }, 2400);
        
        setTimeout(() => {
            this.attackActive = false;
            this.attackPackets = [];
            clearInterval(this.attackPacketInterval);
            this.addAlert('Threat neutralized — all slices nominal', 'success');
            
            document.getElementById('btnAttack').disabled = false;
            document.getElementById('btnDetect').disabled = true;
        }, 4000);
    }
    
    restoreNormalMetrics() {
        this.slices.forEach(slice => {
            slice.throughput = slice.baseThru;
            slice.latency = slice.baseLat;
        });
    }
    
    // ========== SIMULATION CONTROL ==========
    start() {
        if (this.state === 'running' || this.state === 'attack') return;
        
        this.resizeCanvas();
        this.startTime = Date.now();
        this.setStatus('running', 'MONITORING');
        
        // Clear existing data
        Object.keys(this.dataHistory).forEach(k => this.dataHistory[k] = []);
        
        document.getElementById('btnStart').disabled = true;
        document.getElementById('btnStop').disabled = false;
        document.getElementById('btnAttack').disabled = false;
        
        this.addAlert('SliceGuard IDS online — monitoring all slices', 'info');
        
        // Set narration for running state
        this.setNarration(
            'Normal Operation — All Slices Isolated',
            `SliceGuard is now monitoring 3 virtual network slices running on shared physical infrastructure. ` +
            `<strong style="color: var(--embb-color)">eMBB</strong> (blue) streams at ~800 Mbps for video/VR. ` +
            `<strong style="color: var(--urllc-color)">URLLC</strong> (red) handles critical traffic with 1ms latency for autonomous vehicles. ` +
            `<strong style="color: var(--mmtc-color)">mMTC</strong> (green) manages 1000+ IoT sensors at low power. ` +
            `<br><br><strong>Key point:</strong> Right now, each slice is properly isolated — the dashed lines between lanes are <em>isolation barriers</em>. ` +
            `No packets should cross these boundaries. The charts below show stable throughput, low latency, and a <strong>threat level near 0%</strong>.`,
            'fa-eye', 'info'
        );
        
        // Animation loop
        const animate = () => {
            this.updateTimer();
            this.spawnPackets();
            this.updatePackets();
            this.updateAnomalyScore();
            this.drawFrame();
            this.updateMetrics();
            this.animationId = requestAnimationFrame(animate);
        };
        animate();
        
        // Data push every 500ms
        this.dataInterval = setInterval(() => {
            this.pushChartData();
        }, 500);
    }
    
    stop() {
        this.setStatus('idle', 'PAUSED');
        this.attackActive = false;
        this.detectionActive = false;
        
        cancelAnimationFrame(this.animationId);
        clearInterval(this.dataInterval);
        clearInterval(this.attackPacketInterval);
        
        document.getElementById('btnStart').disabled = false;
        document.getElementById('btnStop').disabled = true;
        document.getElementById('btnAttack').disabled = true;
        document.getElementById('btnDetect').disabled = true;
        
        this.addAlert('Simulation paused', 'info');
    }
    
    reset() {
        this.stop();
        this.state = 'idle';
        this.elapsedSeconds = 0;
        this.timerEl.textContent = '00:00';
        this.anomalyScore = 0;
        this.attackPackets = [];
        
        this.slices.forEach(slice => {
            slice.packets = [];
            slice.throughput = slice.baseThru;
            slice.latency = slice.baseLat;
        });
        
        Object.keys(this.dataHistory).forEach(k => this.dataHistory[k] = []);
        
        // Reset charts
        throughputChart.data.datasets.forEach(d => d.data = []);
        latencyChart.data.datasets.forEach(d => d.data = []);
        anomalyChart.data.datasets[0].data = [];
        distributionChart.data.datasets[0].data = [55, 25, 20];
        [throughputChart, latencyChart, anomalyChart, distributionChart].forEach(c => c.update());
        
        this.updateMetrics();
        this.setStatus('idle', 'IDLE');
        this.drawIdleState();
        
        // Reset narration
        this.setNarration(
            "What's Happening",
            `Press <strong>Start</strong> to activate SliceGuard's monitoring system. The canvas shows 3 isolated network slices running on shared infrastructure: ` +
            `<strong style="color: var(--embb-color);">eMBB</strong> (streaming — blue packets), ` +
            `<strong style="color: var(--urllc-color);">URLLC</strong> (critical systems — red packets), and ` +
            `<strong style="color: var(--mmtc-color);">mMTC</strong> (IoT sensors — green packets). ` +
            `Each lane represents a virtual slice with its own guaranteed QoS.`,
            'fa-comment-dots', 'info'
        );
        
        // Reset alert log
        const log = document.getElementById('alertLog');
        log.innerHTML = `<div class="alert-entry" style="color: var(--text-muted); border-color: var(--border-glass); background: transparent;">
            <i class="fas fa-info-circle"></i> Waiting for simulation...
        </div>`;
        
        document.getElementById('btnStart').disabled = false;
    }
    
    updateAnomalyScore() {
        if (this.attackActive && !this.detectionActive) {
            const targets = {
                'resource_theft': 85,
                'data_injection': 92,
                'side_channel': 65
            };
            const target = targets[this.attackType] || 80;
            this.anomalyScore += (target - this.anomalyScore) * 0.03;
        } else if (this.detectionActive) {
            this.anomalyScore += (5 - this.anomalyScore) * 0.05;
        } else {
            // Normal jitter
            this.anomalyScore += (3 + Math.random() * 4 - this.anomalyScore) * 0.05;
        }
    }
    
    // ========== NARRATION SYSTEM ==========
    setNarration(title, text, icon, type) {
        const panel = document.getElementById('narrationPanel');
        const titleEl = document.getElementById('narrationTitle');
        const textEl = document.getElementById('narrationText');
        const iconEl = document.getElementById('narrationIcon');
        
        if (!panel) return;
        
        titleEl.textContent = title;
        textEl.innerHTML = text;
        iconEl.className = `fas ${icon || 'fa-comment-dots'}`;
        
        // Update panel styling based on type
        panel.classList.remove('narration-alert', 'narration-success');
        if (type === 'danger') {
            panel.classList.add('narration-alert');
            panel.style.borderLeftColor = 'var(--danger)';
            titleEl.style.color = 'var(--danger)';
            iconEl.style.color = 'var(--danger)';
        } else if (type === 'success') {
            panel.classList.add('narration-success');
            panel.style.borderLeftColor = 'var(--success)';
            titleEl.style.color = 'var(--success)';
            iconEl.style.color = 'var(--success)';
        } else {
            panel.style.borderLeftColor = 'var(--accent)';
            titleEl.style.color = 'var(--accent)';
            iconEl.style.color = 'var(--accent)';
        }
    }
    
    // ========== UTILITIES ==========
    hexToRGBA(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
}

// ========== INITIALIZE ==========
const simulator = new SliceSimulator();

// ========== SMOOTH SCROLL FOR ANCHORS ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ========== ACTIVE NAV LINK TRACKING ==========
const sections = document.querySelectorAll('section');
const navLinksAll = document.querySelectorAll('.nav-links a:not(.nav-cta)');

window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        if (window.scrollY >= sectionTop) {
            current = section.getAttribute('id');
        }
    });
    navLinksAll.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
});
