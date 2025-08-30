"""Cog for reloading bot extensions (Owner only)."""

from logging import getLogger

from discord.ext import commands

logger = getLogger(__name__)


async def reload_cog(self, ctx, cog_name: str):
    """Reload a cog (Owner only)"""
    try:
        await self.bot.reload_extension(cog_name)
        logger.info("Cog %s reloaded by %s", cog_name, ctx.author)
        await ctx.send(f"✅ Reloaded `{cog_name}`")
    except commands.ExtensionNotLoaded as e:
        await ctx.send(f"❌ Extension not loaded: {e}")
    except commands.ExtensionFailed as e:
        await ctx.send(f"❌ Extension failed to reload: {e}")
    except commands.ExtensionNotFound as e:
        await ctx.send(f"❌ Extension not found: {e}")
    except (commands.ExtensionError, RuntimeError) as e:
        await ctx.send(f"❌ Unexpected error reloading `{cog_name}`: {e}")
        logger.exception("Unexpected error reloading %s: %s", cog_name, e)
