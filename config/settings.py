"""
REX AI Assistant - Global Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SKILLS_DIR = BASE_DIR / "skills"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"

# Create directories
for d in [DATA_DIR, SKILLS_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# REX Configuration
REX_CONFIG = {
    "name": "REX",
    "version": "1.0.0",
    "author": "REX Development Team",
    "description": "Advanced AI Assistant with 20L+ Skills",
    "wake_word": "hey rex",
    "default_language": "en",
    "supported_languages": ["en", "ta", "hi", "es", "fr", "de", "ja", "zh", "ar", "pt"],
    "voice_rate": 175,
    "voice_volume": 1.0,
}

# NLP Configuration
NLP_CONFIG = {
    "model_name": "all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "max_context_length": 4096,
    "similarity_threshold": 0.75,
}

# Memory Configuration
MEMORY_CONFIG = {
    "max_episodic_memory": 100000,
    "max_semantic_memory": 500000,
    "memory_decay_rate": 0.01,
    "consolidation_interval": 3600,  # seconds
    "vector_db_path": str(DATA_DIR / "vector_store"),
    "knowledge_graph_path": str(DATA_DIR / "knowledge_graph.json"),
}

# Voice Configuration
VOICE_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 1024,
    "silence_threshold": 500,
    "silence_duration": 1.5,
    "language": "en-IN",
}

# Security Configuration
SECURITY_CONFIG = {
    "encryption_key_path": str(DATA_DIR / "encryption.key"),
    "max_login_attempts": 5,
    "session_timeout": 3600,
    "enable_guardrails": True,
    "content_filter_level": "medium",
}

# Smart Home Configuration
SMART_HOME_CONFIG = {
    "protocol": "mqtt",
    "broker": "localhost",
    "port": 1883,
    "devices": {},
}

# UI Configuration
UI_CONFIG = {
    "theme": "dark_cyber",
    "primary_color": "#00f5ff",
    "secondary_color": "#7b2ff7",
    "accent_color": "#ff006e",
    "background_color": "#0a0a0f",
    "text_color": "#e0e0e0",
    "font_family": "Segoe UI",
    "font_size": 12,
    "animation_enabled": True,
    "transparency": 0.95,
}

# Investment Configuration
INVESTMENT_CONFIG = {
    "watchlist": [],
    "alerts": {},
    "portfolio": {},
    "risk_tolerance": "medium",
    "auto_rebalance": False,
}

# Self-Improvement Configuration
SELF_IMPROVEMENT_CONFIG = {
    "enabled": True,
    "learning_rate": 0.001,
    "feedback_collection": True,
    "auto_skill_generation": True,
    "max_generated_skills": 10000,
    "improvement_interval": 86400,  # daily
}

# Web Server Configuration
WEB_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "ssl_enabled": False,
}

# Logging Configuration
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    "rotation": "10 MB",
    "retention": "30 days",
    "file": str(LOGS_DIR / "rex.log"),
}
