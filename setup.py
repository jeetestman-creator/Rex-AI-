"""
REX Setup - Installation & Build Script
"""
import os
import sys
import subprocess
import platform
from pathlib import Path


def install_dependencies():
    """Install all dependencies"""
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
    print("✅ Dependencies installed!")


def create_desktop_shortcut():
    """Create desktop shortcut"""
    system = platform.system()
    
    if system == "Windows":
        create_windows_shortcut()
    elif system == "Linux":
        create_linux_shortcut()
    elif system == "Darwin":
        create_mac_shortcut()


def create_windows_shortcut():
    """Create Windows desktop shortcut"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(f"{os.path.expanduser('~')}\\Desktop\\REX AI.lnk")
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = str(Path(__file__).parent / "main.py")
        shortcut.WorkingDirectory = str(Path(__file__).parent)
        shortcut.save()
        print("✅ Desktop shortcut created!")
    except ImportError:
        print("⚠️ Install pywin32 for shortcut creation: pip install pywin32")


def create_linux_shortcut():
    """Create Linux .desktop file"""
    desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=REX AI Assistant
Comment=Advanced AI Assistant
Exec={sys.executable} {Path(__file__).parent / 'main.py'}
Icon={Path(__file__).parent / 'assets' / 'rex_icon.png'}
Terminal=false
Categories=Utility;
"""
    desktop_path = Path.home() / ".local" / "share" / "applications" / "rex-ai.desktop"
    desktop_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(desktop_path, 'w') as f:
        f.write(desktop_entry)
    
    os.chmod(desktop_path, 0o755)
    print("✅ Linux desktop entry created!")


def create_mac_shortcut():
    """Create macOS app bundle"""
    print("ℹ️ For macOS, create an app bundle using py2app")


def build_executable():
    """Build standalone executable using PyInstaller"""
    print("🔨 Building executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=REX",
        "--windowed",
        "--onefile",
        "--icon=assets/rex_icon.ico",
        "--add-data=config;config",
        "--add-data=skills;skills",
        "--hidden-import=PyQt5",
        "--hidden-import=flask",
        "--hidden-import=speech_recognition",
        "--hidden-import=pyttsx3",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Executable built in dist/ folder!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("Make sure PyInstaller is installed: pip install pyinstaller")


def generate_user_manual():
    """Generate user manual PDF"""
    print("📖 Generating user manual...")
    
    manual_content = """# REX AI Assistant - User Manual
## Version 1.0

### Table of Contents
1. Introduction
2. Installation
3. Getting Started
4. Features & Skills
5. Voice Commands
6. Configuration
7. Troubleshooting

---

### 1. Introduction
REX is an advanced AI assistant with capabilities including:
- Natural voice conversations in multiple languages
- Code generation in multiple programming languages
- Investment and stock analysis
- Smart home control
- Cybersecurity tools
- Calendar and scheduling
- Web search and scraping
- Self-improving AI capabilities

### 2. Installation

#### Prerequisites
- Python 3.9+
- pip package manager
- 4GB+ RAM recommended

#### Quick Install
```bash
git clone <repository-url>
cd REX
pip install -r requirements.txt
python main.py
