#!/usr/bin/env python3
"""
🦖 REX - Advanced AI Assistant
===============================
Main Entry Point

A full-stack AI assistant with:
- Natural voice conversations
- Multi-language support (English, Tamil, Hindi +)
- 20L+ extensible skills
- Self-improving capabilities
- Cross-platform (Desktop, Web, Mobile API)
- Smart home integration
- Investment analysis
- Cybersecurity tools
- Code generation
- And much more!

Usage:
    python main.py                  # Start with desktop UI
    python main.py --web            # Start web server only
    python main.py --cli            # Start CLI mode
    python main.py --all            # Start all interfaces
"""
import sys
import asyncio
import argparse
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from config.settings import LOG_CONFIG, WEB_CONFIG

# Configure logging
logger.add(
    LOG_CONFIG["file"],
    level=LOG_CONFIG["level"],
    format=LOG_CONFIG["format"],
    rotation=LOG_CONFIG["rotation"],
    retention=LOG_CONFIG["retention"],
)


def print_banner():
    """Print REX banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗ ███████╗██╗  ██╗                               ║
    ║   ██╔══██╗██╔════╝╚██╗██╔╝                               ║
    ║   ██████╔╝█████╗   ╚███╔╝                                ║
    ║   ██╔══██╗██╔══╝   ██╔██╗                                ║
    ║   ██║  ██║███████╗██╔╝ ██╗                               ║
    ║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                               ║
    ║                                                           ║
    ║   Advanced AI Assistant v1.0                              ║
    ║   Multi-Platform | Multi-Language | Self-Improving        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def run_cli(engine):
    """Run CLI mode"""
    print("\n🦖 REX CLI Mode - Type 'exit' or 'quit' to stop")
    print("=" * 50)
    
    await engine.start()
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ('exit', 'quit', 'bye', 'goodbye'):
                print("\n🦖 REX: Goodbye! Have a great day! 👋")
                break
            
            if not user_input:
                continue
            
            result = await engine.process(user_input)
            
            print(f"\n🦖 REX: {result['text']}")
            
            if result.get('intent'):
                logger.debug(f"Intent: {result['intent']} | Time: {result.get('processing_time', 0):.3f}s")
                
        except KeyboardInterrupt:
            print("\n\n🦖 REX: Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n🦖 REX: I encountered an error: {e}")
            logger.error(f"CLI error: {e}")
    
    await engine.stop()


def run_desktop(engine):
    """Run desktop GUI"""
    try:
        from ui.desktop.main_window import create_desktop_app
        app, window = create_desktop_app(engine)
        
        # Start engine in background
        import threading
        
        def start_engine():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(engine.start())
        
        thread = threading.Thread(target=start_engine, daemon=True)
        thread.start()
        
        sys.exit(app.exec_())
        
    except ImportError as e:
        logger.error(f"Desktop UI error: {e}")
        print("PyQt5 is required for desktop UI. Install with: pip install PyQt5")
        print("Falling back to CLI mode...")
        asyncio.run(run_cli(engine))


def run_web(engine):
    """Run web server"""
    try:
        from ui.web.app import run_web_server
        print(f"\n🌐 Starting REX Web Server at http://localhost:{WEB_CONFIG['port']}")
        run_web_server(engine)
    except ImportError as e:
        logger.error(f"Web server error: {e}")
        print("Flask is required for web UI. Install with: pip install flask flask-cors")


def run_all(engine):
    """Run all interfaces"""
    import threading
    
    # Start web server in background
    web_thread = threading.Thread(target=run_web, args=(engine,), daemon=True)
    web_thread.start()
    
    print(f"🌐 Web UI available at http://localhost:{WEB_CONFIG['port']}")
    
    # Run desktop as main
    run_desktop(engine)


def main():
    """Main entry point"""
    print_banner()
    
    parser = argparse.ArgumentParser(description="REX AI Assistant")
    parser.add_argument('--web', action='store_true', help='Start web server only')
    parser.add_argument('--cli', action='store_true', help='Start CLI mode')
    parser.add_argument('--all', action='store_true', help='Start all interfaces')
    parser.add_argument('--desktop', action='store_true', help='Start desktop GUI (default)')
    
    args = parser.parse_args()
    
    # Initialize engine
    logger.info("🦖 Starting REX AI Assistant...")
    
    from core.engine import REXEngine
    engine = REXEngine()
    
    print(f"\n✅ REX initialized with {len(engine.skill_registry)} skills")
    print(f"📊 Engine Status: {engine.get_status()['name']} v{engine.get_status()['version']}")
    
    # Determine mode
    if args.web:
        run_web(engine)
    elif args.cli:
        asyncio.run(run_cli(engine))
    elif args.all:
        run_all(engine)
    else:
        # Default: try desktop, fallback to CLI
        try:
            run_desktop(engine)
        except Exception as e:
            logger.error(f"Desktop failed: {e}")
            print("Falling back to CLI mode...")
            asyncio.run(run_cli(engine))


if __name__ == "__main__":
    main()
