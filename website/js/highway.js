/**
 * Highway Analogy Animation v3
 * Quarantine destroys zombies then auto-resets to normal
 */

class HighwaySimulator {
    constructor() {
        this.canvas = document.getElementById('highwayCanvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        this.mode = 'normal';
        this.cars = [];
        this.particles = [];
        this.quarantineTimer = 0;
        
        // Lane colors for PDU backgrounds
        this.pduColors = {
            embb: ['rgba(0,180,216,0.06)', 'rgba(0,180,216,0.03)', 'rgba(0,180,216,0.06)'],
            urllc: ['rgba(255,0,110,0.06)', 'rgba(255,0,110,0.03)', 'rgba(255,0,110,0.06)'],
            mmtc: ['rgba(57,255,20,0.06)', 'rgba(57,255,20,0.03)', 'rgba(57,255,20,0.06)']
        };

        this.lanes = [
            { name: "eMBB", y: 65, speedMultiplier: 1.0, color: "#00b4d8", pduOffsets: [-18, 0, 18], pduBg: this.pduColors.embb },
            { name: "URLLC", y: 185, speedMultiplier: 1.5, color: "#ff006e", pduOffsets: [-18, 0, 18], pduBg: this.pduColors.urllc },
            { name: "mMTC", y: 305, speedMultiplier: 0.6, color: "#39ff14", pduOffsets: [-18, 0, 18], pduBg: this.pduColors.mmtc }
        ];

        this.frameCounter = 0;
        this.nextId = 100;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.animate();
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = 400;
    }

    setMode(newMode) {
        if (newMode === 'quarantine') {
            this.mode = 'quarantine';
            this.quarantineTimer = 120; // ~2 seconds at 60fps then auto-reset
        } else {
            this.mode = newMode;
            this.quarantineTimer = 0;
        }
    }

    spawnCars() {
        // eMBB
        if (Math.random() < 0.05) this.addCar(0, 'normal');
        // URLLC
        if (Math.random() < 0.03) this.addCar(1, 'normal');
        // mMTC
        if (this.mode === 'attack') {
            if (Math.random() < 0.35) this.addCar(2, 'zombie', Math.random() > 0.5 ? 1 : 2);
            if (Math.random() < 0.02) this.addCar(2, 'normal', 0);
        } else if (this.mode === 'quarantine') {
            // During quarantine, only spawn normal mMTC on PDU-0
            if (Math.random() < 0.03) this.addCar(2, 'normal', 0);
        } else {
            if (Math.random() < 0.04) this.addCar(2, 'normal');
        }
    }

    addCar(laneIndex, type, forcedSubLane = -1) {
        let speed = (Math.random() * 2 + 3) * this.lanes[laneIndex].speedMultiplier;
        if (this.mode === 'attack' && laneIndex === 1) speed *= 0.2;
        
        let subLaneIndex = forcedSubLane !== -1 ? forcedSubLane : Math.floor(Math.random() * 3);
        let id = this.nextId++;
        if (this.nextId > 999) this.nextId = 100;

        this.cars.push({
            id, x: -40,
            y: this.lanes[laneIndex].y + this.lanes[laneIndex].pduOffsets[subLaneIndex],
            lane: laneIndex, subLane: subLaneIndex,
            type, speed,
            width: type === 'zombie' ? 14 : 20,
            height: type === 'zombie' ? 14 : 10,
            color: type === 'zombie' ? '#ff3860' : this.lanes[laneIndex].color,
        });
    }

    createExplosion(x, y) {
        for (let i = 0; i < 10; i++) {
            this.particles.push({
                x, y,
                vx: (Math.random() - 0.5) * 10,
                vy: (Math.random() - 0.5) * 10,
                life: 35,
                color: '#ff3860'
            });
        }
    }

    update() {
        this.frameCounter++;
        this.spawnCars();

        // Quarantine countdown → auto-reset to normal
        if (this.mode === 'quarantine') {
            this.quarantineTimer--;
            if (this.quarantineTimer <= 0) {
                this.mode = 'normal';
            }
        }

        for (let i = this.cars.length - 1; i >= 0; i--) {
            let car = this.cars[i];
            
            // During quarantine: destroy all zombies
            if (this.mode === 'quarantine' && car.type === 'zombie') {
                this.createExplosion(car.x, car.y);
                this.cars.splice(i, 1);
                continue;
            }

            car.x += car.speed;
            
            // URLLC speed dynamics
            if (car.lane === 1) {
                if (this.mode === 'attack' && car.speed > 0.8) car.speed *= 0.96;
                if (this.mode !== 'attack' && car.speed < 3.5) car.speed += 0.08;
            }

            if (car.x > this.canvas.width + 50) {
                this.cars.splice(i, 1);
            }
        }

        // Particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            let p = this.particles[i];
            p.x += p.vx; p.y += p.vy;
            p.vx *= 0.95; p.vy *= 0.95;
            p.life--;
            if (p.life <= 0) this.particles.splice(i, 1);
        }
    }

    draw() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        ctx.clearRect(0, 0, w, h);

        // Background
        ctx.fillStyle = '#0a0c10';
        ctx.fillRect(0, 0, w, h);

        // Legend
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.font = '500 10px Inter';
        ctx.fillText("Each numbered car represents a PDU session tracked by its IP / SUPI identifier", 15, 16);

        // Draw lanes
        this.lanes.forEach((lane) => {
            // PDU sub-lane backgrounds with distinct colors
            lane.pduOffsets.forEach((offset, idx) => {
                const bgColor = lane.pduBg[idx];
                ctx.fillStyle = bgColor;
                ctx.fillRect(0, lane.y + offset - 8, w, 16);

                // PDU lane dotted divider
                ctx.strokeStyle = lane.color;
                ctx.globalAlpha = 0.12;
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 6]);
                ctx.beginPath();
                ctx.moveTo(60, lane.y + offset);
                ctx.lineTo(w, lane.y + offset);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.globalAlpha = 1;
                
                // PDU label
                ctx.fillStyle = lane.color;
                ctx.globalAlpha = 0.25;
                ctx.font = '500 8px JetBrains Mono';
                ctx.fillText(`PDU-${idx + 1}`, 8, lane.y + offset + 3);
                ctx.globalAlpha = 1;
            });

            // Slice name
            ctx.fillStyle = lane.color;
            ctx.globalAlpha = 0.6;
            ctx.font = '700 13px Inter';
            ctx.fillText(lane.name + " Slice", 15, lane.y - 28);
            ctx.globalAlpha = 1;

            // Status indicators
            if (lane.name === "URLLC") {
                ctx.font = '500 10px JetBrains Mono';
                if (this.mode === 'attack') {
                    ctx.fillStyle = '#ff3860';
                    ctx.fillText("⚠ LATENCY SPIKE (Cross-Slice Impact)", w - 260, lane.y - 28);
                } else {
                    ctx.fillStyle = '#23d160';
                    ctx.fillText("✓ Normal (Sub-1ms)", w - 160, lane.y - 28);
                }
            }
            if (lane.name === "mMTC") {
                ctx.font = '500 10px JetBrains Mono';
                if (this.mode === 'attack') {
                    ctx.fillStyle = '#ff3860';
                    ctx.fillText("⚠ ZOMBIE FLOOD ON PDU-2 & PDU-3", w - 250, lane.y - 28);
                } else if (this.mode === 'quarantine') {
                    ctx.fillStyle = '#23d160';
                    ctx.fillText("🛡 SMF ISOLATING ROGUE PDUs...", w - 230, lane.y - 28);
                }
            }

            // Separator between slices
            if (lane !== this.lanes[this.lanes.length - 1]) {
                const sepY = lane.y + lane.pduOffsets[2] + 22;
                ctx.strokeStyle = 'rgba(255,255,255,0.04)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(0, sepY);
                ctx.lineTo(w, sepY);
                ctx.stroke();
            }
        });

        // Quarantine shield glow on mMTC PDU-2 and PDU-3
        if (this.mode === 'quarantine') {
            const mmtc = this.lanes[2];
            const wallX = 70;
            [1, 2].forEach(idx => {
                const pduY = mmtc.y + mmtc.pduOffsets[idx];
                ctx.fillStyle = 'rgba(35, 209, 96, 0.15)';
                ctx.fillRect(wallX, pduY - 8, w - wallX, 16);
            });
            // Vertical wall line
            ctx.strokeStyle = '#23d160';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(wallX, mmtc.y + mmtc.pduOffsets[1] - 10);
            ctx.lineTo(wallX, mmtc.y + mmtc.pduOffsets[2] + 10);
            ctx.stroke();

            ctx.fillStyle = '#23d160';
            ctx.font = '700 10px Inter';
            ctx.fillText("SMF WALL", wallX - 2, mmtc.y + mmtc.pduOffsets[1] - 14);
        }

        // Draw Cars
        this.cars.forEach(car => {
            ctx.fillStyle = car.color;
            if (car.type === 'zombie') {
                ctx.beginPath();
                ctx.moveTo(car.x + car.width, car.y);
                ctx.lineTo(car.x, car.y - car.height / 2);
                ctx.lineTo(car.x, car.y + car.height / 2);
                ctx.fill();
            } else {
                const r = 3;
                ctx.beginPath();
                ctx.roundRect(car.x, car.y - car.height / 2, car.width, car.height, r);
                ctx.fill();
                // Headlight
                ctx.fillStyle = 'rgba(255,255,255,0.5)';
                ctx.fillRect(car.x + car.width - 2, car.y - car.height / 2 + 1, 2, car.height - 2);
            }
            // ID label
            ctx.fillStyle = 'rgba(255,255,255,0.6)';
            ctx.font = '500 7px JetBrains Mono';
            ctx.fillText(car.id, car.x + 2, car.y - car.height / 2 - 3);
        });

        // Explosion particles
        this.particles.forEach(p => {
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life / 35;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
        });

        // Attack overlay
        if (this.mode === 'attack') {
            const pulse = (Math.sin(this.frameCounter * 0.05) + 1) * 0.5;
            ctx.fillStyle = `rgba(255, 56, 96, ${pulse * 0.04})`;
            ctx.fillRect(0, 0, w, h);
        }
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

let hwySim;
window.addEventListener('load', () => {
    hwySim = new HighwaySimulator();
});
