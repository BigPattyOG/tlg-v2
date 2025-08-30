# cogs/dev/logs.py
"""command for retrieving recent log entries from the bot log file."""

from logging import getLogger

from discord import Embed

from config.settings import get_settings

logger = getLogger(__name__)


async def get_logs(_, ctx, lines: int = 20):
    """Get recent log entries (Owner only)"""
    settings = get_settings()
    if not settings.log_to_file:
        await ctx.send("❌ File logging is disabled")
        return

    try:
        with open(settings.log_file_path, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        recent_logs = log_lines[-lines:] if len(log_lines) >= lines else log_lines
        log_content = "".join(recent_logs)
        if len(log_content) > 1900:
            log_content = "...\n" + log_content[-1900:]
        embed = Embed(
            title=f"📝 Recent Logs ({len(recent_logs)} lines)",
            description=f"```\n{log_content}\n```",
            color=0x00AAFF,
        )
        await ctx.send(embed=embed)
    except (OSError, IOError) as e:
        logger.error("Error reading logs: %s", e)
        await ctx.send(f"❌ Error reading logs: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error in get_logs: %s", e)
        await ctx.send(f"❌ Unexpected error reading logs: {e}")
