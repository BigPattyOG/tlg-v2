# cogs/example.py
"""
Minimal cog example
"""

from asyncio import sleep
from logging import getLogger

from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import get_settings

logger = getLogger(__name__)


STATUS_CHANNEL_ID = int(get_settings().status_channel)

# Minimal metadata required
COG_METADATA = {
    "name": "Example",
    "is_cog": True,
    "enabled": False,
    "commands": {
        "greet": {
            "help": "Greet someone with a custom message",
            "aliases": [],
        },
    },
}


class Example(commands.Cog):
    """A minimal example cog"""

    def __init__(self, bot):
        self.bot = bot
        self.status_msg = None
        logger.info("Example cog loaded")

    @commands.command()
    async def hello(self, ctx):
        """Say hello to the user"""
        await ctx.send(f"👋 Hello {ctx.author.mention}, I am alive!")

    @app_commands.command(name="greet", description=COG_METADATA["commands"]["greet"]["help"])
    @app_commands.describe(
        name="The name of the person you want to greet",
        times="How many times to repeat the greeting",
    )
    async def greet(self, interaction: Interaction, name: str, times: int = 1):
        """Greeter example with Discord args"""
        message = (f"Hello, {name}! " * times).strip()
        await interaction.response.send_message(message)

    async def status_heartbeat(self):
        """Scheduled heartbeat example"""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        while not self.bot.is_closed():
            if channel:
                await channel.send("✅ Bot is alive!")
            await sleep(120)


async def setup(bot):
    """Adds the Example cog and starts heartbeat task"""
    cog = Example(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog.status_heartbeat())
