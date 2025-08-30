# TLG-v2 Discord Bot

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
![Version](https://img.shields.io/badge/version-0.1.0-orange)
[![Build Status](https://github.com/BigPattyOG/tlg-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/BigPattyOG/tlg-v2/actions/workflows/ci.yml)

## Overview

TLG-v2 is a modular Discord bot designed for gaming communities, featuring database integration, logging, and extensible command cogs.

---

## Features

### Discord Bot Core

- Custom command prefix, status channel, and logging.
- Tracks bot statistics (uptime, commands used, messages seen).
- Graceful startup and shutdown messages.
- Global error handling for commands.

### Cogs (Extensions)

- **debug:** System info, alive check, log retrieval, dynamic log level, cog reload, database tests/stats.
- **example:** Minimal demonstration cog (not loaded by default).

### Database Integration

- Async PostgreSQL connection via asyncpg and SQLAlchemy ORM.
- Connection pooling, session management, and transaction support.
- Utility methods for raw SQL and ORM queries.

### Logging

- Configurable logging to file and console.
- Rotating log files and error logs.
- Discord.py and HTTP logging support.

### Configuration

- Environment-based settings via `.env` and `settings.py`.
- Supports custom database URL, logging options, debug mode.

---

## Project Structure

```bash
bot.py                   # Main entry point
core/bot.py              # Core bot class
cogs/                    # Command extensions (cogs)
config/settings.py       # Configuration management
database/connection.py   # Database handler
utils/logging_config.py  # Logging setup
data/logs/               # Log files
```

---

## Installation

### Clone the repository

```sh
git clone <repo-url>
cd tlg-v2
```

### Install dependencies

- Python 3.13+
- Use a modern tool (`uv`, `poetry`, `pdm`) to install from `pyproject.toml`:

```sh
uv pip install -r pyproject.toml
# or
poetry install
# or
pdm install
```

### Configure environment

Copy `.env.example` to `.env` and fill in your Discord token, database URL, etc.

**Example `.env`:**

```env
# Discord
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=!
STATUS_CHANNEL=your_channel_id_here

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Logging Configuration
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
LOG_FILE_MAX_BYTES=10485760
LOG_FILE_BACKUP_COUNT=5
LOG_FILE_PATH=data/logs/bot.log

# Debug Mode
DEBUG_MODE=false
```

---

## Usage

### Run the bot

```sh
python bot.py
```

### Bot Commands

- `!alive` / `!ping` / `!status`: Check bot status and system info.
- `!logs`: Show recent log entries (owner only).
- `!loglevel <level>`: Change log level (owner only).
- `!reload <cog>`: Reload a cog (owner only).
- `!dbtest`: Test database connection (owner only).
- `!dbstats`: Show database statistics (owner only).

---

## Development

- **Cogs:** Add new features by creating cogs in `cogs` and listing them in `COG_MODULES` in `__init__.py`.
- **Pre-commit hooks:** Configured in `.pre-commit-config.yaml` for code style and linting.
- **Testing:** Use the debug cog for live status and database tests.

---

## License

MIT License. See `LICENSE` for details.
