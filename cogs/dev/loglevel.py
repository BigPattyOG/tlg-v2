# cogs/dev/loglevel.py
"""command for changing log level"""


from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, getLogger

logger = getLogger(__name__)


async def set_log_level(_self, ctx, level: str):
    """Change log level dynamically"""
    level = level.upper()
    level_map = {
        "DEBUG": DEBUG,
        "INFO": INFO,
        "WARNING": WARNING,
        "ERROR": ERROR,
        "CRITICAL": CRITICAL,
    }
    if level not in level_map:
        await ctx.send(f"❌ Invalid log level. Valid levels: {', '.join(level_map)}")
        return
    getLogger().setLevel(level_map[level])
    logger.info("Log level changed to %s by %s", level, ctx.author)
    await ctx.send(f"✅ Log level changed to `{level}`")
