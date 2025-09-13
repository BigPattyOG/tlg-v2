# cogs/dev/__init__.py
"""
Dev commands
"""


from discord.ext import commands

from .alive import alive_command
from .cog_load import disable_cog, load_cog, reload_cog
from .dbstats import database_stats
from .dbtest import database_test
from .listcogs import list_cogs
from .loglevel import set_log_level
from .logs import get_logs

COG_METADATA = {
    "name": "Dev Commands",
    "is_cog": True,
    "enabled": True,
    "description": "Basic debug tools",
    "version": "1.0.0",
    "commands": {
        "alive": {
            "help": "Check if the bot is alive and responsive.",
            "aliases": ["status"],
        },
        "logs": {
            "help": "Show recent bot logs (default: last 20 lines).",
            "aliases": [],
        },
        "loglevel": {
            "help": "Change logging level (DEBUG, INFO, WARNING, ERROR).",
            "aliases": [],
        },
        "listcogs": {
            "help": "List all available cogs their state and commands.",
            "aliases": [],
        },
        "reload": {
            "help": "Reload a specific cog by module name. (e.g., `cogs.dev`)",
            "aliases": [],
        },
        "load": {
            "help": "Load a specific cog by module name. (e.g., `cogs.dev`)",
            "aliases": [],
        },
        "disable": {
            "help": "Disable/unload a specific cog by module name. (e.g., `cogs.dev`)",
            "aliases": [],
        },
        "dbtest": {
            "help": "Run a test query on the database.",
            "aliases": [],
        },
        "dbstats": {
            "help": "Show database statistics and usage info.",
            "aliases": [],
        },
    },
}


class Dev(commands.Cog):
    """All dev commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="alive",
        aliases=COG_METADATA["commands"]["alive"]["aliases"],
        help=COG_METADATA["commands"]["alive"]["help"],
    )
    async def alive(self, ctx):
        """Responds if the bot is alive and responsive."""
        await alive_command(self, ctx)

    @commands.command(
        name="logs",
        help=COG_METADATA["commands"]["logs"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def logs(self, ctx, lines: int = 20):
        """Shows recent bot logs."""
        await get_logs(self, ctx, lines)

    @commands.command(
        name="loglevel",
        help=COG_METADATA["commands"]["loglevel"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def loglevel(self, ctx, level: str):
        """Changes the logging level."""
        await set_log_level(self, ctx, level)

    @commands.command(
        name="listcogs",
        help=COG_METADATA["commands"]["listcogs"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def listcogs(self, ctx):
        """Lists all available cogs, their state, and commands."""
        await list_cogs(self, ctx)

    @commands.command(
        name="reload",
        help=COG_METADATA["commands"]["reload"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def reload(self, ctx, cog_name: str):
        """Reloads a specific cog by module name."""
        await reload_cog(self, ctx, cog_name)

    @commands.command(
        name="load",
        help=COG_METADATA["commands"]["load"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def load(self, ctx, cog_name: str):
        """Loads a specific cog by module name."""
        await load_cog(self, ctx, cog_name)

    @commands.command(
        name="disable",
        help=COG_METADATA["commands"]["disable"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def disable(self, ctx, cog_name: str):
        """Disables/unloads a specific cog by module name."""
        await disable_cog(self, ctx, cog_name)

    @commands.command(
        name="dbtest",
        help=COG_METADATA["commands"]["dbtest"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def dbtest(self, ctx):
        """Runs a test query on the database."""
        await database_test(self, ctx)

    @commands.command(
        name="dbstats",
        help=COG_METADATA["commands"]["dbstats"]["help"],
        hidden=True,
    )
    @commands.is_owner()
    async def dbstats(self, ctx):
        """Shows database statistics and usage info."""
        await database_stats(self, ctx)


async def setup(bot):
    """Adds the Dev cog to the bot."""
    await bot.add_cog(Dev(bot))
