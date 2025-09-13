"""Cog for reloading bot extensions (Owner only)."""

from logging import getLogger

from discord import HTTPException
from discord.ext import commands

logger = getLogger(__name__)


async def load_cog(self, ctx, cog_name: str):
    """Load a cog (Owner only)"""
    try:
        await self.bot.load_extension(cog_name)
        logger.info("Cog %s loaded by %s", cog_name, ctx.author)

        # Sync slash commands with Discord
        try:
            await self.bot.tree.sync()
            await ctx.send(f"✅ Loaded `{cog_name}` and synced slash commands")
        except (HTTPException, RuntimeError) as sync_error:
            await ctx.send(
                f"✅ Loaded `{cog_name}` but failed to sync slash commands: {sync_error}"
            )
            logger.warning(
                "Failed to sync slash commands after loading %s: %s", cog_name, sync_error
            )

    except commands.ExtensionAlreadyLoaded as e:
        await ctx.send(f"❌ Extension already loaded: {e}")
    except commands.ExtensionFailed as e:
        await ctx.send(f"❌ Extension failed to load: {e}")
    except commands.ExtensionNotFound as e:
        await ctx.send(f"❌ Extension not found: {e}")
    except (commands.ExtensionError, RuntimeError) as e:
        await ctx.send(f"❌ Unexpected error loading `{cog_name}`: {e}")
        logger.exception("Unexpected error loading %s: %s", cog_name, e)


async def disable_cog(self, ctx, cog_name: str):
    """Disable/unload a cog (Owner only)"""
    try:
        await self.bot.unload_extension(cog_name)
        logger.info("Cog %s disabled by %s", cog_name, ctx.author)

        # Sync slash commands with Discord
        try:
            await self.bot.tree.sync()
            await ctx.send(f"✅ Disabled `{cog_name}` and synced slash commands")
        except (HTTPException, RuntimeError) as sync_error:
            await ctx.send(
                f"✅ Disabled `{cog_name}` but failed to sync slash commands: {sync_error}"
            )
            logger.warning(
                "Failed to sync slash commands after disabling %s: %s", cog_name, sync_error
            )

    except commands.ExtensionNotLoaded as e:
        await ctx.send(f"❌ Extension not loaded: {e}")
    except (commands.ExtensionError, RuntimeError) as e:
        await ctx.send(f"❌ Unexpected error disabling `{cog_name}`: {e}")
        logger.exception("Unexpected error disabling %s: %s", cog_name, e)


async def reload_cog(self, ctx, cog_name: str):
    """Reload a cog (Owner only)"""
    try:
        await self.bot.reload_extension(cog_name)
        logger.info("Cog %s reloaded by %s", cog_name, ctx.author)

        # Sync slash commands with Discord
        try:
            await self.bot.tree.sync()
            await ctx.send(f"✅ Reloaded `{cog_name}` and synced slash commands")
        except (HTTPException, RuntimeError) as sync_error:
            await ctx.send(
                f"✅ Reloaded `{cog_name}` but failed to sync slash commands: {sync_error}"
            )
            logger.warning(
                "Failed to sync slash commands after reloading %s: %s", cog_name, sync_error
            )

    except commands.ExtensionNotLoaded as e:
        await ctx.send(f"❌ Extension not loaded: {e}")
    except commands.ExtensionFailed as e:
        await ctx.send(f"❌ Extension failed to reload: {e}")
    except commands.ExtensionNotFound as e:
        await ctx.send(f"❌ Extension not found: {e}")
    except (commands.ExtensionError, RuntimeError) as e:
        await ctx.send(f"❌ Unexpected error reloading `{cog_name}`: {e}")
        logger.exception("Unexpected error reloading %s: %s", cog_name, e)
