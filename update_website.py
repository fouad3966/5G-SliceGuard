import re

def main():
    file_path = "website/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Navbar rewrite
    content = content.replace(
        '<li><a href="#architecture">Architecture</a></li>',
        '<li><a href="#highway">Defense Mechanism</a></li>'
    )

    # 2. Extract SIMULATOR
    # We use non-greedy matching to capture the whole simulator block up to the start of ATTACK EXPLANATION
    sim_match = re.search(r'(<!-- ========== SIMULATOR ========== -->.*?)<!-- ========== ATTACK EXPLANATION ========== -->', content, re.DOTALL)
    if not sim_match:
        print("Simulator block not found")
        return
    sim_block = sim_match.group(1)
    
    # Remove simulator block from original spot
    content = content.replace(sim_block, '')

    # 3. Extract ARCHITECTURE
    arch_match = re.search(r'(<!-- ========== ARCHITECTURE ========== -->.*?)</section>', content, re.DOTALL)
    if not arch_match:
        print("Architecture block not found")
        return
    arch_block = arch_match.group(1) + "</section>\n\n"

    # 4. Construct HIGHWAY block
    highway_block = """<!-- ========== DEFENSE MECHANISM (THE HIGHWAY) ========== -->
<section class="highway-section" id="highway" style="padding: 100px 0; background-color: var(--bg-alt);">
    <div class="container">
        <div class="reveal">
            <span class="section-label">Defense Mechanism</span>
            <h2 class="section-title">The "Highway" Analogy: How SliceGuard Operates</h2>
            <p class="section-subtitle">
                A 5G Network is a massive highway. Slices are dedicated lanes, and PDU Sessions are the individual cars. 
                Watch how our ML Engine identifies and quarantines rogue vehicles without shutting down the entire infrastructure.
            </p>
        </div>

        <div class="highway-interactive-wrapper reveal" style="display: flex; gap: 40px; margin-top: 40px; flex-wrap: wrap;">
            <!-- Left: Interactive Canvas -->
            <div class="highway-canvas-area" style="flex: 1.5; min-width: 400px; display:flex; flex-direction:column; gap:16px;">
                <canvas id="highwayCanvas" style="width: 100%; height: 400px; background: #0a0c10; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);"></canvas>
                <div class="highway-controls" style="display: flex; gap: 12px; justify-content: center;">
                    <button class="sim-btn" style="background: rgba(255,255,255,0.05); color:white; flex:1;" onclick="hwySim.setMode('normal')"><i class="fas fa-car-side"></i> Normal Traffic</button>
                    <button class="sim-btn danger" style="flex:1;" onclick="hwySim.setMode('attack')"><i class="fas fa-biohazard"></i> Inject Zombies</button>
                    <button class="sim-btn success" style="flex:1;" onclick="hwySim.setMode('quarantine')"><i class="fas fa-shield-halved"></i> SMF Quarantine</button>
                </div>
            </div>
            
            <!-- Right: The ML IDS Features -->
            <div class="highway-features" style="flex: 1; min-width: 300px; display: flex; flex-direction: column; gap: 20px;">
                <h4 style="margin-bottom: 5px; color: var(--text-primary); font-size: 1.1rem;"><i class="fas fa-microchip"></i> What the ML IDS is Monitoring</h4>
                
                <div class="feature-item" style="display:flex; gap:16px; align-items:flex-start;">
                    <div class="feat-icon" style="color: var(--accent); font-size: 1.4rem; padding-top:2px;"><i class="fas fa-network-wired"></i></div>
                    <div class="feat-text">
                        <strong style="display:block; color:#fff; font-size: 0.95rem; margin-bottom:4px;">1. Volumetric Features</strong>
                        <p style="color:var(--text-secondary); margin:0; font-size: 0.85rem; line-height:1.5;">Total bandwidth (Mbps) and Packet Rate (pps). Spots brute-force floods.</p>
                    </div>
                </div>
                
                <div class="feature-item" style="display:flex; gap:16px; align-items:flex-start;">
                    <div class="feat-icon" style="color: var(--embb-color); font-size: 1.4rem; padding-top:2px;"><i class="fas fa-server"></i></div>
                    <div class="feat-text">
                        <strong style="display:block; color:#fff; font-size: 0.95rem; margin-bottom:4px;">2. Infrastructure Status</strong>
                        <p style="color:var(--text-secondary); margin:0; font-size: 0.85rem; line-height:1.5;">CPU and Memory usage of the UPF virtual machines.</p>
                    </div>
                </div>

                <div class="feature-item" style="display:flex; gap:16px; align-items:flex-start;">
                    <div class="feat-icon" style="color: var(--urllc-color); font-size: 1.4rem; padding-top:2px;"><i class="fas fa-tower-broadcast"></i></div>
                    <div class="feat-text">
                        <strong style="display:block; color:#fff; font-size: 0.95rem; margin-bottom:4px;">3. QoS Degradation</strong>
                        <p style="color:var(--text-secondary); margin:0; font-size: 0.85rem; line-height:1.5;">Latency, Jitter, and Drops. Critical for ensuring URLLC slices don't crash.</p>
                    </div>
                </div>

                <div class="feature-item" style="display:flex; gap:16px; align-items:flex-start;">
                    <div class="feat-icon" style="color: var(--mmtc-color); font-size: 1.4rem; padding-top:2px;"><i class="fas fa-link"></i></div>
                    <div class="feat-text">
                        <strong style="display:block; color:#fff; font-size: 0.95rem; margin-bottom:4px;">4. Cross-Slice Correlation</strong>
                        <p style="color:var(--text-secondary); margin:0; font-size: 0.85rem; line-height:1.5;">Analyses a 10-second rolling correlation: if mMTC CPU spikes exactly when URLLC latency spikes, it proves a physical hypervisor attack.</p>
                    </div>
                </div>
                
                <div class="quarantine-box glass-card" style="margin-top: 10px; padding: 16px 20px; border-left: 3px solid var(--success);">
                    <h5 style="color: var(--success); margin-bottom: 8px; font-size: 0.9rem;"><i class="fas fa-bolt"></i> The Scalpel, Not The Shield</h5>
                    <p style="color: var(--text-secondary); margin:0; font-size: 0.82rem; line-height:1.6;">
                        When flagged, the ML doesn't shut down the whole mMTC lane. It commands the <strong>SMF (Session Management Function)</strong> to target only rogue <em>PDU Sessions</em>. 
                        The attacker is dropped, but innocent cars keep driving safely.
                    </p>
                </div>
            </div>
        </div>
    </div>
</section>

"""
    
    # 5. Swap Architecture for Highway
    content = content.replace(arch_block, highway_block)

    # 6. Insert Simulator back in at the end (before TEAM)
    insert_point = "<!-- ========== TEAM ========== -->"
    content = content.replace(insert_point, sim_block + "\n" + insert_point)

    # 7. Inject highway.js script tag
    content = content.replace('<script src="js/app.js"></script>', '<script src="js/app.js"></script>\n<script src="js/highway.js"></script>')

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("HTML Update Successful!")

if __name__ == "__main__":
    main()
