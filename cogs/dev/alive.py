# cogs/dev/alive.py
"""Provides the 'alive' command to check bot and system status."""


import logging
from datetime import datetime, timedelta
from platform import python_version, release, system
from time import time

from discord import Embed, __version__
from psutil import Process

logger = logging.getLogger(__name__)


async def alive_command(self, ctx):
    """
    Sends an embed with bot status, uptime, latency, resource usage, and system info.

    Parameters:
        self: The cog or bot instance.
        ctx: The command context.
    """
    logger.info("Alive command used by %s in %s", ctx.author, ctx.guild)

    uptime_seconds = time() - self.bot.startup_time
    uptime = str(timedelta(seconds=int(uptime_seconds)))

    process = Process()
    memory_usage = process.memory_info().rss / 1024 / 1024
    cpu_usage = process.cpu_percent()
    latency = round(self.bot.latency * 1000, 2)

    db_status = "🟢 Connected" if self.bot.has_database else "🔴 Disconnected"
    db_emoji = "✅" if self.bot.has_database else "❌"

    embed = Embed(title="🟢 Bot Status - ALIVE", color=0x00FF00)
    embed.add_field(name="🏓 Latency", value=f"{latency}ms", inline=True)
    embed.add_field(name="⏰ Uptime", value=uptime, inline=True)
    embed.add_field(name=f"{db_emoji} Database", value=db_status, inline=True)
    embed.add_field(name="🏠 Guilds", value=len(self.bot.guilds), inline=True)
    embed.add_field(name="👥 Users", value=len(self.bot.users), inline=True)
    embed.add_field(name="💬 Commands Used", value=self.bot.commands_used, inline=True)
    embed.add_field(name="📨 Messages Seen", value=self.bot.messages_seen, inline=True)
    embed.add_field(name="🖥️ System", value=f"{system()} {release()}", inline=True)
    embed.add_field(name="💾 Memory Usage", value=f"{memory_usage:.1f} MB", inline=True)
    embed.add_field(name="⚡ CPU Usage", value=f"{cpu_usage}%", inline=True)
    embed.add_field(name="🐍 Python Version", value=python_version(), inline=True)
    embed.add_field(name="📚 Discord.py", value=__version__, inline=True)
    embed.add_field(name="🔧 Loaded Cogs", value=len(self.bot.cogs), inline=True)
    embed.set_footer(text="Bot started at")
    embed.timestamp = datetime.fromtimestamp(self.bot.startup_time)

    await ctx.send(embed=embed)
