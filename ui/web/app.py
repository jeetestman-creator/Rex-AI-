"""
REX Web Interface - Ultimate JARVIS 3D Holographic UI
"""
import json
import asyncio
import time
import platform
from typing import Dict

from loguru import logger

try:
    from flask import Flask, render_template_string, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
    START_TIME = time.time()
    prev_net = psutil.net_io_counters()
    prev_time = time.time()
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed. System telemetry will be simulated.")

from config.settings import WEB_CONFIG

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>R.E.X // J.A.R.V.I.S. Interface</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
    :root {
        --jarvis-cyan: #00f3ff;
        --jarvis-blue: #0066ff;
        --jarvis-gold: #ffaa00;
        --jarvis-bg: #020611;
        --panel-bg: rgba(0, 20, 40, 0.4);
        --border-glow: rgba(0, 243, 255, 0.6);
        --text-main: #a8e6ff;
        --text-dim: #4a7c99;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        background: var(--jarvis-bg);
        color: var(--text-main);
        font-family: 'Share Tech Mono', monospace;
        overflow: hidden;
        height: 100vh;
        width: 100vw;
    }

    /* 3D Canvas Background */
    #three-container {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        z-index: 0;
    }

    /* Cinematic Grid & Vignette */
    body::before {
        content: '';
        position: fixed;
        inset: 0;
        background: 
            radial-gradient(circle at 50% 50%, transparent 0%, rgba(2, 6, 17, 0.8) 100%),
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 40px 40px, 40px 40px;
        z-index: 1;
        pointer-events: none;
    }

    /* HUD Overlay */
    .hud {
        position: fixed;
        inset: 0;
        z-index: 10;
        display: grid;
        grid-template-areas: 
            "top top top"
            "left center right"
            "bottom bottom bottom";
        grid-template-columns: 320px 1fr 320px;
        grid-template-rows: 80px 1fr 280px;
        gap: 20px;
        padding: 20px;
        pointer-events: none;
    }

    .hud > * { pointer-events: auto; }

    /* Glassmorphism Panels */
    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-glow);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.1), inset 0 0 20px rgba(0, 243, 255, 0.05);
        position: relative;
        overflow: hidden;
    }

    .panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--jarvis-cyan), transparent);
    }

    .panel-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        letter-spacing: 3px;
        color: var(--jarvis-cyan);
        padding: 15px;
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        text-transform: uppercase;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .panel-title::after {
        content: '◉';
        color: var(--jarvis-gold);
        animation: blink 2s infinite;
    }

    /* Top Bar */
    .top-bar {
        grid-area: top;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 30px;
        background: var(--panel-bg);
        border-bottom: 1px solid var(--border-glow);
        backdrop-filter: blur(10px);
    }

    .logo {
        font-family: 'Orbitron', sans-serif;
        font-size: 28px;
        font-weight: 900;
        color: var(--jarvis-cyan);
        text-shadow: 0 0 15px var(--jarvis-cyan);
        letter-spacing: 5px;
    }

    .status-group {
        display: flex;
        gap: 30px;
        font-size: 12px;
        letter-spacing: 2px;
    }

    .status-item { display: flex; align-items: center; gap: 10px; }
    .status-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--jarvis-cyan);
        box-shadow: 0 0 10px var(--jarvis-cyan);
        animation: pulse 2s infinite;
    }

    /* Left Panel: Telemetry */
    .left-panel { grid-area: left; padding-bottom: 20px; }
    
    .metric {
        padding: 15px;
        border-bottom: 1px solid rgba(0, 243, 255, 0.1);
    }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        letter-spacing: 2px;
        margin-bottom: 8px;
        color: var(--text-dim);
    }
    
    .metric-val { color: var(--jarvis-cyan); font-weight: bold; font-size: 14px; }
    
    .bar-bg {
        height: 4px;
        background: rgba(0, 243, 255, 0.1);
        border-radius: 2px;
        overflow: hidden;
    }
    
    .bar-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--jarvis-blue), var(--jarvis-cyan));
        box-shadow: 0 0 10px var(--jarvis-cyan);
        transition: width 0.5s ease-out;
    }

    /* Right Panel: Radar & Memory */
    .right-panel { grid-area: right; display: flex; flex-direction: column; }
    
    .radar-container {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        padding: 20px;
    }
    
    .radar {
        width: 200px; height: 200px;
        border-radius: 50%;
        border: 1px solid var(--border-glow);
        position: relative;
        background: radial-gradient(circle, rgba(0,243,255,0.05) 0%, transparent 70%);
    }
    
    .radar::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: conic-gradient(from 0deg, transparent 0deg, rgba(0,243,255,0.4) 45deg, transparent 90deg);
        animation: sweep 3s linear infinite;
    }
    
    .radar-ring {
        position: absolute;
        border: 1px solid rgba(0,243,255,0.3);
        border-radius: 50%;
    }
    .radar-ring.r1 { inset: 25%; }
    .radar-ring.r2 { inset: 50%; }
    .radar-cross {
        position: absolute; inset: 0;
        background: linear-gradient(transparent 49.5%, rgba(0,243,255,0.3) 49.5%, rgba(0,243,255,0.3) 50.5%, transparent 50.5%),
                    linear-gradient(90deg, transparent 49.5%, rgba(0,243,255,0.3) 49.5%, rgba(0,243,255,0.3) 50.5%, transparent 50.5%);
    }

    /* Center: Empty for 3D Core to show through */
    .center-area { grid-area: center; pointer-events: none; }

    /* Bottom: Chat Terminal */
    .chat-terminal {
        grid-area: bottom;
        display: flex;
        flex-direction: column;
        border-top: 2px solid var(--jarvis-cyan);
    }

    .chat-header {
        padding: 10px 20px;
        background: rgba(0, 243, 255, 0.05);
        font-family: 'Orbitron', sans-serif;
        font-size: 11px;
        letter-spacing: 3px;
        display: flex;
        justify-content: space-between;
        color: var(--jarvis-cyan);
    }

    .chat-log {
        flex: 1;
        overflow-y: auto;
        padding: 15px 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        font-size: 14px;
        line-height: 1.6;
    }

    .chat-log::-webkit-scrollbar { width: 4px; }
    .chat-log::-webkit-scrollbar-thumb { background: var(--jarvis-cyan); }

    .msg { display: flex; gap: 15px; animation: slideUp 0.4s ease-out; }
    .msg-user .prefix { color: var(--jarvis-gold); }
    .msg-rex .prefix { color: var(--jarvis-cyan); text-shadow: 0 0 8px var(--jarvis-cyan); }
    .msg-error .prefix { color: #ff3860; }
    .prefix { font-weight: bold; min-width: 80px; }
    .content { color: rgba(255,255,255,0.9); white-space: pre-wrap; word-break: break-word; }

    .input-row {
        display: flex;
        padding: 15px 20px;
        background: rgba(0, 0, 0, 0.4);
        border-top: 1px solid rgba(0, 243, 255, 0.2);
        gap: 15px;
    }

    .prompt { color: var(--jarvis-cyan); font-weight: bold; font-size: 18px; }

    .chat-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        color: #fff;
        font-family: inherit;
        font-size: 16px;
        letter-spacing: 1px;
    }

    .btn-jarvis {
        background: transparent;
        border: 1px solid var(--jarvis-cyan);
        color: var(--jarvis-cyan);
        padding: 8px 25px;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        letter-spacing: 2px;
        cursor: pointer;
        text-transform: uppercase;
        transition: all 0.3s;
        clip-path: polygon(10% 0%, 100% 0%, 90% 100%, 0% 100%);
    }

    .btn-jarvis:hover {
        background: var(--jarvis-cyan);
        color: #000;
        box-shadow: 0 0 20px var(--jarvis-cyan);
    }

    /* Animations */
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    @keyframes sweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

    /* Responsive */
    @media (max-width: 1100px) {
        .hud { grid-template-columns: 1fr; grid-template-rows: 60px 1fr 250px; }
        .left-panel, .right-panel { display: none; }
    }
</style>
</head>
<body>

<div id="three-container"></div>

<div class="hud">
    <!-- Top Bar -->
    <div class="top-bar">
        <div class="logo">R.E.X</div>
        <div class="status-group">
            <div class="status-item"><div class="status-dot"></div> NEURAL LINK</div>
            <div class="status-item"><div class="status-dot" style="background: var(--jarvis-gold); box-shadow: 0 0 10px var(--jarvis-gold);"></div> <span id="skill-count">24</span> MODULES</div>
            <div class="status-item" id="clock">00:00:00</div>
        </div>
    </div>

    <!-- Left Panel: Telemetry -->
    <div class="panel left-panel">
        <div class="panel-title"><span>Hardware Telemetry</span></div>
        
        <div class="metric">
            <div class="metric-header"><span>CPU LOAD</span><span class="metric-val" id="cpu-val">--%</span></div>
            <div class="bar-bg"><div class="bar-fill" id="cpu-bar" style="width: 0%"></div></div>
        </div>
        
        <div class="metric">
            <div class="metric-header"><span>MEMORY ALLOCATION</span><span class="metric-val" id="ram-val">--%</span></div>
            <div class="bar-bg"><div class="bar-fill" id="ram-bar" style="width: 0%"></div></div>
        </div>

        <div class="metric">
            <div class="metric-header"><span>DISK I/O</span><span class="metric-val" id="disk-val">--%</span></div>
            <div class="bar-bg"><div class="bar-fill" id="disk-bar" style="width: 0%"></div></div>
        </div>

        <div class="metric">
            <div class="metric-header"><span>UPLINK (DOWN)</span><span class="metric-val" id="net-down">-- KB/s</span></div>
            <div class="metric-header" style="margin-top:10px;"><span>UPLINK (UP)</span><span class="metric-val" id="net-up">-- KB/s</span></div>
        </div>

        <div class="metric">
            <div class="metric-header"><span>SYSTEM UPTIME</span><span class="metric-val" id="uptime">00:00:00</span></div>
        </div>
    </div>

    <!-- Center (Empty for 3D) -->
    <div class="center-area"></div>

    <!-- Right Panel: Radar -->
    <div class="panel right-panel">
        <div class="panel-title"><span>Neural Network Scan</span></div>
        <div class="radar-container">
            <div class="radar">
                <div class="radar-ring r1"></div>
                <div class="radar-ring r2"></div>
                <div class="radar-cross"></div>
            </div>
        </div>
        <div class="panel-title" style="border-top: 1px solid rgba(0,243,255,0.2); border-bottom: none;"><span>Memory Nodes</span></div>
        <div style="padding: 15px; font-size: 12px; color: var(--text-dim);">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span>Episodic</span><span id="mem-epi" style="color:var(--jarvis-cyan)">0</span></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span>Semantic</span><span id="mem-sem" style="color:var(--jarvis-cyan)">0</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Knowledge Graph</span><span id="mem-kg" style="color:var(--jarvis-cyan)">0</span></div>
        </div>
    </div>

    <!-- Bottom Chat Terminal -->
    <div class="panel chat-terminal">
        <div class="chat-header">
            <span>◈ SECURE COMM TERMINAL</span>
            <span id="intent-display">AWAITING INPUT</span>
        </div>
        <div class="chat-log" id="chat-log">
            <div class="msg msg-rex">
                <span class="prefix">[R.E.X]</span>
                <span class="content">System initialized. 3D Holographic Interface online. How may I assist you, sir?</span>
            </div>
        </div>
        <div class="input-row">
            <span class="prompt">&gt;_</span>
            <input type="text" class="chat-input" id="user-input" placeholder="ENTER COMMAND..." autocomplete="off" onkeypress="if(event.key==='Enter')sendMessage()">
            <button class="btn-jarvis" onclick="startVoice()">🎤 VOICE</button>
            <button class="btn-jarvis" onclick="sendMessage()">TRANSMIT</button>
        </div>
    </div>
</div>

<script>
    // === THREE.JS 3D HOLOGRAPHIC CORE ===
    let scene, camera, renderer, core, ring1, ring2, ring3;
    let targetScale = 1;
    let targetColor = new THREE.Color(0x00f3ff);
    let material;

    function initThree() {
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.getElementById('three-container').appendChild(renderer.domElement);

        // Particle Core
        const particles = 3000;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particles * 3);
        for(let i=0; i<particles; i++) {
            const r = 4 * Math.cbrt(Math.random()); 
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            positions[i*3] = r * Math.sin(phi) * Math.cos(theta);
            positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i*3+2] = r * Math.cos(phi);
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        material = new THREE.PointsMaterial({ color: 0x00f3ff, size: 0.06, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending });
        core = new THREE.Points(geometry, material);
        scene.add(core);

        // Orbital Rings
        const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.4, side: THREE.DoubleSide });
        ring1 = new THREE.Mesh(new THREE.TorusGeometry(6, 0.03, 16, 100), ringMat);
        ring1.rotation.x = Math.PI / 2;
        scene.add(ring1);

        ring2 = new THREE.Mesh(new THREE.TorusGeometry(7.5, 0.05, 16, 100), new THREE.MeshBasicMaterial({color: 0x0088ff, transparent: true, opacity: 0.3}));
        ring2.rotation.x = Math.PI / 3;
        scene.add(ring2);

        ring3 = new THREE.Mesh(new THREE.TorusGeometry(9, 0.02, 16, 100), new THREE.MeshBasicMaterial({color: 0x00ffff, transparent: true, opacity: 0.5}));
        ring3.rotation.y = Math.PI / 4;
        scene.add(ring3);

        camera.position.z = 14;
        animate();
    }

    function animate() {
        requestAnimationFrame(animate);
        core.rotation.y += 0.002;
        core.rotation.x += 0.001;
        ring1.rotation.z += 0.005;
        ring2.rotation.z -= 0.003;
        ring2.rotation.x += 0.002;
        ring3.rotation.y += 0.004;

        // Smooth transitions for reactivity
        core.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.05);
        material.color.lerp(targetColor, 0.05);

        renderer.render(scene, camera);
    }

    function setProcessingState(isProcessing) {
        if(isProcessing) {
            targetScale = 1.6;
            targetColor.setHex(0xffaa00); // Gold when thinking
        } else {
            targetScale = 1.0;
            targetColor.setHex(0x00f3ff); // Cyan when idle
        }
    }

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    initThree();

    // === LIVE TELEMETRY & CLOCK ===
    function updateClock() {
        const now = new Date();
        document.getElementById('clock').innerText = now.toTimeString().split(' ')[0];
    }
    setInterval(updateClock, 1000);
    updateClock();

    async function fetchTelemetry() {
        try {
            const res = await fetch('/api/status');
            const d = await res.json();
            
            document.getElementById('cpu-val').innerText = d.cpu + '%';
            document.getElementById('cpu-bar').style.width = d.cpu + '%';
            
            document.getElementById('ram-val').innerText = d.ram + '%';
            document.getElementById('ram-bar').style.width = d.ram + '%';
            
            document.getElementById('disk-val').innerText = d.disk + '%';
            document.getElementById('disk-bar').style.width = d.disk + '%';
            
            document.getElementById('net-down').innerText = d.net_down + ' KB/s';
            document.getElementById('net-up').innerText = d.net_up + ' KB/s';
            
            const h = String(Math.floor(d.uptime / 3600)).padStart(2, '0');
            const m = String(Math.floor((d.uptime % 3600) / 60)).padStart(2, '0');
            const s = String(d.uptime % 60).padStart(2, '0');
            document.getElementById('uptime').innerText = `${h}:${m}:${s}`;
            
            if(d.skills_loaded) document.getElementById('skill-count').innerText = d.skills_loaded;
            if(d.memory_stats) {
                document.getElementById('mem-epi').innerText = d.memory_stats.episodic_count || 0;
                document.getElementById('mem-sem').innerText = d.memory_stats.semantic_count || 0;
                document.getElementById('mem-kg').innerText = d.memory_stats.knowledge_graph_nodes || 0;
            }
        } catch(e) {}
    }
    setInterval(fetchTelemetry, 1500);
    fetchTelemetry();

    // === CHAT LOGIC ===
    const chatLog = document.getElementById('chat-log');
    const userInput = document.getElementById('user-input');
    const intentDisplay = document.getElementById('intent-display');

    function addMsg(prefix, content, type = 'rex') {
        const div = document.createElement('div');
        div.className = 'msg msg-' + type;
        div.innerHTML = `<span class="prefix">[${prefix}]</span><span class="content"></span>`;
        div.querySelector('.content').textContent = content;
        chatLog.appendChild(div);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;
        
        addMsg('YOU', text, 'user');
        userInput.value = '';
        setProcessingState(true);
        intentDisplay.textContent = 'PROCESSING NEURAL PATHWAYS...';
        
        try {
            const r = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const data = await r.json();
            setProcessingState(false);
            addMsg('R.E.X', data.response || 'No response', data.error ? 'error' : 'rex');
            intentDisplay.textContent = 'INTENT: ' + (data.intent || 'GENERAL').toUpperCase();
        } catch (err) {
            setProcessingState(false);
            addMsg('ERR', 'Uplink failed: ' + err.message, 'error');
            intentDisplay.textContent = 'LINK ERROR';
        }
    }

    // === VOICE RECOGNITION ===
    function startVoice() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            addMsg('ERR', 'Voice hardware unsupported.', 'error'); return;
        }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SR();
        rec.lang = 'en-IN';
        rec.continuous = false;
        setProcessingState(true);
        intentDisplay.textContent = 'AUDIO RECEPTORS ACTIVE...';
        addMsg('SYS', 'Listening...', 'rex');
        
        rec.onresult = (e) => {
            userInput.value = e.results[0][0].transcript;
            setProcessingState(false);
            sendMessage();
        };
        rec.onerror = () => { setProcessingState(false); intentDisplay.textContent = 'AUDIO ERROR'; };
        rec.onend = () => { setProcessingState(false); };
        rec.start();
    }

    setTimeout(() => userInput.focus(), 500);
</script>
</body>
</html>
"""

def create_web_app(engine=None):
    if not FLASK_AVAILABLE:
        logger.error("Flask is required for web UI")
        return None
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.json
        message = data.get('message', '')
        
        if engine:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(engine.process(message))
                return jsonify({
                    "response": result.get("text", ""),
                    "intent": result.get("intent", ""),
                    "data": result.get("data", {}),
                })
            except Exception as e:
                logger.error(f"Web chat error: {e}")
                return jsonify({"response": f"Error: {str(e)}", "error": True})
            finally:
                loop.close()
        else:
            return jsonify({"response": f"Echo: {message}"})
    
    @app.route('/api/status', methods=['GET'])
    def status():
        global prev_net, prev_time
        
        stats = {"cpu": 0, "ram": 0, "disk": 0, "net_down": 0, "net_up": 0, "uptime": 0}
        
        if PSUTIL_AVAILABLE:
            current_net = psutil.net_io_counters()
            dt = time.time() - prev_time
            if dt > 0:
                stats["net_down"] = round((current_net.bytes_recv - prev_net.bytes_recv) / dt / 1024, 1)
                stats["net_up"] = round((current_net.bytes_sent - prev_net.bytes_sent) / dt / 1024, 1)
            prev_net = current_net
            prev_time = time.time()
            
            stats["cpu"] = psutil.cpu_percent(interval=0.1)
            stats["ram"] = psutil.virtual_memory().percent
            stats["disk"] = psutil.disk_usage('/').percent
            stats["uptime"] = int(time.time() - START_TIME)
            
        if engine:
            stats.update(engine.get_status())
            
        return jsonify(stats)
    
    return app

def run_web_server(engine=None):
    app = create_web_app(engine)
    if app:
        print(f"\n🛸 J.A.R.V.I.S. 3D Interface online: http://localhost:{WEB_CONFIG['port']}")
        app.run(
            host=WEB_CONFIG["host"],
            port=WEB_CONFIG["port"],
            debug=WEB_CONFIG["debug"],
            threaded=True
        )
