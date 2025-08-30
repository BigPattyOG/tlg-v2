# core/bot.py
"""
Core bot class
"""

from asyncio import CancelledError
from logging import getLogger
from time import time
from typing import Optional, cast

from discord import (
    Activity,
    ActivityType,
    Forbidden,
    HTTPException,
    Intents,
    Message,
    NotFound,
    TextChannel,
)
from discord.ext import commands
from discord.ext.commands import Context, errors

from cogs import COG_MODULES
from config.settings import get_settings
from database import Database

logger = getLogger(__name__)


class CoreBot(commands.Bot):
    """
    Bot core
    """

    def __init__(self):
        settings = get_settings()
        intents = Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
        )

        # Bot statistics
        self.startup_time = time()
        self.commands_used = 0
        self.messages_seen = 0

        # Database
        self.db: Optional[Database] = None

    async def setup_hook(self):
        """Initialize bot components"""
        logger.info("Starting bot setup...")

        # Initialize database
        await self._setup_database()

        # Load all cogs
        await self._load_all_cogs()

        # Sync application (slash) commands globally
        await self.tree.sync()

        logger.info("Bot setup complete")

    async def _setup_database(self):
        """Initialize database connection"""
        settings = get_settings()

        if not settings.database_url:
            logger.warning("⚠️ DATABASE_URL not provided, running without database")
            return

        try:
            self.db = Database()
            await self.db.connect()
            logger.info("✅ Database initialized successfully")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("❌ Failed to initialize database: %s", e)

    async def _load_all_cogs(self):
        for module_name in COG_MODULES:
            try:
                await self.load_extension(module_name)
                logger.info("✅ Loaded %s", module_name)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("❌ Failed to load %s: %s", module_name, e)

    async def close(self):
        """
        Cleanup on bot shutdown
        """
        logger.info("Shutting down bot...")

        # Send shutdown message to status channel
        settings = get_settings()
        channel_id = int(settings.status_channel)
        channel = self.get_channel(channel_id)
        if isinstance(channel, TextChannel):
            try:
                await channel.send("🔴 Bot is shutting down.")
            except CancelledError:
                logger.warning("Shutdown message sending cancelled (asyncio.CancelledError)")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Failed to send shutdown message: %s [%s]", e, type(e).__name__, exc_info=True
                )

        if self.db:
            await self.db.disconnect()

        await super().close()

    async def on_ready(self):
        """Called when bot is ready"""
        if self.user is not None:
            logger.info("Bot logged in as %s (ID: %s)", self.user, self.user.id)
        else:
            logger.info("Bot logged in, but user is None")
        db_status = "Yes" if self.db and self.db.is_connected else "No"
        logger.info("Database connected: %s", db_status)
        logger.info("Loaded %d cogs with %d commands", len(self.cogs), len(self.commands))

        # Send online message to status channel
        settings = get_settings()
        channel_id = int(settings.status_channel)
        channel = self.get_channel(channel_id)
        if isinstance(channel, TextChannel):
            try:
                await channel.send("🟢 Bot is online!")
            except (HTTPException, Forbidden, NotFound) as e:
                logger.error(
                    "Failed to send online message: %s [%s]", e, type(e).__name__, exc_info=True
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Unexpected error sending online message: %s [%s]",
                    e,
                    type(e).__name__,
                    exc_info=True,
                )

        # Set bot status
        activity = Activity(
            type=ActivityType.watching,
            name=f"{len(self.guilds)} servers | {get_settings().command_prefix}help",
        )
        await self.change_presence(activity=activity)

    async def on_message(self, message: Message, /):
        """Track message statistics"""
        if not message.author.bot:
            self.messages_seen += 1

        await self.process_commands(message)

    async def on_command(self, ctx):
        """Track command usage"""
        self.commands_used += 1
        logger.info(
            "Command '%s' used by %s in %s",
            ctx.command,
            ctx.author,
            ctx.guild.name if ctx.guild else "DMs",
        )

    async def on_command_error(self, ctx: Context, error: errors.CommandError, /) -> None:
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param}`")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds")
            return

        # Log unexpected errors
        logger.error("Unhandled command error in %s: %s", ctx.command, error, exc_info=True)
        await ctx.send("❌ An unexpected error occurred. This has been logged.")

    @property
    def has_database(self) -> bool:
        """Check if database is available and connected"""
        return self.db is not None and self.db.is_connected

    def get_db(self) -> Database:
        """Get database instance, raises if not connected"""
        if not self.has_database:
            raise RuntimeError("Database is not connected")
        return cast(Database, self.db)
