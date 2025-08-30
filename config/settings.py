# config/settings.py
"""
Configuration management
"""

from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:  # pylint: disable=too-many-instance-attributes
    """
    settings
    """

    # Discord
    discord_token: str
    status_channel: str
    command_prefix: str = "!"

    # Database
    database_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    log_file_max_bytes: int = 10 * 1024 * 1024
    log_file_backup_count: int = 5
    log_file_path: str = "data/logs/bot.log"

    # Debug
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """
        from env
        """
        discord_token = getenv("DISCORD_TOKEN")
        if discord_token is None:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        status_channel = getenv("STATUS_CHANNEL")
        if status_channel is None:
            raise ValueError("STATUS_CHANNEL environment variable is required")
        return cls(
            discord_token=discord_token,
            status_channel=status_channel,
            command_prefix=getenv("COMMAND_PREFIX", "!"),
            database_url=getenv("DATABASE_URL"),
            log_level=getenv("LOG_LEVEL", "INFO"),
            log_to_file=getenv("LOG_TO_FILE", "true").lower() == "true",
            log_to_console=getenv("LOG_TO_CONSOLE", "true").lower() == "true",
            log_file_max_bytes=int(getenv("LOG_FILE_MAX_BYTES", "10485760")),
            log_file_backup_count=int(getenv("LOG_FILE_BACKUP_COUNT", "5")),
            log_file_path=getenv("LOG_FILE_PATH", "data/logs/bot.log"),
            debug_mode=getenv("DEBUG_MODE", "false").lower() == "true",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Settings instance
    """
    return Settings.from_env()
