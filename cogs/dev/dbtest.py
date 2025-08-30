# cogs/dev/dbtest.py
"""command for running a database test command."""

from logging import getLogger
from typing import TYPE_CHECKING

from asyncpg import PostgresError
from discord import Embed
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db_decorators import requires_database

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from database import Database

logger = getLogger(__name__)


@requires_database
async def database_test(_self, ctx: "Context", *, db: "Database") -> None:
    """Runs a test query and ORM check on the database."""
    try:
        test_result = await db.test_connection()
        if not test_result:
            await ctx.send("❌ Database connection test failed")
            return

        db_name = await db.fetchval("SELECT current_database()")
        version = await db.fetchval("SELECT version()")
        user_count = await db.fetchval("SELECT COUNT(*) FROM pg_stat_activity WHERE state='active'")

        orm_passed = False
        try:
            async with db.get_session() as session:
                result = await session.execute(text("SELECT 1 as test_value"))
                orm_passed = result.scalar() == 1
        except SQLAlchemyError as e:
            logger.error("ORM test failed: %s", e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected ORM test error: %s", e)

        embed = Embed(title="✅ Database Test Results", color=0x00FF00)
        embed.add_field(name="Database Name", value=db_name, inline=False)
        embed.add_field(
            name="PostgreSQL Version",
            value=version[:50] + "..." if len(version) > 50 else version,
            inline=False,
        )
        embed.add_field(name="Active Connections", value=str(user_count), inline=True)
        embed.add_field(name="AsyncPG Test", value="✅ Passed", inline=True)
        embed.add_field(
            name="SQLAlchemy ORM Test",
            value="✅ Passed" if orm_passed else "❌ Failed",
            inline=True,
        )
        await ctx.send(embed=embed)

    except PostgresError as e:
        logger.error("Database test error: %s", e)
        await ctx.send(f"❌ Database test error: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error in database test: %s", e)
        await ctx.send("❌ Unexpected error occurred during database test.")
