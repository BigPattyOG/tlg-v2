# cogs/dev/dbstats.py
"""command for displaying database statistics and usage information."""

from logging import getLogger
from typing import TYPE_CHECKING

from asyncpg import PostgresError
from discord import Embed

from .db_decorators import requires_database

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from database.connection import Database

logger = getLogger(__name__)


@requires_database
async def database_stats(_self, ctx: "Context", *, db: "Database") -> None:
    """Shows statistics and usage info for the current database."""
    try:
        stats = await db.fetchrow(
            """
            SELECT datname as db_name, numbackends as connections,
            xact_commit as transactions_committed, xact_rollback as transactions_rolled_back,
            blks_read as blocks_read, blks_hit as blocks_hit,
            temp_files as temp_files, temp_bytes as temp_bytes
            FROM pg_stat_database WHERE datname=current_database()
        """
        )

        if stats is None:
            await ctx.send("❌ No database statistics found")
            return

        cache_hit_ratio = (
            (stats["blocks_hit"] / (stats["blocks_read"] + stats["blocks_hit"]) * 100)
            if stats["blocks_read"] + stats["blocks_hit"] > 0
            else 0
        )

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

    except PostgresError as e:
        logger.error("Database stats error: %s", e)
        await ctx.send(f"❌ Database stats error: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error in database stats: %s", e)
        await ctx.send("❌ Unexpected error occurred while fetching database stats.")
