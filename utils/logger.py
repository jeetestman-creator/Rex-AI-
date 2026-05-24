"""
REX Utility - Logging Configuration
"""
from loguru import logger
from config.settings import LOG_CONFIG


def setup_logging():
    """Configure logging for REX"""
    logger.remove()  # Remove default handler
    
    # Console handler
    logger.add(
        lambda msg: print(msg, end=''),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
    )
    
    # File handler
    logger.add(
        LOG_CONFIG["file"],
        level=LOG_CONFIG["level"],
        format=LOG_CONFIG["format"],
        rotation=LOG_CONFIG["rotation"],
        retention=LOG_CONFIG["retention"],
    )
    
    return logger
