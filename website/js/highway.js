/**
 * Highway Analogy Animation v2 (Detailed PDU Lanes)
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
        
        // Main Slices (Lanes)
        // We will define inner PDU sub-lanes offset from the center
        this.lanes = [
            { name: "eMBB", y: 80, speedMultiplier: 1.0, color: "#00b4d8", pduOffsets: [-15, 0, 15] },
            { name: "URLLC", y: 180, speedMultiplier: 1.5, color: "#ff006e", pduOffsets: [-15, 0, 15] },
            { name: "mMTC", y: 280, speedMultiplier: 0.6, color: "#39ff14", pduOffsets: [-15, 0, 15] }
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
        this.mode = newMode;
        if (newMode === 'quarantine') {
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
            // Zombie flood ONLY on PDU sub-lanes 1 and 2
            if (Math.random() < 0.4) {
                let subLane = Math.random() > 0.5 ? 1 : 2;
                this.addCar(2, 'zombie', subLane);
            }
            // Normal cars keep flowing on PDU sub-lane 0
            if (Math.random() < 0.02) this.addCar(2, 'normal', 0);
        } else {
            // Normal mMTC flowing everywhere
            if (Math.random() < 0.04) this.addCar(2, 'normal');
        }
    }

    addCar(laneIndex, type, forcedSubLane = -1) {
        let speed = (Math.random() * 2 + 3) * this.lanes[laneIndex].speedMultiplier;
        
        // Simulating Resource Theft: URLLC slows down dramatically during attack
        if (this.mode === 'attack' && laneIndex === 1) speed *= 0.2; 
        
        // Choose sub-lane (PDU tunnel)
        let subLaneIndex = forcedSubLane !== -1 ? forcedSubLane : Math.floor(Math.random() * 3);
        let id = this.nextId++;
        if (this.nextId > 999) this.nextId = 100;

        this.cars.push({
            id: id,
            x: -40,
            y: this.lanes[laneIndex].y + this.lanes[laneIndex].pduOffsets[subLaneIndex],
            lane: laneIndex,
            subLane: subLaneIndex,
            type: type, 
            speed: speed,
            width: type === 'zombie' ? 14 : 20,
            height: type === 'zombie' ? 14 : 10,
            color: type === 'zombie' ? '#ff3860' : this.lanes[laneIndex].color,
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

        for (let i = this.cars.length - 1; i >= 0; i--) {
            let car = this.cars[i];
            
            // SMF Quarantine active: Destroy zombies on specific sub-lanes
             if (this.mode === 'quarantine' && car.lane === 2 && (car.subLane === 1 || car.subLane === 2)) {
                // If it hits the firewall line
                if (car.x > 140) { 
                    this.createExplosion(car.x, car.y);
                    this.cars.splice(i, 1);
                    continue;
                }
            }

            car.x += car.speed;
            
            if (car.lane === 1) {
                if (this.mode === 'attack' && car.speed > 1) car.speed *= 0.95; 
                if (this.mode !== 'attack' && car.speed < 3.5) car.speed += 0.1; 
            }

            if (car.x > this.canvas.width + 50) {
                this.cars.splice(i, 1);
            }
        }

        for (let i = this.particles.length-1; i>=0; i--) {
            let p = this.particles[i];
            p.x += p.vx; p.y += p.vy; p.life--;
            if(p.life <= 0) this.particles.splice(i, 1);
        }

        if (this.mode === 'quarantine') {
            let targetY = this.lanes[2].y + Math.max(...this.lanes[2].pduOffsets) + 10;
            let startY = this.lanes[2].y + this.lanes[2].pduOffsets[1] - 10;
            if (this.quarantineWallY < targetY) {
                if (this.quarantineWallY < startY) this.quarantineWallY = startY;
                this.quarantineWallY += 10;
            }
        } else {
            this.quarantineWallY = -100;
        }
    }

    draw() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        ctx.clearRect(0, 0, w, h);

        // Draw Legend for IDs
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.font = '600 11px Inter';
        ctx.fillText("Legend: Numeric IDs over cars visually represent the tracking of device IPs or SUPIs.", 20, 20);

        this.lanes.forEach((lane) => {
            // Highlight background
            ctx.fillStyle = 'rgba(255,255,255,0.02)';
            ctx.fillRect(0, lane.y - 40, w, 80);

            // Draw micro-lanes (PDU Sessions)
            lane.pduOffsets.forEach((offset, idx) => {
                ctx.strokeStyle = 'rgba(255,255,255,0.06)';
                ctx.lineWidth = 1;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(0, lane.y + offset);
                ctx.lineTo(w, lane.y + offset);
                ctx.stroke();
                ctx.setLineDash([]);
                
                // PDU label
                ctx.fillStyle = `rgba(255,255,255,0.15)`;
                ctx.font = '500 8px JetBrains Mono';
                ctx.fillText(`PDU-${idx+1}`, 10, lane.y + offset + 3);
            });
            
            ctx.fillStyle = `rgba(255,255,255,0.5)`;
            ctx.font = '700 14px Inter';
            ctx.fillText(lane.name + " Slice", 20, lane.y - 25);
            
            if (lane.name === "URLLC") {
                ctx.fillStyle = this.mode === 'attack' ? '#ff3860' : '#23d160';
                ctx.font = '500 11px JetBrains Mono';
                ctx.fillText(this.mode === 'attack' ? "LATENCY SPIKE! (Cross-Slice Impact)" : "Normal Latency (Sub-1ms)", w - 240, lane.y - 25);
            }
        });

        // Draw Quarantine Firewall
        if (this.mode === 'quarantine') {
            const wallX = 145;
            const startY = this.lanes[2].y + this.lanes[2].pduOffsets[1] - 8;
            
            // Only blocks PDU-2 and PDU-3! PDU-1 is untouched.
            const glow = ctx.createLinearGradient(wallX, startY, wallX+20, startY);
            glow.addColorStop(0, 'rgba(35, 209, 96, 0.8)');
            glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow;
            ctx.fillRect(wallX, startY, 40, 40);

            ctx.strokeStyle = '#23d160';
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(wallX, startY);
            ctx.lineTo(wallX, this.quarantineWallY);
            ctx.stroke();

            ctx.fillStyle = '#23d160';
            ctx.font = '700 12px Inter';
            ctx.fillText("SMF BLOCKS ONLY TARGET PDUs", wallX-90, startY - 10);
        }

        // Draw Cars
        this.cars.forEach(car => {
            ctx.fillStyle = car.color;
            if (car.type === 'zombie') {
                ctx.beginPath();
                ctx.moveTo(car.x + car.width, car.y);
                ctx.lineTo(car.x, car.y - car.height/2);
                ctx.lineTo(car.x, car.y + car.height/2);
                ctx.fill();
            } else {
                ctx.fillRect(car.x, car.y - car.height/2, car.width, car.height);
                ctx.fillStyle = 'rgba(255,255,255,0.6)';
                ctx.fillRect(car.x + car.width - 2, car.y - car.height/2, 2, car.height);
            }
            
            // Draw ID Text
            ctx.fillStyle = 'rgba(255,255,255,0.7)';
            ctx.font = '500 8px JetBrains Mono';
            ctx.fillText(car.id, car.x, car.y - 8);
        });

        this.particles.forEach(p => {
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life / 30;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI*2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        });
        
        if (this.mode === 'attack') {
            const pulse = (Math.sin(this.frameCounter * 0.05) + 1) * 0.5;
            ctx.fillStyle = `rgba(255, 56, 96, ${pulse * 0.05})`;
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
