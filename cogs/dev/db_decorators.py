# cogs/dev/db_decorators.py
"""Database decorators for dev cogs."""

from functools import wraps
from logging import getLogger
from typing import Any, Awaitable, Callable, TypeVar

logger = getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def requires_database(func: F) -> F:
    """
    Decorator to check database connection before executing command.

    The decorated function will receive a 'db' parameter as the last argument.
    """

    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if not self.bot.has_database:
            await ctx.send("❌ Database not initialized")
            return

        try:
            db = self.bot.get_db()
            if db is None:
                await ctx.send("❌ Failed to get database connection")
                return
            if "db" not in kwargs:
                kwargs["db"] = db
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Database connection error in %s: %s", func.__name__, e)
            await ctx.send(f"❌ Database connection failed: {e}")
            return

    return wrapper  # type: ignore[return-value]
