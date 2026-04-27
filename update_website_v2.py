import re

def main():
    file_path = "website/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the document into blocks using the comment headers
    # We will find all headers
    pattern = r"(<!-- ========== [A-Z0-9 ()-]+ ========== -->)"
    parts = re.split(pattern, content)
    
    # parts[0] is the top of the file before the first block
    
    blocks = {}
    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        blocks[header] = body

    # New pipeline detection block
    pipeline_html = """
<section class="detection-section" id="detection" style="background-color: var(--bg-color); padding: 80px 0;">
    <div class="container">
        <div class="reveal" style="text-align: center; margin-bottom: 50px;">
            <span class="section-label">Defense Engine</span>
            <h2 class="section-title">SliceGuard Dual-Model Architecture</h2>
            <p class="section-subtitle" style="max-width: 700px; margin: 0 auto;">
                A multi-model machine learning pipeline integrated at the 5G Core. It extracts per-flow UPF telemetry and utilizes both supervised algorithms and unsupervised isolation forests to autonomously trigger the SMF.
            </p>
        </div>

        <div class="reveal">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 15px; position: relative;">
                <style>
                    .pipe-node { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px 25px; border-radius: 12px; width: 340px; text-align: center; z-index: 2; position: relative;}
                    .pipe-node i { font-size: 28px; margin-bottom: 12px; }
                    .pipe-node h4 { margin: 0 0 5px 0; color: #fff; font-size: 16px; font-family: 'JetBrains Mono', monospace;}
                    .pipe-node p { margin: 0; color: rgba(255,255,255,0.6); font-size: 13.5px; }
                    .pipe-connector-v { width: 4px; height: 40px; background: rgba(255,255,255,0.1); position: relative; overflow: hidden; }
                    @keyframes dataFlow { 0% { top: -10px; opacity:1;} 80% { top: 40px; opacity:0;} 100% { top: 40px; opacity:0;}}
                    .pipe-pulse { position: absolute; width: 10px; height: 10px; border-radius: 5px; background: var(--accent); left: -3px; animation: dataFlow 1.2s infinite ease-out; box-shadow: 0 0 10px var(--accent);}
                    .split-container { display: flex; gap: 40px; position: relative; padding: 20px 0;}
                    .split-line-top { position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 380px; height: 3px; background: rgba(255,255,255,0.1); }
                    .split-vert-top { position: absolute; top: 0; width: 3px; height: 20px; background: rgba(255,255,255,0.1); }
                    .split-line-bot { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 380px; height: 3px; background: rgba(255,255,255,0.1); }
                    .split-vert-bot { position: absolute; bottom: 0; width: 3px; height: 20px; background: rgba(255,255,255,0.1); }
                </style>

                <div class="pipe-node" style="border-top: 3px solid var(--accent);">
                    <i class="fas fa-satellite-dish" style="color: var(--accent);"></i>
                    <h4>UPF Data Plane</h4>
                    <p>Continuous Per-Flow Telemetry. Monitors PDU sessions deep inside the GTP-U Tunnels.</p>
                </div>

                <div class="pipe-connector-v"><div class="pipe-pulse"></div></div>

                <div class="pipe-node">
                    <i class="fas fa-filter" style="color: var(--warning);"></i>
                    <h4>Feature Engineering Engine</h4>
                    <p>Calculates QoS, Infrastructure, and Cross-Slice correlations across a 10-tick rolling window.</p>
                </div>

                <div class="pipe-connector-v"><div class="pipe-pulse" style="background:var(--warning); box-shadow: 0 0 10px var(--warning); animation-delay: 0.4s;"></div></div>

                <div class="split-container">
                    <div class="split-line-top"></div>
                    <div class="split-vert-top" style="left: 0;"></div>
                    <div class="split-vert-top" style="right: 0;"></div>
                    
                    <div class="pipe-node" style="border-left: 3px solid #00b4d8; width: 320px;">
                        <i class="fas fa-bolt" style="color: #00b4d8;"></i>
                        <h4>XGBoost Classifier</h4>
                        <p>Supervised. Extremely fast detection of known Resource Theft logic.</p>
                    </div>
                    <div class="pipe-node" style="border-left: 3px solid #7b61ff; width: 320px;">
                        <i class="fas fa-brain" style="color: #7b61ff;"></i>
                        <h4>Isolation Forest</h4>
                        <p>Unsupervised. Catches Zero-Day anomalies & stealthy Side-Channels.</p>
                    </div>

                    <div class="split-line-bot"></div>
                    <div class="split-vert-bot" style="left: 0;"></div>
                    <div class="split-vert-bot" style="right: 0;"></div>
                    <div class="split-vert-bot" style="left: 50%; height: 20px; background:transparent;"></div> 
                </div>

                <div class="pipe-connector-v"><div class="pipe-pulse" style="background:#ff3860; box-shadow: 0 0 10px #ff3860; animation-delay: 0.8s;"></div></div>

                <div class="pipe-node" style="border-bottom: 3px solid #23d160;">
                    <i class="fas fa-shield-halved" style="color: #23d160;"></i>
                    <h4>SMF Executive API</h4>
                    <p>Automated PDU Quarantine. Drops attacker IDs instantly while preserving innocent slice traffic.</p>
                </div>
            </div>
        </div>
    </div>
</section>
"""
    # Replace the old Detection block
    blocks["<!-- ========== DETECTION ========== -->"] = "\n" + pipeline_html + "\n"

    # Desired order:
    # NAVBAR, HERO, ABOUT, DEFENSE MECHANISM (THE HIGHWAY), DETECTION, ATTACK EXPLANATION, PROTOCOL COMPARISON, SIMULATOR, TEAM, FOOTER
    desired_order = [
        "<!-- ========== NAVBAR ========== -->",
        "<!-- ========== HERO ========== -->",
        "<!-- ========== ABOUT – WHAT IS NETWORK SLICING ========== -->",
        "<!-- ========== DEFENSE MECHANISM (THE HIGHWAY) ========== -->",
        "<!-- ========== DETECTION ========== -->",
        "<!-- ========== ATTACK EXPLANATION ========== -->",
        "<!-- ========== PROTOCOL COMPARISON ========== -->",
        "<!-- ========== SIMULATOR ========== -->",
        "<!-- ========== TEAM ========== -->",
        "<!-- ========== FOOTER ========== -->"
    ]

    new_content = parts[0] # Add doctype and head
    
    for section in desired_order:
        if section in blocks:
            new_content += section + blocks[section]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("Re-order Output Successful.")

if __name__ == "__main__":
    main()
