"""
REX Web Interface - JARVIS-Style Holographic UI
"""
import json
import asyncio
from typing import Dict

from loguru import logger

try:
    from flask import Flask, render_template_string, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from config.settings import WEB_CONFIG


HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>R.E.X // Tactical AI Interface</title>
<style>
    :root {
        --jarvis-cyan: #00d4ff;
        --jarvis-cyan-dim: #00a0cc;
        --jarvis-blue: #0066ff;
        --jarvis-bg: #000814;
        --jarvis-panel: rgba(0, 30, 60, 0.35);
        --jarvis-border: rgba(0, 212, 255, 0.4);
        --jarvis-text: #a8e6ff;
        --jarvis-warning: #ffaa00;
        --jarvis-danger: #ff3860;
        --jarvis-success: #00ff9d;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    html, body {
        background: var(--jarvis-bg);
        color: var(--jarvis-text);
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        overflow: hidden;
        height: 100vh;
        cursor: crosshair;
    }

    /* === Animated Background Grid === */
    body::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(0, 212, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 212, 255, 0.04) 1px, transparent 1px);
        background-size: 40px 40px;
        z-index: 0;
        animation: gridPulse 8s ease-in-out infinite;
    }

    @keyframes gridPulse {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    /* === Scanning Line === */
    body::after {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--jarvis-cyan), transparent);
        box-shadow: 0 0 20px var(--jarvis-cyan);
        z-index: 100;
        animation: scanLine 4s linear infinite;
    }

    @keyframes scanLine {
        0% { transform: translateY(0); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateY(100vh); opacity: 0; }
    }

    /* === Boot Sequence === */
    #bootScreen {
        position: fixed;
        inset: 0;
        background: #000;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        color: var(--jarvis-cyan);
        font-family: 'Consolas', monospace;
        transition: opacity 1s;
    }

    #bootScreen.hidden { opacity: 0; pointer-events: none; }

    .boot-text {
        font-size: 14px;
        text-align: left;
        max-width: 600px;
        line-height: 1.8;
        text-shadow: 0 0 10px var(--jarvis-cyan);
    }

    .boot-text .line { opacity: 0; animation: bootLine 0.1s forwards; }

    @keyframes bootLine { to { opacity: 1; } }

    /* === Main Layout === */
    .jarvis-container {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: 280px 1fr 280px;
        grid-template-rows: 60px 1fr 180px;
        gap: 15px;
        padding: 15px;
        height: 100vh;
    }

    /* === Top Bar === */
    .top-bar {
        grid-column: 1 / -1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 25px;
        background: var(--jarvis-panel);
        border: 1px solid var(--jarvis-border);
        border-radius: 2px;
        backdrop-filter: blur(10px);
        position: relative;
    }

    .top-bar::before, .top-bar::after {
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        border: 2px solid var(--jarvis-cyan);
    }
    .top-bar::before { top: -2px; left: -2px; border-right: none; border-bottom: none; }
    .top-bar::after { top: -2px; right: -2px; border-left: none; border-bottom: none; }

    .logo {
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 4px;
        color: var(--jarvis-cyan);
        text-shadow: 0 0 15px var(--jarvis-cyan);
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .logo-hex {
        width: 30px;
        height: 30px;
        background: var(--jarvis-cyan);
        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-weight: 900;
        font-size: 14px;
        box-shadow: 0 0 20px var(--jarvis-cyan);
        animation: hexPulse 2s ease-in-out infinite;
    }

    @keyframes hexPulse {
        0%, 100% { box-shadow: 0 0 20px var(--jarvis-cyan); }
        50% { box-shadow: 0 0 35px var(--jarvis-cyan), 0 0 50px var(--jarvis-cyan); }
    }

    .status-group {
        display: flex;
        gap: 20px;
        font-size: 11px;
        letter-spacing: 1.5px;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--jarvis-success);
        box-shadow: 0 0 10px var(--jarvis-success);
        animation: blink 2s infinite;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .time-display {
        color: var(--jarvis-cyan);
        font-size: 13px;
        letter-spacing: 2px;
        text-shadow: 0 0 10px var(--jarvis-cyan);
    }

    /* === Side Panels === */
    .panel {
        background: var(--jarvis-panel);
        border: 1px solid var(--jarvis-border);
        backdrop-filter: blur(10px);
        padding: 15px;
        overflow-y: auto;
        position: relative;
    }

    .panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 30px; height: 2px;
        background: var(--jarvis-cyan);
        box-shadow: 0 0 10px var(--jarvis-cyan);
    }

    .panel-title {
        font-size: 10px;
        letter-spacing: 3px;
        color: var(--jarvis-cyan);
        text-transform: uppercase;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px dashed var(--jarvis-border);
        display: flex;
        justify-content: space-between;
    }

    .panel-title::after {
        content: '▮';
        animation: blink 1s infinite;
    }

    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        font-size: 11px;
        border-bottom: 1px dotted rgba(0, 212, 255, 0.15);
    }

    .stat-label { color: rgba(168, 230, 255, 0.6); letter-spacing: 1px; }
    .stat-value { color: var(--jarvis-cyan); font-weight: bold; }

    .skill-list {
        list-style: none;
        font-size: 11px;
    }

    .skill-list li {
        padding: 6px 0;
        padding-left: 15px;
        position: relative;
        color: rgba(168, 230, 255, 0.8);
        transition: all 0.2s;
    }

    .skill-list li::before {
        content: '▸';
        position: absolute;
        left: 0;
        color: var(--jarvis-cyan);
    }

    .skill-list li:hover {
        color: var(--jarvis-cyan);
        padding-left: 20px;
        text-shadow: 0 0 5px var(--jarvis-cyan);
    }

    /* === Center: JARVIS Orb === */
    .orb-container {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .jarvis-orb {
        position: relative;
        width: 400px;
        height: 400px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Rotating rings */
    .ring {
        position: absolute;
        border-radius: 50%;
        border: 1px solid var(--jarvis-cyan);
    }

    .ring-1 {
        width: 400px; height: 400px;
        border-style: dashed;
        border-color: rgba(0, 212, 255, 0.3);
        animation: rotate 30s linear infinite;
    }

    .ring-2 {
        width: 340px; height: 340px;
        border-width: 2px;
        border-top-color: var(--jarvis-cyan);
        border-right-color: transparent;
        border-bottom-color: transparent;
        border-left-color: var(--jarvis-cyan);
        animation: rotate 15s linear infinite reverse;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
    }

    .ring-3 {
        width: 280px; height: 280px;
        border-style: dotted;
        animation: rotate 20s linear infinite;
    }

    .ring-4 {
        width: 220px; height: 220px;
        border: 2px solid transparent;
        border-top: 2px solid var(--jarvis-cyan);
        animation: rotate 8s linear infinite;
    }

    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* Central Arc Reactor */
    .arc-reactor {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: radial-gradient(circle, 
            rgba(0, 212, 255, 0.9) 0%, 
            rgba(0, 150, 200, 0.6) 30%, 
            rgba(0, 50, 100, 0.3) 60%, 
            transparent 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        z-index: 5;
        cursor: pointer;
        transition: transform 0.3s;
        animation: reactorPulse 3s ease-in-out infinite;
    }

    .arc-reactor:hover { transform: scale(1.05); }

    .arc-reactor.active {
        animation: reactorActive 0.5s ease-in-out infinite;
    }

    @keyframes reactorPulse {
        0%, 100% { 
            box-shadow: 0 0 40px var(--jarvis-cyan), 
                        inset 0 0 30px rgba(0, 212, 255, 0.5);
        }
        50% { 
            box-shadow: 0 0 80px var(--jarvis-cyan), 
                        0 0 120px rgba(0, 212, 255, 0.4),
                        inset 0 0 50px rgba(0, 212, 255, 0.8);
        }
    }

    @keyframes reactorActive {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    .arc-reactor::before {
        content: '';
        position: absolute;
        width: 100px; height: 100px;
        border: 2px solid rgba(255, 255, 255, 0.6);
        border-radius: 50%;
    }

    .arc-reactor::after {
        content: 'R';
        font-size: 40px;
        font-weight: 900;
        color: #fff;
        text-shadow: 0 0 20px #fff;
        letter-spacing: 2px;
    }

    /* Floating data labels around orb */
    .data-label {
        position: absolute;
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--jarvis-cyan);
        padding: 3px 8px;
        border: 1px solid var(--jarvis-border);
        background: rgba(0, 30, 60, 0.5);
        text-transform: uppercase;
    }

    .data-label.tl { top: 20px; left: 20px; }
    .data-label.tr { top: 20px; right: 20px; }
    .data-label.bl { bottom: 20px; left: 20px; }
    .data-label.br { bottom: 20px; right: 20px; }

    /* Waveform canvas */
    #waveform {
        position: absolute;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 500px;
        height: 40px;
    }

    /* === Chat Panel (Bottom) === */
    .chat-panel {
        grid-column: 1 / -1;
        background: var(--jarvis-panel);
        border: 1px solid var(--jarvis-border);
        backdrop-filter: blur(10px);
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: hidden;
    }

    .chat-header {
        padding: 8px 20px;
        border-bottom: 1px solid var(--jarvis-border);
        font-size: 10px;
        letter-spacing: 3px;
        color: var(--jarvis-cyan);
        display: flex;
        justify-content: space-between;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 10px 20px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .chat-messages::-webkit-scrollbar { width: 4px; }
    .chat-messages::-webkit-scrollbar-track { background: transparent; }
    .chat-messages::-webkit-scrollbar-thumb { background: var(--jarvis-cyan); }

    .msg {
        display: flex;
        gap: 12px;
        font-size: 12px;
        line-height: 1.5;
        animation: msgSlide 0.4s ease-out;
        white-space: pre-wrap;
        word-break: break-word;
    }

    @keyframes msgSlide {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .msg-user .msg-prefix { color: var(--jarvis-warning); }
    .msg-rex .msg-prefix { color: var(--jarvis-cyan); text-shadow: 0 0 8px var(--jarvis-cyan); }
    .msg-error .msg-prefix { color: var(--jarvis-danger); }

    .msg-prefix {
        font-weight: bold;
        min-width: 80px;
        letter-spacing: 1px;
    }

    .msg-content {
        color: rgba(168, 230, 255, 0.9);
        flex: 1;
    }

    .chat-input-row {
        display: flex;
        gap: 10px;
        padding: 10px 20px;
        border-top: 1px solid var(--jarvis-border);
        background: rgba(0, 10, 25, 0.5);
    }

    .prompt-symbol {
        color: var(--jarvis-cyan);
        font-weight: bold;
        padding: 10px 0;
        text-shadow: 0 0 8px var(--jarvis-cyan);
    }

    .chat-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        color: var(--jarvis-text);
        font-family: inherit;
        font-size: 13px;
        letter-spacing: 1px;
        padding: 10px 0;
    }

    .chat-input::placeholder {
        color: rgba(168, 230, 255, 0.3);
        letter-spacing: 2px;
    }

    .btn-jarvis {
        background: transparent;
        border: 1px solid var(--jarvis-cyan);
        color: var(--jarvis-cyan);
        padding: 8px 20px;
        font-family: inherit;
        font-size: 11px;
        letter-spacing: 2px;
        cursor: pointer;
        text-transform: uppercase;
        transition: all 0.2s;
        clip-path: polygon(10% 0%, 100% 0%, 90% 100%, 0% 100%);
        padding-left: 25px;
        padding-right: 25px;
    }

    .btn-jarvis:hover {
        background: var(--jarvis-cyan);
        color: #000;
        box-shadow: 0 0 20px var(--jarvis-cyan);
    }

    .btn-mic {
        width: 40px;
        clip-path: none;
        padding: 0;
        font-size: 16px;
    }

    /* Typing indicator */
    .typing {
        display: none;
        padding: 0 20px 10px;
        font-size: 11px;
        color: var(--jarvis-cyan);
        letter-spacing: 2px;
    }

    .typing.active { display: block; }

    .typing span {
        animation: typeDot 1.4s infinite;
        display: inline-block;
    }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes typeDot {
        0%, 60%, 100% { opacity: 0.2; }
        30% { opacity: 1; }
    }

    /* Corner decorations */
    .corner {
        position: fixed;
        width: 40px;
        height: 40px;
        border: 2px solid var(--jarvis-cyan);
        z-index: 50;
        pointer-events: none;
    }
    .corner.tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
    .corner.tr { top: 10px; right: 10px; border-left: none; border-bottom: none; }
    .corner.bl { bottom: 10px; left: 10px; border-right: none; border-top: none; }
    .corner.br { bottom: 10px; right: 10px; border-left: none; border-top: none; }

    /* Responsive */
    @media (max-width: 1100px) {
        .jarvis-container {
            grid-template-columns: 1fr;
            grid-template-rows: 60px auto 1fr 180px;
        }
        .panel.left, .panel.right { display: none; }
        .jarvis-orb { width: 300px; height: 300px; }
        .ring-1 { width: 300px; height: 300px; }
        .ring-2 { width: 250px; height: 250px; }
        .ring-3 { width: 200px; height: 200px; }
        .ring-4 { width: 160px; height: 160px; }
        .arc-reactor { width: 120px; height: 120px; }
    }
</style>
</head>
<body>

<!-- Boot Sequence -->
<div id="bootScreen">
    <div class="boot-text" id="bootText"></div>
</div>

<!-- Corner decorations -->
<div class="corner tl"></div>
<div class="corner tr"></div>
<div class="corner bl"></div>
<div class="corner br"></div>

<div class="jarvis-container">

    <!-- Top Bar -->
    <div class="top-bar">
        <div class="logo">
            <div class="logo-hex">R</div>
            <span>R.E.X // TACTICAL AI</span>
        </div>
        <div class="status-group">
            <div class="status-item">
                <div class="status-dot"></div>
                <span>SYSTEM ONLINE</span>
            </div>
            <div class="status-item">
                <div class="status-dot" style="background: var(--jarvis-cyan); box-shadow: 0 0 10px var(--jarvis-cyan);"></div>
                <span>NEURAL LINK</span>
            </div>
            <div class="status-item">
                <div class="status-dot" style="background: var(--jarvis-success); box-shadow: 0 0 10px var(--jarvis-success);"></div>
                <span id="skillCount">SKILLS: 24</span>
            </div>
        </div>
        <div class="time-display" id="timeDisplay">--:--:--</div>
    </div>

    <!-- Left Panel: System Status -->
    <div class="panel left">
        <div class="panel-title"><span>SYSTEM STATUS</span></div>
        <div class="stat-row"><span class="stat-label">CPU</span><span class="stat-value" id="cpuVal">--</span></div>
        <div class="stat-row"><span class="stat-label">MEMORY</span><span class="stat-value" id="memVal">--</span></div>
        <div class="stat-row"><span class="stat-label">UPTIME</span><span class="stat-value" id="uptimeVal">--</span></div>
        <div class="stat-row"><span class="stat-label">SESSIONS</span><span class="stat-value">1</span></div>
        <div class="stat-row"><span class="stat-label">HEALTH</span><span class="stat-value" style="color: var(--jarvis-success);">100%</span></div>

        <div class="panel-title" style="margin-top: 20px;"><span>MEMORY CORE</span></div>
        <div class="stat-row"><span class="stat-label">EPISODIC</span><span class="stat-value" id="epiVal">0</span></div>
        <div class="stat-row"><span class="stat-label">SEMANTIC</span><span class="stat-value" id="semVal">0</span></div>
        <div class="stat-row"><span class="stat-label">KNOWLEDGE</span><span class="stat-value" id="kgVal">0</span></div>
    </div>

    <!-- Center: Orb + Chat is below -->
    <div class="orb-container">
        <div class="jarvis-orb">
            <div class="ring ring-1"></div>
            <div class="ring ring-2"></div>
            <div class="ring ring-3"></div>
            <div class="ring ring-4"></div>
            <div class="arc-reactor" id="arcReactor" title="Click to activate voice"></div>
            <div class="data-label tl">LAT 13.0827°N</div>
            <div class="data-label tr">SEC: ALPHA</div>
            <div class="data-label bl">FREQ: 2.4GHz</div>
            <div class="data-label br">v1.0.0</div>
        </div>
        <canvas id="waveform"></canvas>
    </div>

    <!-- Right Panel: Skills -->
    <div class="panel right">
        <div class="panel-title"><span>ACTIVE MODULES</span></div>
        <ul class="skill-list">
            <li>Neural NLP Core</li>
            <li>Voice Recognition</li>
            <li>Knowledge Graph</li>
            <li>Code Generation</li>
            <li>Financial Analysis</li>
            <li>Smart Home IoT</li>
            <li>Cyber Defense</li>
            <li>Ethical Hacking</li>
            <li>Web Intelligence</li>
            <li>Media Synthesis</li>
            <li>Self-Healing</li>
            <li>Self-Improvement</li>
        </ul>

        <div class="panel-title" style="margin-top: 20px;"><span>NETWORK</span></div>
        <div class="stat-row"><span class="stat-label">IN</span><span class="stat-value" id="netIn">0 KB/s</span></div>
        <div class="stat-row"><span class="stat-label">OUT</span><span class="stat-value" id="netOut">0 KB/s</span></div>
        <div class="stat-row"><span class="stat-label">PING</span><span class="stat-value" id="pingVal">-- ms</span></div>
    </div>

    <!-- Chat Panel -->
    <div class="chat-panel">
        <div class="chat-header">
            <span>◈ COMM TERMINAL // ENCRYPTED CHANNEL</span>
            <span id="intentDisplay">AWAITING INPUT</span>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="msg msg-rex">
                <span class="msg-prefix">[R.E.X]&gt;</span>
                <span class="msg-content">System initialized. All modules operational. How may I assist you, sir?</span>
            </div>
        </div>
        <div class="typing" id="typing">
            <span>PROCESSING</span><span>.</span><span>.</span><span>.</span>
        </div>
        <div class="chat-input-row">
            <span class="prompt-symbol">&gt;_</span>
            <input type="text" class="chat-input" id="userInput" 
                   placeholder="ENTER COMMAND..." autocomplete="off"
                   onkeypress="if(event.key==='Enter')sendMessage()">
            <button class="btn-jarvis btn-mic" onclick="startVoice()" title="Voice">🎤</button>
            <button class="btn-jarvis" onclick="sendMessage()">TRANSMIT</button>
        </div>
    </div>

</div>

<script>
// === Boot Sequence ===
const bootLines = [
    '> STARK INDUSTRIES SECURE OS v1.0.0',
    '> Initializing R.E.X Neural Core...',
    '> Loading NLP modules... [OK]',
    '> Calibrating voice synthesis... [OK]',
    '> Establishing knowledge graph... [OK]',
    '> Activating 24 skill modules... [OK]',
    '> Self-healing protocols: ARMED',
    '> Security guardrails: ENGAGED',
    '> Tactical AI online.',
    '> Welcome back, sir.'
];

const bootText = document.getElementById('bootText');
bootLines.forEach((line, i) => {
    setTimeout(() => {
        const div = document.createElement('div');
        div.className = 'line';
        div.textContent = line;
        div.style.animationDelay = '0s';
        bootText.appendChild(div);
        if (i === bootLines.length - 1) {
            setTimeout(() => {
                document.getElementById('bootScreen').classList.add('hidden');
            }, 800);
        }
    }, i * 250);
});

// === Clock ===
function updateTime() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    document.getElementById('timeDisplay').textContent = `${h}:${m}:${s}`;
}
setInterval(updateTime, 1000);
updateTime();

// === Simulated Stats (replace with real API if desired) ===
let uptime = 0;
setInterval(() => {
    uptime++;
    document.getElementById('cpuVal').textContent = (Math.random() * 20 + 10).toFixed(1) + '%';
    document.getElementById('memVal').textContent = (Math.random() * 30 + 20).toFixed(1) + '%';
    const mm = String(Math.floor(uptime / 60)).padStart(2, '0');
    const ss = String(uptime % 60).padStart(2, '0');
    document.getElementById('uptimeVal').textContent = `00:${mm}:${ss}`;
    document.getElementById('netIn').textContent = Math.floor(Math.random() * 500) + ' KB/s';
    document.getElementById('netOut').textContent = Math.floor(Math.random() * 200) + ' KB/s';
    document.getElementById('pingVal').textContent = Math.floor(Math.random() * 30 + 10) + ' ms';
}, 1500);

// Fetch real status periodically
async function fetchStatus() {
    try {
        const r = await fetch('/api/status');
        if (r.ok) {
            const s = await r.json();
            if (s.skills_loaded) document.getElementById('skillCount').textContent = 'SKILLS: ' + s.skills_loaded;
            if (s.memory_stats) {
                document.getElementById('epiVal').textContent = s.memory_stats.episodic_count || 0;
                document.getElementById('semVal').textContent = s.memory_stats.semantic_count || 0;
                document.getElementById('kgVal').textContent = s.memory_stats.knowledge_graph_nodes || 0;
            }
        }
    } catch(e) {}
}
setInterval(fetchStatus, 5000);
fetchStatus();

// === Waveform Visualizer ===
const canvas = document.getElementById('waveform');
const ctx = canvas.getContext('2d');
canvas.width = 500;
canvas.height = 40;
let wavePhase = 0;
let waveAmplitude = 5;
let targetAmplitude = 5;

function drawWave() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#00d4ff';
    ctx.beginPath();
    waveAmplitude += (targetAmplitude - waveAmplitude) * 0.1;
    for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + 
                  Math.sin((x * 0.02) + wavePhase) * waveAmplitude +
                  Math.sin((x * 0.05) + wavePhase * 1.5) * (waveAmplitude * 0.5);
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    wavePhase += 0.08;
    requestAnimationFrame(drawWave);
}
drawWave();

// === Chat Logic ===
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const typing = document.getElementById('typing');
const intentDisplay = document.getElementById('intentDisplay');
const arcReactor = document.getElementById('arcReactor');

function addMsg(prefix, content, type = 'rex') {
    const div = document.createElement('div');
    div.className = 'msg msg-' + type;
    const prefixText = type === 'user' ? '[YOU]> ' : type === 'error' ? '[ERR]> ' : '[R.E.X]> ';
    div.innerHTML = `<span class="msg-prefix">${prefixText}</span><span class="msg-content"></span>`;
    div.querySelector('.msg-content').textContent = content;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    
    addMsg('YOU', text, 'user');
    userInput.value = '';
    typing.classList.add('active');
    targetAmplitude = 15;
    intentDisplay.textContent = 'PROCESSING...';
    
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const data = await r.json();
        typing.classList.remove('active');
        targetAmplitude = 5;
        addMsg('REX', data.response || 'No response', data.error ? 'error' : 'rex');
        intentDisplay.textContent = 'INTENT: ' + (data.intent || 'GENERAL').toUpperCase();
    } catch (err) {
        typing.classList.remove('active');
        targetAmplitude = 5;
        addMsg('ERR', 'Connection failed: ' + err.message, 'error');
        intentDisplay.textContent = 'LINK ERROR';
    }
}

// === Voice Recognition ===
function startVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addMsg('ERR', 'Voice recognition unsupported in this browser.', 'error');
        return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = 'en-IN';
    rec.continuous = false;
    arcReactor.classList.add('active');
    targetAmplitude = 20;
    intentDisplay.textContent = 'LISTENING...';
    addMsg('SYS', 'Voice channel open. Speak now.', 'rex');
    
    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        userInput.value = text;
        arcReactor.classList.remove('active');
        sendMessage();
    };
    rec.onerror = () => {
        arcReactor.classList.remove('active');
        targetAmplitude = 5;
        intentDisplay.textContent = 'VOICE ERROR';
    };
    rec.onend = () => {
        arcReactor.classList.remove('active');
        targetAmplitude = 5;
    };
    rec.start();
}

// Click reactor to activate voice
arcReactor.addEventListener('click', startVoice);

// Focus input on load
setTimeout(() => userInput.focus(), bootLines.length * 250 + 1000);
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
        if engine:
            return jsonify(engine.get_status())
        return jsonify({"status": "standby"})
    
    return app


def run_web_server(engine=None):
    app = create_web_app(engine)
    if app:
        print(f"\n🛸 JARVIS Interface online: http://localhost:{WEB_CONFIG['port']}")
        app.run(
            host=WEB_CONFIG["host"],
            port=WEB_CONFIG["port"],
            debug=WEB_CONFIG["debug"],
            threaded=True
        )
