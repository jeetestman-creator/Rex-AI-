"""
REX Web Interface - Flask-based cross-platform UI
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


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦖 REX AI Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a0a0f 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, rgba(0,245,255,0.1), rgba(123,47,247,0.1));
            border-radius: 20px;
            border: 1px solid rgba(0,245,255,0.3);
            margin-bottom: 20px;
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #00f5ff, #7b2ff7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        
        .header p {
            color: #8888aa;
            font-size: 0.9em;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(18,18,26,0.8);
            border-radius: 20px;
            border: 1px solid #2a2a3a;
            margin-bottom: 20px;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px 20px;
            border-radius: 15px;
            max-width: 80%;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            background: linear-gradient(135deg, rgba(0,245,255,0.15), rgba(0,245,255,0.05));
            border: 1px solid rgba(0,245,255,0.3);
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .message.rex {
            background: linear-gradient(135deg, rgba(123,47,247,0.15), rgba(123,47,247,0.05));
            border: 1px solid rgba(123,47,247,0.3);
            border-bottom-left-radius: 5px;
        }
        
        .message .sender {
            font-weight: bold;
            font-size: 0.8em;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        
        .message.user .sender { color: #00f5ff; }
        .message.rex .sender { color: #7b2ff7; }
        
        .message .content {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
        }
        
        .input-area input {
            flex: 1;
            padding: 15px 25px;
            background: #1a1a2e;
            border: 2px solid #2a2a3a;
            border-radius: 30px;
            color: #e0e0e0;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-area input:focus {
            border-color: #00f5ff;
        }
        
        .input-area button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #00f5ff, #7b2ff7);
            border: none;
            border-radius: 30px;
            color: white;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.3s;
        }
        
        .input-area button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(0,245,255,0.3);
        }
        
        .voice-btn {
            width: 50px;
            height: 50px;
            border-radius: 50% !important;
            padding: 0 !important;
            font-size: 20px;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px;
            color: #8888aa;
        }
        
        .typing-indicator.active {
            display: block;
        }
        
        .typing-indicator span {
            animation: blink 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes blink {
            0%, 20% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
        
        .status-bar {
            text-align: center;
            padding: 10px;
            color: #8888aa;
            font-size: 0.8em;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header h1 { font-size: 1.8em; }
            .message { max-width: 90%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦖 REX AI Assistant</h1>
            <p>Advanced AI with 20L+ Skills | Multi-language | Cross-platform</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message rex">
                <div class="sender">🦖 REX</div>
                <div class="content">Hello! I'm REX, your advanced AI assistant. How can I help you today?

I can assist with:
• 💻 Code generation
• 📊 Investment analysis
• 🌤️ Weather
• 🏠 Smart home
• 🔒 Cybersecurity
• 📅 Scheduling
• And much more!</div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            🦖 REX is thinking<span>.</span><span>.</span><span>.</span>
        </div>
        
        <div class="input-area">
            <button class="voice-btn" onclick="startVoice()">🎤</button>
            <input type="text" id="userInput" placeholder="Type your message..." 
                   onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()">Send 🚀</button>
        </div>
        
        <div class="status-bar">
            REX v1.0 | Connected | Skills: Active
        </div>
    </div>
    
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const typingIndicator = document.getElementById('typingIndicator');
        
        function addMessage(sender, content, isUser = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user' : 'rex'}`;
            msgDiv.innerHTML = `
                <div class="sender">${isUser ? '👤 YOU' : '🦖 REX'}</div>
                <div class="content">${content}</div>
            `;
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;
            
            addMessage('user', text, true);
            userInput.value = '';
            
            typingIndicator.classList.add('active');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                
                const data = await response.json();
                typingIndicator.classList.remove('active');
                addMessage('rex', data.response || 'No response');
                
            } catch (error) {
                typingIndicator.classList.remove('active');
                addMessage('rex', 'Error: Could not connect to REX engine. Make sure the server is running.');
            }
        }
        
        function startVoice() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-IN';
                recognition.continuous = false;
                
                recognition.onresult = (event) => {
                    const text = event.results[0][0].transcript;
                    userInput.value = text;
                    sendMessage();
                };
                
                recognition.start();
            } else {
                alert('Speech recognition not supported in this browser.');
            }
        }
    </script>
</body>
</html>
"""


def create_web_app(engine=None):
    """Create Flask web application"""
    if not FLASK_AVAILABLE:
        logger.error("Flask is required for web UI")
        return None
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/chat', methods=['POST'])
    async def chat():
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
                return jsonify({"response": f"Error: {str(e)}", "error": True})
            finally:
                loop.close()
        else:
            return jsonify({
                "response": f"You said: '{message}' (Engine not connected)",
            })
    
    @app.route('/api/status', methods=['GET'])
    def status():
        if engine:
            return jsonify(engine.get_status())
        return jsonify({"status": "standby"})
    
    return app


def run_web_server(engine=None):
    """Run the web server"""
    app = create_web_app(engine)
    if app:
        app.run(
            host=WEB_CONFIG["host"],
            port=WEB_CONFIG["port"],
            debug=WEB_CONFIG["debug"]
        )
