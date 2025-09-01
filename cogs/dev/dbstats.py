# cogs/dev/dbstats.py
"""command for displaying database statistics and usage information."""

from logging import getLogger

from discord import Embed
from discord.ext.commands import Context

from database.connection import Database

logger = getLogger(__name__)


async def database_stats(_self, ctx: Context) -> None:
    """Shows statistics and usage info for the current database."""
    # Get database instance from bot
    db: Database = _self.bot.get_db()

    # Check database health first
    health_result = await db.health_check()
    if health_result.failed:
        await ctx.send(f"❌ Database unavailable: {health_result.error}")
        return

    # Fetch database statistics using safe method
    stats_result = await db.fetchrow(
        """
        SELECT datname as db_name, numbackends as connections,
        xact_commit as transactions_committed, xact_rollback as transactions_rolled_back,
        blks_read as blocks_read, blks_hit as blocks_hit,
        temp_files as temp_files, temp_bytes as temp_bytes
        FROM pg_stat_database WHERE datname=current_database()
    """
    )

    if stats_result.failed:
        logger.error("Database stats error: %s", stats_result.error)
        await ctx.send(f"❌ Database stats error: {stats_result.error}")
        return

    if stats_result.data is None:
        await ctx.send("❌ No database statistics found")
        return

    stats = stats_result.data

    # Calculate cache hit ratio
    total_blocks = stats["blocks_read"] + stats["blocks_hit"]
    cache_hit_ratio = (stats["blocks_hit"] / total_blocks * 100) if total_blocks > 0 else 0

    embed = Embed(title="📊 Database Statistics", color=0x00AAFF)
    embed.add_field(name="Database", value=stats["db_name"], inline=True)
    embed.add_field(name="Active Connections", value=stats["connections"], inline=True)
    embed.add_field(name="Cache Hit Ratio", value=f"{cache_hit_ratio:.2f}%", inline=True)
    embed.add_field(
        name="Committed Transactions", value=f"{stats['transactions_committed']:,}", inline=True
    )
    embed.add_field(
        name="Rolled Back Transactions",
        value=f"{stats['transactions_rolled_back']:,}",
        inline=True,
    )
    embed.add_field(name="Blocks Read", value=f"{stats['blocks_read']:,}", inline=True)
    embed.add_field(name="Blocks Hit", value=f"{stats['blocks_hit']:,}", inline=True)
    embed.add_field(name="Temp Files", value=f"{stats['temp_files']:,}", inline=True)
    embed.add_field(name="Temp Bytes", value=f"{stats['temp_bytes']:,}", inline=True)

    await ctx.send(embed=embed)
