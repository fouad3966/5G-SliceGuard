import re

def main():
    file_path = "website/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # We will completely parse out the individual sections and reconstruct them.
    # The sections currently in the file are separated by <!-- ========== SECTION ========== -->
    pattern = r"(<!-- ========== [A-Z0-9 ()-]+ ========== -->)"
    parts = re.split(pattern, content)
    
    blocks = {}
    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        blocks[header] = body

    # Fix NAVBAR
    navbar_html = """
<nav class="navbar" id="navbar">
    <div class="container">
        <a href="#hero" class="nav-logo">
            <div class="logo-icon"><i class="fas fa-shield-halved"></i></div>
            <span>5G SliceGuard</span>
        </a>
        <ul class="nav-links" id="navLinks">
            <li><a href="#about">About</a></li>
            <li><a href="#attacks">Threats</a></li>
            <li><a href="#detection">Defense Pipeline</a></li>
            <li><a href="#comparison">Protocols</a></li>
            <li><a href="#simulator" class="nav-cta">Launch Demo</a></li>
        </ul>
        <button class="nav-hamburger" id="hamburger" aria-label="Menu">
            <span></span><span></span><span></span>
        </button>
    </div>
</nav>
"""
    blocks["<!-- ========== NAVBAR ========== -->"] = "\n" + navbar_html + "\n"

    # We are dropping the old DEFENSE MECHANISM (THE HIGHWAY) section
    if "<!-- ========== DEFENSE MECHANISM (THE HIGHWAY) ========== -->" in blocks:
        del blocks["<!-- ========== DEFENSE MECHANISM (THE HIGHWAY) ========== -->"]

    # Reconstruct the unified PIPELINE section, merging the markdown conceptual logic with the canvas
    pipeline_html = """
<section class="pipeline-timeline-section" id="detection" style="background-color: var(--bg-color); padding: 80px 0;">
    <div class="container">
        <div class="reveal" style="text-align: center; margin-bottom: 50px;">
            <span class="section-label">Defense Engine</span>
            <h2 class="section-title">End-to-End IDS Defense Pipeline</h2>
            <p class="section-subtitle" style="max-width: 800px; margin: 0 auto;">
                From uncovering core hypervisor vulnerabilities to executing targeted PDU quarantine via REST APIs, this is the exact flow of the dual-model architecture.
            </p>
        </div>

        <div class="reveal">
            <div style="display: flex; flex-direction: column; align-items: center; position: relative;">
                
                <style>
                    .pipe-node-v3 { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 20px 30px; border-radius: 12px; width: 500px; text-align: left; z-index: 2; position: relative; backdrop-filter: blur(10px); }
                    @media (max-width: 600px) { .pipe-node-v3 { width: 90%; } }
                    .pipe-node-v3 h4 { margin: 0 0 10px 0; color: #fff; font-size: 17px; font-family: 'JetBrains Mono', monospace; display:flex; align-items:center; gap:12px; }
                    .pipe-node-v3 p { margin: 0; color: rgba(255,255,255,0.7); font-size: 13.5px; line-height: 1.6; }
                    .pipe-conn-v3 { width: 4px; height: 45px; background: rgba(255,255,255,0.1); position: relative; overflow: hidden; }
                    .pipe-pulse-v3 { position: absolute; width: 10px; height: 10px; border-radius: 5px; background: var(--accent); left: -3px; animation: dataFlow 1.8s infinite linear; box-shadow: 0 0 12px var(--accent); }
                    @keyframes dataFlow { 0% { top: -10px; opacity:1;} 90% { top: 50px; opacity:0;} 100% { top: 50px; opacity:0;}}
                    .highway-mid-container { width: 100%; max-width: 850px; background: rgba(10,12,16,0.6); padding: 25px; border-radius: 16px; border: 1px solid rgba(35, 209, 96, 0.3); text-align: center; margin: 5px 0; box-shadow: 0 0 40px rgba(35, 209, 96, 0.05); }
                </style>

                <!-- 1. Vulnerability -->
                <div class="pipe-node-v3" style="border-top: 3px solid #ff3860;">
                    <h4><i class="fas fa-biohazard" style="color: #ff3860; font-size: 22px;"></i> The Core Vulnerability</h4>
                    <p>Network slices share physical Hypervisor hardware. Attackers exploit this by flooding a low-security slice (mMTC) to mathematically steal CPU/Memory from critical slices (URLLC), risking autonomous vehicle accidents or physical infrastructure failures.</p>
                </div>
                <div class="pipe-conn-v3"><div class="pipe-pulse-v3" style="background:#ff3860; box-shadow: 0 0 10px #ff3860; animation-delay: 0.1s;"></div></div>

                <!-- 2. UPF Telemetry -->
                <div class="pipe-node-v3" style="border-top: 3px solid var(--accent);">
                    <h4><i class="fas fa-satellite-dish" style="color: var(--accent); font-size: 22px;"></i> Flow-Level Monitoring (UPF)</h4>
                    <p>The IDS sits seamlessly at the 5G Core. It doesn't treat slices as opaque pipes. It performs <strong>flow-level extraction</strong> directly on the UPF, categorizing all traffic by individual <strong>PDU Sessions</strong> mapped to distinct IP or SUPI device IDs.</p>
                </div>
                <div class="pipe-conn-v3"><div class="pipe-pulse-v3" style="animation-delay: 0.4s;"></div></div>

                <!-- 3. Feature ML -->
                <div class="pipe-node-v3" style="border-top: 3px solid var(--warning);">
                    <h4><i class="fas fa-filter" style="color: var(--warning); font-size: 22px;"></i> Feature Engineering</h4>
                    <p>The engine monitors features (Volumetric, Infrastructure, QoS) over rolling time windows. Crucially, it calculates <strong>Cross-Slice Correlation</strong>: mathematically proving that when mMTC volumetric stats spike, URLLC QoS latency degrades simultaneously.</p>
                </div>
                <div class="pipe-conn-v3"><div class="pipe-pulse-v3" style="background:var(--warning); box-shadow: 0 0 10px var(--warning); animation-delay: 0.7s;"></div></div>

                <!-- 4. Dual Model -->
                <div class="pipe-node-v3" style="border-top: 3px solid #00b4d8;">
                    <h4><i class="fas fa-brain" style="color: #00b4d8; font-size: 22px;"></i> Dual-Model Machine Learning</h4>
                    <p><strong>XGBoost (Supervised):</strong> Instantly classifies known signatures like massive Resource Theft or Data Injections.<br><br><strong>Isolation Forest (Unsupervised):</strong> Mathematically acts as a safety-net to isolate zero-day anomalies and stealthy cache-timing Side-Channels.</p>
                </div>
                <div class="pipe-conn-v3"><div class="pipe-pulse-v3" style="background:#00b4d8; box-shadow: 0 0 10px #00b4d8; animation-delay: 1.0s;"></div></div>

                <!-- 5. REST API -->
                <div class="pipe-node-v3" style="border-bottom: 3px solid #23d160;">
                    <h4><i class="fas fa-code" style="color: #23d160; font-size: 22px;"></i> Automated Quarantine (REST APIs)</h4>
                    <p>The IDS acts as a <em>scalpel</em>. Instead of shutting down the whole mMTC slice, it identifies the exact corrupted PDU tracking IDs. It fires an urgent HTTP POST request (SBA API) commanding the <strong>SMF (Session Management Function)</strong> to forcefully drop exclusively those rogue PDU connections.</p>
                </div>

                <div class="pipe-conn-v3" style="height: 30px;"><div class="pipe-pulse-v3" style="background:#23d160; box-shadow: 0 0 10px #23d160; animation-delay: 1.3s;"></div></div>

                <!-- THE HIGHWAY CANVAS VISUALIZATION -->
                <div class="highway-mid-container">
                    <h5 style="color: #23d160; font-family: 'JetBrains Mono'; font-size: 14px; margin: 0 0 15px 0; align-items:center; justify-content:center; display:flex;"><i class="fas fa-vial" style="margin-right: 8px;"></i> LIVE VISUALIZATION: TARGETED PDU QUARANTINE</h5>
                    <div style="display:flex; flex-direction:column; gap:16px;">
                        <canvas id="highwayCanvas" style="width: 100%; height: 350px; background: #000; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);"></canvas>
                        <div class="highway-controls" style="display: flex; gap: 12px; justify-content: center;">
                            <button class="sim-btn" style="background: rgba(255,255,255,0.05); color:white; flex:1;" onclick="hwySim.setMode('normal')"><i class="fas fa-car-side"></i> Normal Traffic</button>
                            <button class="sim-btn danger" style="flex:1;" onclick="hwySim.setMode('attack')"><i class="fas fa-biohazard"></i> Inject Zombies</button>
                            <button class="sim-btn success" style="flex:1;" onclick="hwySim.setMode('quarantine')"><i class="fas fa-shield-halved"></i> API SMF Trigger</button>
                        </div>
                    </div>
                </div>

                <div class="pipe-conn-v3" style="height: 30px;"><div class="pipe-pulse-v3" style="background:#23d160; box-shadow: 0 0 10px #23d160; animation-delay: 1.6s;"></div></div>

                <!-- 6. Restoration -->
                <div class="pipe-node-v3" style="border-bottom: 3px solid var(--text-primary); margin-bottom: 20px;">
                    <h4><i class="fas fa-heart-pulse" style="color: var(--text-primary); font-size: 22px;"></i> System Restoration</h4>
                    <p>The malicious traffic physically drops before it reaches the core. The hypervisor CPU buffers drain automatically, and the critical slices instantly restore to standard sub-1ms communication latencies.</p>
                </div>

            </div>
        </div>
    </div>
</section>
"""
    blocks["<!-- ========== DETECTION ========== -->"] = "\n" + pipeline_html + "\n"

    # Let's enforce the order precisely as the user requested:
    desired_order = [
        "<!-- ========== NAVBAR ========== -->",
        "<!-- ========== HERO ========== -->",
        "<!-- ========== ABOUT – WHAT IS NETWORK SLICING ========== -->",
        "<!-- ========== DETECTION ========== -->",
        "<!-- ========== ATTACK EXPLANATION ========== -->",
        "<!-- ========== PROTOCOL COMPARISON ========== -->",
        "<!-- ========== SIMULATOR ========== -->",
        "<!-- ========== TEAM ========== -->",
        "<!-- ========== FOOTER ========== -->"
    ]

    new_content = parts[0]
    
    for section in desired_order:
        if section in blocks:
            new_content += section + blocks[section]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("V3 Timeline Output Successful.")

if __name__ == "__main__":
    main()
