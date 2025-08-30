# database/connection.py
"""
Main database connection handler with ORM support
"""

from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, List, Optional

from asyncpg import Pool, Record, create_pool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from config.settings import get_settings

logger = getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()


class Database:
    """PostgreSQL database connection manager with ORM support"""

    def __init__(self):
        self.pool: Optional[Pool] = None
        self.engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection pool and SQLAlchemy engine"""
        settings = get_settings()

        if not settings.database_url:
            logger.error("DATABASE_URL not found in environment variables")
            raise ValueError("DATABASE_URL is required")

        try:
            logger.info("Connecting to PostgreSQL database...")

            # Create asyncpg connection pool
            self.pool = await create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                server_settings={"jit": "off"},  # Disable JIT for better compatibility
            )

            # Create SQLAlchemy async engine
            # Convert postgresql:// to postgresql+asyncpg:// for SQLAlchemy
            sqlalchemy_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

            self.engine = create_async_engine(
                sqlalchemy_url,
                echo=False,  # Set to True for SQL query logging
                future=True,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300,
            )

            # Create session factory
            self.async_session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            self._connected = True
            logger.info("✅ Database connection pool and SQLAlchemy engine established")

            # Test connections
            await self.test_connection()

        except Exception as e:
            logger.error("❌ Failed to connect to database: %s", e)
            raise

    async def disconnect(self) -> None:
        """Close database connection pool and SQLAlchemy engine"""
        if self.engine:
            logger.info("Closing SQLAlchemy engine...")
            await self.engine.dispose()
            self.engine = None
            self.async_session_factory = None

        if self.pool:
            logger.info("Closing database connection pool...")
            await self.pool.close()
            self.pool = None

        self._connected = False
        logger.info("✅ Database connections closed")

    async def test_connection(self) -> bool:
        """Test database connections"""
        try:
            # Test asyncpg connection
            if self.pool is not None:
                async with self.pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    if result == 1:
                        logger.info("✅ AsyncPG connection test successful")
                    else:
                        logger.warning("⚠️ AsyncPG connection test returned unexpected result")
                        return False

            # Test SQLAlchemy connection
            if self.engine is not None:
                async with self.engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    if result.scalar() == 1:
                        logger.info("✅ SQLAlchemy connection test successful")
                    else:
                        logger.warning("⚠️ SQLAlchemy connection test returned unexpected result")
                        return False

            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("❌ Database connection test failed: %s", e)
            return False

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected and self.pool is not None and self.engine is not None

    # AsyncPG methods for raw SQL queries
    async def execute(self, query: str, *args) -> str:
        """Execute a query that doesn't return data (INSERT, UPDATE, DELETE)"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *args)
                logger.debug("Executed query: %s... | Result: %s", query[:50], result)
                return result
        except Exception as e:
            logger.error("Error executing query: %s | Query: %s...", e, query[:100])
            raise

    async def fetch(self, query: str, *args) -> List[Record]:
        """Fetch multiple rows from database"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetch(query, *args)
                logger.debug("Fetched %d rows | Query: %s...", len(result), query[:50])
                return result
        except Exception as e:
            logger.error("Error fetching data: %s | Query: %s...", e, query[:100])
            raise

    async def fetchrow(self, query: str, *args) -> Optional[Record]:
        """Fetch single row from database"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(query, *args)
                logger.debug("Fetched single row | Query: %s...", query[:50])
                return result
        except Exception as e:
            logger.error("Error fetching row: %s | Query: %s...", e, query[:100])
            raise

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value from database"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(query, *args)
                logger.debug("Fetched single value | Query: %s...", query[:50])
                return result
        except Exception as e:
            logger.error("Error fetching value: %s | Query: %s...", e, query[:100])
            raise

    async def executemany(self, query: str, args_list: List[tuple]) -> None:
        """Execute query multiple times with different parameters"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(query, args_list)
                logger.debug("Executed query %d times | Query: %s...", len(args_list), query[:50])
        except Exception as e:
            logger.error("Error executing many: %s | Query: %s...", e, query[:100])
            raise

    @asynccontextmanager
    async def transaction(self):
        """Get a database transaction context manager for raw SQL"""
        if not self.is_connected or self.pool is None:
            raise RuntimeError("Database not connected")

        conn = await self.pool.acquire()
        transaction = None
        try:
            transaction = conn.transaction()
            await transaction.start()
            logger.debug("Database transaction started")
            yield conn
            await transaction.commit()
            logger.debug("Database transaction committed")
        except Exception:
            if transaction:
                await transaction.rollback()
                logger.debug("Database transaction rolled back")
            raise
        finally:
            await self.pool.release(conn)

    # SQLAlchemy ORM methods
    @asynccontextmanager
    async def get_session(self):
        """Get an SQLAlchemy async session"""
        if not self.is_connected or self.async_session_factory is None:
            raise RuntimeError("Database not connected or session factory not initialized")

        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_session_with_transaction(self):
        """Get an SQLAlchemy async session with automatic transaction management"""
        if not self.is_connected or self.async_session_factory is None:
            raise RuntimeError("Database not connected or session factory not initialized")

        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all tables defined in SQLAlchemy models"""
        if not self.is_connected or self.engine is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error("❌ Failed to create tables: %s", e)
            raise

    async def drop_tables(self) -> None:
        """Drop all tables defined in SQLAlchemy models"""
        if not self.is_connected or self.engine is None:
            raise RuntimeError("Database not connected")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("✅ Database tables dropped successfully")
        except Exception as e:
            logger.error("❌ Failed to drop tables: %s", e)
            raise


# Global database instance
db = Database()


# Dependency function for FastAPI or similar frameworks
async def get_database() -> Database:
    """Dependency function to get database instance"""
    return db


@asynccontextmanager
async def get_db_session():
    """Dependency function to get database session"""
    async with db.get_session() as session:
        yield session
