# cogs/minimal/__init__.py
"""
Super minimal cog as a package
"""

import logging

from discord.ext import commands

from .minimal import logic

logger = logging.getLogger(__name__)

# Minimal metadata required
COG_METADATA = {
    "name": "SuperMinimal",
    "is_cog": True,
    "enabled": True,
    "commands": {
        "ping": {
            "help": "ping pong",
            "aliases": [],
        },
        "minimal": {
            "help": "minimal command (reverse input)",
            "aliases": [],
        },
    },
}


class SuperMinimal(commands.Cog):
    """Super minimal example cog"""

    def __init__(self, bot):
        self.bot = bot
        logger.info("SuperMinimal cog loaded")

    @commands.command(name="ping", help=COG_METADATA["commands"]["ping"]["help"])
    async def ping(self, ctx):
        """Simple ping command"""
        await ctx.send("🏓 Pong!")

    @commands.command(name="minimal", help=COG_METADATA["commands"]["minimal"]["help"])
    async def minimal(self, ctx, *, data: str = "default"):
        """A command that uses the minimal logic"""
        result = logic(data)
        await ctx.send(f"Minimal logic returned: `{result}`")


async def setup(bot):
    """Adds the SuperMinimal cog"""
    await bot.add_cog(SuperMinimal(bot))
