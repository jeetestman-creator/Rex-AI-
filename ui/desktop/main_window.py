"""
REX Desktop UI - PyQt5 Main Window
"""
import sys
from typing import Optional
from datetime import datetime

from loguru import logger

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QTextEdit, QLineEdit, QScrollArea,
        QFrame, QSplitter, QTabWidget, QGroupBox, QStatusBar,
        QMenuBar, QAction, QSystemTrayIcon, QMenu, QMessageBox,
        QComboBox, QSlider, QProgressBar, QGridLayout
    )
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
    from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    logger.warning("PyQt5 not available. Desktop UI disabled.")


if PYQT_AVAILABLE:
    
    class REXTheme:
        """REX Cyber Theme"""
        DARK_BG = "#0a0a0f"
        CARD_BG = "#12121a"
        PRIMARY = "#00f5ff"
        SECONDARY = "#7b2ff7"
        ACCENT = "#ff006e"
        TEXT = "#e0e0e0"
        TEXT_DIM = "#8888aa"
        SUCCESS = "#00ff88"
        WARNING = "#ffaa00"
        ERROR = "#ff3366"
        BORDER = "#2a2a3a"
        
        @staticmethod
        def get_stylesheet():
            return f"""
                QMainWindow {{
                    background-color: {REXTheme.DARK_BG};
                    color: {REXTheme.TEXT};
                }}
                QWidget {{
                    background-color: {REXTheme.CARD_BG};
                    color: {REXTheme.TEXT};
                    font-family: 'Segoe UI', 'Arial';
                }}
                QLabel {{
                    background: transparent;
                    color: {REXTheme.TEXT};
                }}
                QLineEdit {{
                    background-color: #1a1a2e;
                    border: 2px solid {REXTheme.BORDER};
                    border-radius: 25px;
                    padding: 12px 20px;
                    color: {REXTheme.TEXT};
                    font-size: 14px;
                }}
                QLineEdit:focus {{
                    border-color: {REXTheme.PRIMARY};
                }}
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {REXTheme.PRIMARY}, stop:1 {REXTheme.SECONDARY});
                    border: none;
                    border-radius: 25px;
                    padding: 12px 24px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {REXTheme.SECONDARY}, stop:1 {REXTheme.ACCENT});
                }}
                QPushButton:pressed {{
                    background: {REXTheme.ACCENT};
                }}
                QTextEdit {{
                    background-color: #0d0d15;
                    border: 1px solid {REXTheme.BORDER};
                    border-radius: 10px;
                    padding: 15px;
                    color: {REXTheme.TEXT};
                    font-size: 13px;
                    selection-background-color: {REXTheme.SECONDARY};
                }}
                QTabWidget::pane {{
                    border: 1px solid {REXTheme.BORDER};
                    border-radius: 10px;
                    background-color: {REXTheme.CARD_BG};
                }}
                QTabBar::tab {{
                    background-color: {REXTheme.CARD_BG};
                    color: {REXTheme.TEXT_DIM};
                    padding: 10px 20px;
                    border: 1px solid {REXTheme.BORDER};
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    margin-right: 2px;
                }}
                QTabBar::tab:selected {{
                    background-color: {REXTheme.DARK_BG};
                    color: {REXTheme.PRIMARY};
                    border-bottom: 2px solid {REXTheme.PRIMARY};
                }}
                QStatusBar {{
                    background-color: {REXTheme.DARK_BG};
                    color: {REXTheme.TEXT_DIM};
                    border-top: 1px solid {REXTheme.BORDER};
                }}
                QProgressBar {{
                    border: 1px solid {REXTheme.BORDER};
                    border-radius: 5px;
                    text-align: center;
                    background-color: {REXTheme.DARK_BG};
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {REXTheme.PRIMARY}, stop:1 {REXTheme.SECONDARY});
                    border-radius: 5px;
                }}
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
                QScrollBar:vertical {{
                    background: {REXTheme.DARK_BG};
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {REXTheme.BORDER};
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {REXTheme.PRIMARY};
                }}
                QComboBox {{
                    background-color: #1a1a2e;
                    border: 1px solid {REXTheme.BORDER};
                    border-radius: 8px;
                    padding: 8px 12px;
                    color: {REXTheme.TEXT};
                }}
            """
    
    
    class REXChatThread(QThread):
        """Background thread for processing AI responses"""
        response_ready = pyqtSignal(dict)
        
        def __init__(self, engine, user_input):
            super().__init__()
            self.engine = engine
            self.user_input = user_input
        
        def run(self):
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self.engine.process(self.user_input))
                self.response_ready.emit(result)
            except Exception as e:
                self.response_ready.emit({
                    "text": f"Error: {str(e)}",
                    "intent": "error",
                    "data": {},
                })
            finally:
                loop.close()
    
    
    class REXMainWindow(QMainWindow):
        """REX Main Desktop Window"""
        
        def __init__(self, engine=None):
            super().__init__()
            self.engine = engine
            self.chat_thread = None
            self.is_listening = False
            
            self.setWindowTitle("🦖 REX AI Assistant v1.0")
            self.setMinimumSize(1000, 700)
            self.resize(1200, 800)
            
            self.setStyleSheet(REXTheme.get_stylesheet())
            self._init_ui()
            self._init_status_bar()
            
            logger.info("🖥️ Desktop UI initialized")
        
        def _init_ui(self):
            """Initialize the user interface"""
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout(central)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Header
            header = self._create_header()
            main_layout.addWidget(header)
            
            # Main content with tabs
            self.tabs = QTabWidget()
            self.tabs.addTab(self._create_chat_tab(), "💬 Chat")
            self.tabs.addTab(self._create_skills_tab(), "🛠️ Skills")
            self.tabs.addTab(self._create_settings_tab(), "⚙️ Settings")
            self.tabs.addTab(self._create_status_tab(), "📊 Status")
            
            main_layout.addWidget(self.tabs)
        
        def _create_header(self) -> QWidget:
            """Create header with REX branding"""
            header = QFrame()
            header.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {REXTheme.DARK_BG}, stop:0.5 #1a0a2e, stop:1 {REXTheme.DARK_BG});
                    border-bottom: 2px solid {REXTheme.PRIMARY};
                }}
            """)
            header.setFixedHeight(70)
            
            layout = QHBoxLayout(header)
            
            # Logo and name
            logo_label = QLabel("🦖 REX")
            logo_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
            logo_label.setStyleSheet(f"color: {REXTheme.PRIMARY}; background: transparent;")
            layout.addWidget(logo_label)
            
            # Subtitle
            subtitle = QLabel("Advanced AI Assistant")
            subtitle.setStyleSheet(f"color: {REXTheme.TEXT_DIM}; font-size: 12px; background: transparent;")
            layout.addWidget(subtitle)
            
            layout.addStretch()
            
            # Voice button
            self.voice_btn = QPushButton("🎤 Voice")
            self.voice_btn.setFixedWidth(100)
            self.voice_btn.clicked.connect(self.toggle_voice)
            layout.addWidget(self.voice_btn)
            
            # Language selector
            self.lang_combo = QComboBox()
            self.lang_combo.addItems(["English", "தமிழ் (Tamil)", "हिंदी (Hindi)"])
            self.lang_combo.setFixedWidth(150)
            layout.addWidget(self.lang_combo)
            
            return header
        
        def _create_chat_tab(self) -> QWidget:
            """Create chat interface"""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Chat display
            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setFont(QFont("Segoe UI", 12))
            self._append_message("rex", "Hello! I'm REX, your advanced AI assistant. 🦖\n\nI can help you with:\n• 💻 Code generation & development\n• 📊 Investment analysis\n• 🌤️ Weather information\n• 🏠 Smart home control\n• 🔒 Cybersecurity\n• 📅 Calendar & scheduling\n• 🌐 Web search & scraping\n• And much more!\n\nHow can I help you today?")
            layout.addWidget(self.chat_display)
            
            # Input area
            input_layout = QHBoxLayout()
            
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("Type your message here... (Press Enter to send)")
            self.input_field.setFont(QFont("Segoe UI", 13))
            self.input_field.returnPressed.connect(self.send_message)
            input_layout.addWidget(self.input_field)
            
            send_btn = QPushButton("Send 🚀")
            send_btn.setFixedWidth(120)
            send_btn.clicked.connect(self.send_message)
            input_layout.addWidget(send_btn)
            
            layout.addLayout(input_layout)
            
            return widget
        
        def _create_skills_tab(self) -> QWidget:
            """Create skills browser"""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)
            
            title = QLabel("🛠️ Available Skills")
            title.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title.setStyleSheet(f"color: {REXTheme.PRIMARY};")
            layout.addWidget(title)
            
            # Skills grid
            skills_display = QTextEdit()
            skills_display.setReadOnly(True)
            
            if self.engine:
                skills_text = ""
                for name, info in self.engine.skill_registry.items():
                    desc = info.get("description", "No description") if isinstance(info, dict) else "Loaded"
                    skills_text += f"🔹 **{name}**: {desc}\n\n"
                skills_display.setText(skills_text or "Loading skills...")
            else:
                skills_display.setText("Engine not connected")
            
            layout.addWidget(skills_display)
            return widget
        
        def _create_settings_tab(self) -> QWidget:
            """Create settings panel"""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)
            
            title = QLabel("⚙️ Settings")
            title.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title.setStyleSheet(f"color: {REXTheme.PRIMARY};")
            layout.addWidget(title)
            
            # Voice settings
            voice_group = QGroupBox("Voice Settings")
            voice_layout = QGridLayout()
            
            voice_layout.addWidget(QLabel("Speech Rate:"), 0, 0)
            self.rate_slider = QSlider(Qt.Horizontal)
            self.rate_slider.setRange(100, 300)
            self.rate_slider.setValue(175)
            voice_layout.addWidget(self.rate_slider, 0, 1)
            
            voice_layout.addWidget(QLabel("Volume:"), 1, 0)
            self.volume_slider = QSlider(Qt.Horizontal)
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(100)
            voice_layout.addWidget(self.volume_slider, 1, 1)
            
            voice_group.setLayout(voice_layout)
            layout.addWidget(voice_group)
            
            # Theme settings
            theme_group = QGroupBox("Appearance")
            theme_layout = QVBoxLayout()
            theme_layout.addWidget(QLabel("Theme: Cyber Dark (Active)"))
            theme_group.setLayout(theme_layout)
            layout.addWidget(theme_group)
            
            layout.addStretch()
            return widget
        
        def _create_status_tab(self) -> QWidget:
            """Create system status panel"""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)
            
            title = QLabel("📊 System Status")
            title.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title.setStyleSheet(f"color: {REXTheme.PRIMARY};")
            layout.addWidget(title)
            
            self.status_display = QTextEdit()
            self.status_display.setReadOnly(True)
            self._update_status()
            layout.addWidget(self.status_display)
            
            # Refresh button
            refresh_btn = QPushButton("🔄 Refresh Status")
            refresh_btn.clicked.connect(self._update_status)
            layout.addWidget(refresh_btn)
            
            # Auto-refresh timer
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self._update_status)
            self.status_timer.start(30000)  # Every 30 seconds
            
            return widget
        
        def _init_status_bar(self):
            """Initialize status bar"""
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            self.status_bar.showMessage("🦖 REX Ready | Skills: Loading | Health: 100%")
        
        def _append_message(self, sender: str, text: str):
            """Append message to chat display"""
            if sender == "user":
                color = REXTheme.PRIMARY
                icon = "👤"
            else:
                color = REXTheme.SUCCESS
                icon = "🦖"
            
            html = f"""
            <div style='margin: 10px 0; padding: 12px; 
                        background-color: #1a1a2e; border-radius: 12px;
                        border-left: 4px solid {color};'>
                <span style='color: {color}; font-weight: bold;'>{icon} {sender.upper()}</span>
                <br><br>
                <span style='color: {REXTheme.TEXT};'>{text}</span>
            </div>
            """
            self.chat_display.append(html)
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
        
        def send_message(self):
            """Send user message"""
            text = self.input_field.text().strip()
            if not text:
                return
            
            self._append_message("user", text)
            self.input_field.clear()
            
            if self.engine:
                self._append_message("rex", "🤔 Thinking...")
                self.chat_thread = REXChatThread(self.engine, text)
                self.chat_thread.response_ready.connect(self._handle_response)
                self.chat_thread.start()
            else:
                self._append_message("rex", f"You said: '{text}'\n\n(Engine not connected - running in UI-only mode)")
        
        def _handle_response(self, response: dict):
            """Handle AI response"""
            text = response.get("text", "No response")
            intent = response.get("intent", "unknown")
            
            # Remove "Thinking..." message
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.End)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            
            self._append_message("rex", text)
            self.status_bar.showMessage(
                f"🦖 REX Active | Intent: {intent} | "
                f"Skills: {len(self.engine.skill_registry) if self.engine else 0}"
            )
        
        def toggle_voice(self):
            """Toggle voice input"""
            self.is_listening = not self.is_listening
            if self.is_listening:
                self.voice_btn.setText("🔴 Stop")
                self.voice_btn.setStyleSheet(f"background-color: {REXTheme.ERROR};")
                self.status_bar.showMessage("🎤 Listening... Speak now!")
            else:
                self.voice_btn.setText("🎤 Voice")
                self.voice_btn.setStyleSheet("")
                self.status_bar.showMessage("🦖 REX Ready")
        
        def _update_status(self):
            """Update status display"""
            import psutil
            
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status_text = f"""System Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

🖥️ SYSTEM:
  CPU Usage: {cpu}%
  Memory: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
  Disk: {disk.percent}% ({disk.free // (1024**3)}GB free)

🦖 REX ENGINE:
  Status: {'Running' if self.engine and self.engine.is_running else 'Standby'}
  Skills Loaded: {len(self.engine.skill_registry) if self.engine else 0}
  Health Score: {self.engine.self_healing.health_score if self.engine else 'N/A'}%

💾 MEMORY:
  {self.engine.memory.get_stats() if self.engine else 'N/A'}

🔄 SELF-IMPROVEMENT:
  {self.engine.self_improvement.get_improvement_stats() if self.engine else 'N/A'}
"""
            self.status_display.setText(status_text)


def create_desktop_app(engine=None):
    """Create and return the desktop application"""
    if not PYQT_AVAILABLE:
        logger.error("PyQt5 is required for desktop UI")
        return None
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = REXMainWindow(engine)
    window.show()
    
    return app, window
