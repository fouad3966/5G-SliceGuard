/**
 * Highway Analogy Animation
 * 5G Slicing & SMF Quarantine Visualization
 */

class HighwaySimulator {
    constructor() {
        this.canvas = document.getElementById('highwayCanvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        // Mode: 'normal', 'attack', 'quarantine'
        this.mode = 'normal';
        this.cars = [];
        this.particles = [];
        this.quarantineWallY = -100;
        
        // Lanes: 0=eMBB, 1=URLLC, 2=mMTC
        this.lanes = [
            { name: "eMBB", y: 80, speedMultiplier: 1.0, color: "#00b4d8" },
            { name: "URLLC", y: 180, speedMultiplier: 1.5, color: "#ff006e" },
            { name: "mMTC", y: 280, speedMultiplier: 0.6, color: "#39ff14" }
        ];

        this.frameCounter = 0;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.animate();
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = 400; // Fixed height
    }

    setMode(newMode) {
        this.mode = newMode;
        if (newMode === 'quarantine') {
            // Drop the SMF wall animation
            this.quarantineWallY = 0;
        }
    }

    spawnCars() {
        // eMBB cars
        if (Math.random() < 0.05) this.addCar(0, 'normal');
        
        // URLLC cars
        if (Math.random() < 0.03) this.addCar(1, 'normal');
        
        // mMTC cars
        if (this.mode === 'attack') {
            // Zombie flood
            if (Math.random() < 0.4) this.addCar(2, 'zombie');
            if (Math.random() < 0.02) this.addCar(2, 'normal');
        } else {
            // Normal mMTC
            if (Math.random() < 0.04) this.addCar(2, 'normal');
        }
    }

    addCar(laneIndex, type) {
        let speed = (Math.random() * 2 + 3) * this.lanes[laneIndex].speedMultiplier;
        
        // Simulating Resource Theft: URLLC slows down dramatically during attack
        if (this.mode === 'attack' && laneIndex === 1) {
            speed *= 0.2; // Massive latency spike
        }
        
        this.cars.push({
            x: -40,
            y: this.lanes[laneIndex].y,
            lane: laneIndex,
            type: type, // 'normal', 'zombie'
            speed: speed,
            width: type === 'zombie' ? 12 : 20,
            height: type === 'zombie' ? 12 : 10,
            color: type === 'zombie' ? '#ff3860' : this.lanes[laneIndex].color,
            dead: false
        });
    }

    createExplosion(x, y) {
        for(let i=0; i<8; i++) {
            this.particles.push({
                x: x, y: y,
                vx: (Math.random() - 0.5) * 8,
                vy: (Math.random() - 0.5) * 8,
                life: 30,
                color: '#ff3860'
            });
        }
    }

    update() {
        this.frameCounter++;
        this.spawnCars();

        // Update cars
        for (let i = this.cars.length - 1; i >= 0; i--) {
            let car = this.cars[i];
            
            // SMF Quarantine active: Destroy zombies
            if (this.mode === 'quarantine' && car.type === 'zombie') {
                if (car.x > 100) { // SMF firewall line
                    this.createExplosion(car.x, car.y);
                    this.cars.splice(i, 1);
                    continue;
                }
            }

            car.x += car.speed;
            
            // Speed adjustments based on real-time mode changes
            if (car.lane === 1) {
                const targetSpeed = (this.mode === 'attack') ? car.speed * 0.2 : (car.speed > 2 ? car.speed : (Math.random() * 2 + 3)*1.5 );
                if (this.mode === 'attack' && car.speed > 1) car.speed *= 0.95; // decelerate
                if (this.mode !== 'attack' && car.speed < 3) car.speed += 0.1; // accelerate back
            }

            if (car.x > this.canvas.width + 50) {
                this.cars.splice(i, 1);
            }
        }

        // Update particles
        for (let i = this.particles.length-1; i>=0; i--) {
            let p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life--;
            if(p.life <= 0) this.particles.splice(i, 1);
        }

        // Update Wall
        if (this.mode === 'quarantine' && this.quarantineWallY < this.lanes[2].y - 20) {
            this.quarantineWallY += 10;
        } else if (this.mode !== 'quarantine') {
            this.quarantineWallY = -100;
        }
    }

    draw() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        ctx.clearRect(0, 0, w, h);

        // Draw Highway lanes
        this.lanes.forEach((lane, i) => {
            // Sub-background for lane
            ctx.fillStyle = 'rgba(255,255,255,0.02)';
            ctx.fillRect(0, lane.y - 30, w, 60);

            // Center dotted line
            ctx.strokeStyle = 'rgba(255,255,255,0.1)';
            ctx.lineWidth = 2;
            ctx.setLineDash([20, 20]);
            ctx.beginPath();
            ctx.moveTo(0, lane.y);
            ctx.lineTo(w, lane.y);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Lane Name
            ctx.fillStyle = `rgba(255,255,255,0.4)`;
            ctx.font = '700 14px Inter';
            ctx.fillText(lane.name + " PDU Sessions", 20, lane.y - 10);
            
            // Status text
            if (lane.name === "URLLC") {
                ctx.fillStyle = this.mode === 'attack' ? '#ff3860' : '#23d160';
                ctx.font = '500 11px JetBrains Mono';
                ctx.fillText(this.mode === 'attack' ? "LATENCY SPIKE! (Cross-Slice Impact)" : "Normal Latency (Sub-1ms)", 20, lane.y + 20);
            }
            if (lane.name === "mMTC" && this.mode !== 'normal') {
                ctx.fillStyle = this.mode === 'attack' ? '#ff3860' : '#23d160';
                ctx.font = '500 11px JetBrains Mono';
                ctx.fillText(this.mode === 'attack' ? "ROGUE DEVICE FLOOD (Zombies)" : "MALICIOUS FLOWS ISOLATED", 20, lane.y + 20);
            }
        });

        // Draw Quarantine Wall
        if (this.mode === 'quarantine') {
            const wallX = 110;
            // Draw forcefield over mMTC
            const glow = ctx.createLinearGradient(wallX, this.lanes[2].y-30, wallX+20, this.lanes[2].y-30);
            glow.addColorStop(0, 'rgba(35, 209, 96, 0.8)');
            glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow;
            ctx.fillRect(wallX, this.lanes[2].y-30, 40, 60);

            ctx.strokeStyle = '#23d160';
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(wallX, this.quarantineWallY);
            ctx.lineTo(wallX, this.lanes[2].y + 30);
            ctx.stroke();

            ctx.fillStyle = '#23d160';
            ctx.font = '700 12px Inter';
            ctx.fillText("SMF ISOLATION LINE", wallX-50, this.lanes[2].y - 35);
        }

        // Draw Cars
        this.cars.forEach(car => {
            ctx.fillStyle = car.color;
            if (car.type === 'zombie') {
                // Triangle for zombie
                ctx.beginPath();
                ctx.moveTo(car.x + car.width, car.y);
                ctx.lineTo(car.x, car.y - car.height/2);
                ctx.lineTo(car.x, car.y + car.height/2);
                ctx.fill();
            } else {
                ctx.fillRect(car.x, car.y - car.height/2, car.width, car.height);
                // Headlight
                ctx.fillStyle = 'rgba(255,255,255,0.6)';
                ctx.fillRect(car.x + car.width - 2, car.y - car.height/2, 2, car.height);
            }
        });

        // Draw Particles
        this.particles.forEach(p => {
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life / 30;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI*2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        });
        
        // Attack overlay glow
        if (this.mode === 'attack') {
            const pulse = (Math.sin(this.frameCounter * 0.05) + 1) * 0.5;
            ctx.fillStyle = `rgba(255, 56, 96, ${pulse * 0.05})`;
            ctx.fillRect(0, 0, w, h);
            
            ctx.fillStyle = '#ff3860';
            ctx.font = '700 16px Inter';
            ctx.textAlign = 'right';
            ctx.fillText("⚠️ ML IDS: RESOURCE CONTENTION DETECTED", w - 20, 30);
            ctx.textAlign = 'left';
        }

        if (this.mode === 'quarantine') {
            ctx.fillStyle = '#23d160';
            ctx.font = '700 16px Inter';
            ctx.textAlign = 'right';
            ctx.fillText("🛡️ AUTOMATED QUARANTINE ACTIVE", w - 20, 30);
            ctx.textAlign = 'left';
        }
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when loaded
let hwySim;
window.addEventListener('load', () => {
    hwySim = new HighwaySimulator();
});
