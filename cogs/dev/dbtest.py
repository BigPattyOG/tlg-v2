# cogs/dev/dbtest.py
"""command for running a database test command."""

from logging import getLogger

from discord import Embed
from discord.ext.commands import Context
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import Database

logger = getLogger(__name__)


async def database_test(_self, ctx: Context) -> None:
    """Runs a test query and ORM check on the database."""
    # Get database instance from bot
    db: Database = _self.bot.get_db()

    # Perform comprehensive health check
    health_result = await db.health_check()
    if health_result.failed:
        await ctx.send(f"❌ Database health check failed: {health_result.error}")
        return

    # Get basic database information using safe methods
    db_name_result = await db.fetchval("SELECT current_database()")
    if db_name_result.failed:
        await ctx.send(f"❌ Failed to get database name: {db_name_result.error}")
        return

    version_result = await db.fetchval("SELECT version()")
    if version_result.failed:
        await ctx.send(f"❌ Failed to get database version: {version_result.error}")
        return

    user_count_result = await db.fetchval(
        "SELECT COUNT(*) FROM pg_stat_activity WHERE state='active'"
    )
    if user_count_result.failed:
        await ctx.send(f"❌ Failed to get active connections: {user_count_result.error}")
        return

    # Test ORM functionality
    orm_passed = False
    orm_error = None
    try:
        async with db.get_session() as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            orm_passed = result.scalar() == 1
    except SQLAlchemyError as e:
        logger.error("ORM test failed: %s", e)
        orm_error = f"SQLAlchemy error: {e}"
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected ORM test error: %s", e)
        orm_error = f"Unexpected error: {e}"

    # Extract data from results
    db_name = db_name_result.data
    version = version_result.data
    user_count = user_count_result.data

    # Create embed with results
    embed = Embed(title="✅ Database Test Results", color=0x00FF00)
    embed.add_field(name="Database Name", value=db_name, inline=False)
    embed.add_field(
        name="PostgreSQL Version",
        value=version[:50] + "..." if len(version) > 50 else version,
        inline=False,
    )
    embed.add_field(name="Active Connections", value=str(user_count), inline=True)
    embed.add_field(name="AsyncPG Test", value="✅ Passed", inline=True)

    if orm_passed:
        embed.add_field(name="SQLAlchemy ORM Test", value="✅ Passed", inline=True)
    else:
        embed.add_field(name="SQLAlchemy ORM Test", value="❌ Failed", inline=True)
        if orm_error:
            embed.add_field(name="ORM Error", value=orm_error[:1024], inline=False)

    await ctx.send(embed=embed)
