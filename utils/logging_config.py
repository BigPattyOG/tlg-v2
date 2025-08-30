# utils/logging_config.py
"""
Logging configuration
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from config.settings import get_settings


def setup_logging() -> logging.Logger:
    """Setup comprehensive logging system"""
    settings = get_settings()

    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if settings.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if settings.log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.log_file_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, settings.log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Error file handler for ERROR and CRITICAL logs
    if settings.log_to_file:
        error_file_path = log_file_path.parent / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=str(error_file_path),
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    # Discord.py logging configuration
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO if settings.debug_mode else logging.WARNING)

    # HTTP logging for debug
    if settings.debug_mode:
        http_logger = logging.getLogger("discord.http")
        http_logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info("Log level: %s", settings.log_level)
    logger.info("Log to file: %s", settings.log_to_file)
    logger.info("Log to console: %s", settings.log_to_console)

    return logger
