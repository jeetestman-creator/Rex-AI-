<div align="center">

# 📘 REX Setup Guide

### *Complete Installation & Configuration Manual*

**For Windows, macOS, Linux, and Advanced Deployments**

[Prerequisites](#-prerequisites) • [Installation](#-installation) • [Configuration](#-configuration) • [Building](#-building-executables) • [Troubleshooting](#-troubleshooting) • [FAQ](#-faq)

</div>

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Installation](#-installation)
3. [Platform-Specific Setup](#-platform-specific-setup)
4. [Voice Setup](#-voice-setup)
5. [Configuration](#-configuration)
6. [Building Executables](#-building-executables)
7. [Creating Installers](#-creating-installers)
8. [Deployment](#-deployment)
9. [Adding Custom Skills](#-adding-custom-skills)
10. [Troubleshooting](#-troubleshooting)
11. [FAQ](#-faq)

---

## ✅ Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Dual-core 2GHz | Quad-core 3GHz+ |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 2GB free | 10GB+ SSD |
| **OS** | Windows 10 / macOS 10.15 / Ubuntu 20.04 | Latest versions |
| **Python** | 3.9 | 3.11+ |
| **Network** | Optional (for voice features) | Broadband |

### Required Software

- **Python 3.9+** — [Download here](https://www.python.org/downloads/)
- **Git** — [Download here](https://git-scm.com/)
- **pip** (comes with Python)
- **Microphone** (for voice features)
- **Speakers/Headphones** (for audio output)

### Optional Software

- **FFmpeg** — For advanced audio/video processing
- **Pandoc** — For PDF manual generation
- **PyInstaller** — For building executables
- **Inno Setup** — For Windows installers (Windows only)

---

## 🚀 Installation

### Method 1: Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/REX.git
cd REX

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run REX
python main.py
