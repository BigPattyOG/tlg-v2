# database/connection.py
"""
Main database connection handler
"""

from asyncio import Lock
from asyncio import TimeoutError as asyncioTimeoutError
from asyncio import get_event_loop, sleep, timeout
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger
from re import sub
from typing import Any, List, Optional

from asyncpg import Pool, PostgresError, create_pool
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


class DatabaseState(Enum):
    """Database connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class DatabaseResult:
    """Wrapper for database operation results"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0

    @property
    def failed(self) -> bool:
        """Check if the database operation failed"""
        return not self.success


@dataclass
class ConnectionMetrics:
    """Database connection metrics for monitoring"""

    total_queries: int = 0
    failed_queries: int = 0
    total_reconnections: int = 0
    last_connection_time: Optional[datetime] = None
    average_query_time: float = 0.0


class Database:  # pylint: disable=too-many-instance-attributes
    """Future-proof PostgreSQL database connection manager"""

    def __init__(
        self,
        auto_reconnect: bool = True,
        max_retry_attempts: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 30,
    ):
        self.pool: Optional[Pool] = None
        self.engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._state = DatabaseState.DISCONNECTED
        self._connection_lock = Lock()

        # Configuration
        self.auto_reconnect = auto_reconnect
        self.max_retry_attempts = max_retry_attempts
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # Circuit breaker state
        self._circuit_failures = 0
        self._circuit_last_failure: Optional[datetime] = None
        self._circuit_open = False

        # Metrics
        self.metrics = ConnectionMetrics()

    def _update_metrics(self, success: bool, execution_time: float = 0) -> None:
        """Update connection metrics"""
        self.metrics.total_queries += 1
        if not success:
            self.metrics.failed_queries += 1

        # Update rolling average
        if self.metrics.total_queries == 1:
            self.metrics.average_query_time = execution_time
        else:
            self.metrics.average_query_time = (
                self.metrics.average_query_time * (self.metrics.total_queries - 1) + execution_time
            ) / self.metrics.total_queries

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self._circuit_open:
            return False

        if self._circuit_last_failure is None:
            return False

        # Check if timeout has passed
        if datetime.now() - self._circuit_last_failure > timedelta(
            seconds=self.circuit_breaker_timeout
        ):
            self._circuit_open = False
            self._circuit_failures = 0
            logger.info("Circuit breaker reset - attempting reconnection")
            return False

        return True

    def _record_circuit_failure(self) -> None:
        """Record a failure for circuit breaker"""
        self._circuit_failures += 1
        self._circuit_last_failure = datetime.now()

        if self._circuit_failures >= self.circuit_breaker_threshold:
            self._circuit_open = True
            logger.warning(
                "Circuit breaker opened after %d failures - will retry in %d seconds",
                self._circuit_failures,
                self.circuit_breaker_timeout,
            )

    async def _ensure_connected(self) -> DatabaseResult:
        """Ensure database is connected with circuit breaker protection"""
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            return DatabaseResult(
                success=False, error="Circuit breaker open - database temporarily unavailable"
            )

        if self._state == DatabaseState.CONNECTED:
            return DatabaseResult(success=True)

        if not self.auto_reconnect:
            return DatabaseResult(
                success=False, error="Database not connected and auto-reconnect disabled"
            )

        async with self._connection_lock:
            # Double-check after acquiring lock
            if self._state == DatabaseState.CONNECTED:
                return DatabaseResult(success=True)

            logger.warning("Database not connected, attempting reconnection...")

            try:
                await self.connect()
                self._circuit_failures = 0  # Reset on successful connection
                return DatabaseResult(success=True)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._record_circuit_failure()
                error_msg = f"Failed to reconnect to database: {e}"
                logger.error(error_msg)
                self._state = DatabaseState.ERROR
                return DatabaseResult(success=False, error=error_msg)

    async def _retry_operation(  # pylint: disable=too-many-locals
        self, operation, *args, **kwargs
    ) -> DatabaseResult:
        """Retry database operations with comprehensive error handling"""
        start_time = get_event_loop().time()

        for attempt in range(self.max_retry_attempts):
            try:
                # Ensure connection before each attempt
                conn_result = await self._ensure_connected()
                if conn_result.failed:
                    return conn_result

                operation_start = get_event_loop().time()
                result = await operation(*args, **kwargs)
                execution_time = get_event_loop().time() - operation_start

                total_time = get_event_loop().time() - start_time
                self._update_metrics(True, execution_time)

                return DatabaseResult(
                    success=True, data=result, execution_time=total_time, retry_count=attempt
                )

            except (PostgresError, ConnectionError, OSError) as e:
                # These are retryable errors
                logger.warning("Database operation failed (attempt %d): %s", attempt + 1, e)

                if attempt == self.max_retry_attempts - 1:
                    # Final attempt failed
                    total_time = get_event_loop().time() - start_time
                    error_msg = (
                        f"Database operation failed after {self.max_retry_attempts} attempts: {e}"
                    )
                    logger.error(error_msg)

                    self._update_metrics(False, total_time)

                    return DatabaseResult(
                        success=False,
                        error=error_msg,
                        execution_time=total_time,
                        retry_count=attempt + 1,
                    )

                # Wait before retry with jittered exponential backoff
                base_wait = 2**attempt
                jitter = base_wait * 0.1 * (get_event_loop().time() % 1)
                wait_time = base_wait + jitter
                await sleep(min(wait_time, 10))  # Cap at 10 seconds

                # Mark as disconnected to trigger reconnection
                self._state = DatabaseState.DISCONNECTED

            except Exception as e:  # pylint: disable=broad-exception-caught
                # Non-retryable errors
                total_time = get_event_loop().time() - start_time
                error_msg = f"Non-retryable database error: {e}"
                logger.error(error_msg)

                self._update_metrics(False, total_time)

                return DatabaseResult(
                    success=False,
                    error=error_msg,
                    execution_time=total_time,
                    retry_count=attempt + 1,
                )

        return DatabaseResult(success=False, error="Unexpected retry loop exit")

    async def connect(self) -> None:
        """Establish connection pool and SQLAlchemy engine"""
        settings = get_settings()

        if not settings.database_url:
            logger.error("DATABASE_URL not found in environment variables")
            raise ValueError("DATABASE_URL is required")

        try:
            logger.info("Connecting to PostgreSQL database...")
            self._state = DatabaseState.CONNECTING

            self.pool = await create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                server_settings={"jit": "off"},
            )

            # Remove sslmode from SQLAlchemy connection string if present
            sqlalchemy_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
            if "sslmode=" in sqlalchemy_url:
                sqlalchemy_url = sub(r"(\?|&)sslmode=[^&]+", "", sqlalchemy_url)
                sqlalchemy_url = sub(r"\?$", "", sqlalchemy_url)

            self.engine = create_async_engine(
                sqlalchemy_url,
                echo=False,
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

            self._state = DatabaseState.CONNECTED
            self.metrics.last_connection_time = datetime.now()
            self.metrics.total_reconnections += 1

            logger.info("✅ Database connection pool and SQLAlchemy engine established")

            # Test connections
            await self.test_connection()

        except Exception as e:
            self._state = DatabaseState.ERROR
            logger.error("❌ Failed to connect to database: %s", e)
            raise

    async def disconnect(self) -> None:
        """Close database connection pool and SQLAlchemy engine"""
        async with self._connection_lock:
            if self.engine:
                logger.info("Closing SQLAlchemy engine...")
                await self.engine.dispose()
                self.engine = None
                self.async_session_factory = None

            if self.pool:
                logger.info("Closing database connection pool...")
                await self.pool.close()
                self.pool = None

            self._state = DatabaseState.DISCONNECTED
            logger.info("✅ Database connections closed")

    async def test_connection(self) -> bool:
        """Test database connections with timeout"""
        try:
            async with timeout(10):
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
                            logger.warning(
                                "⚠️ SQLAlchemy connection test returned unexpected result"
                            )
                            return False

                return True
        except asyncioTimeoutError:
            logger.error("❌ Database connection test timed out")
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("❌ Database connection test failed: %s", e)
            return False

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return (
            self._state == DatabaseState.CONNECTED
            and self.pool is not None
            and self.engine is not None
        )

    @property
    def connection_state(self) -> DatabaseState:
        """Get current connection state"""
        return self._state

    # Database operation methods
    async def execute(self, query: str, *args) -> DatabaseResult:
        """Execute a query that doesn't return data (INSERT, UPDATE, DELETE)"""

        async def _execute():
            if self.pool is None:
                return DatabaseResult(success=False, error="Connection pool not available")
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *args)
                logger.debug("Executed query: %s... | Result: %s", query[:50], result)
                return result

        return await self._retry_operation(_execute)

    async def fetch(self, query: str, *args) -> DatabaseResult:
        """Fetch multiple rows from database"""

        async def _fetch():
            if self.pool is None:
                return DatabaseResult(success=False, error="Connection pool not available")
            async with self.pool.acquire() as conn:
                result = await conn.fetch(query, *args)
                logger.debug("Fetched %d rows | Query: %s...", len(result), query[:50])
                return result

        return await self._retry_operation(_fetch)

    async def fetchrow(self, query: str, *args) -> DatabaseResult:
        """Fetch single row from database"""

        async def _fetchrow():
            if self.pool is None:
                return DatabaseResult(success=False, error="Connection pool not available")
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(query, *args)
                logger.debug("Fetched single row | Query: %s...", query[:50])
                return result

        return await self._retry_operation(_fetchrow)

    async def fetchval(self, query: str, *args) -> DatabaseResult:
        """Fetch single value from database"""

        async def _fetchval():
            if self.pool is None:
                return DatabaseResult(success=False, error="Connection pool not available")
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(query, *args)
                logger.debug("Fetched single value | Query: %s...", query[:50])
                return result

        return await self._retry_operation(_fetchval)

    async def executemany(self, query: str, args_list: List[tuple]) -> DatabaseResult:
        """Execute query multiple times with different parameters"""

        async def _executemany():
            if self.pool is None:
                return DatabaseResult(success=False, error="Connection pool not available")
            async with self.pool.acquire() as conn:
                await conn.executemany(query, args_list)
                logger.debug("Executed query %d times | Query: %s...", len(args_list), query[:50])

        return await self._retry_operation(_executemany)

    @asynccontextmanager
    async def transaction(self):
        """Get a database transaction context manager for raw SQL"""
        conn_result = await self._ensure_connected()
        if conn_result.failed:
            yield DatabaseResult(
                success=False, error=conn_result.error or "Failed to establish connection"
            )
            return

        if self.pool is None:
            yield DatabaseResult(success=False, error="Connection pool not available")
            return

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
        conn_result = await self._ensure_connected()
        if conn_result.failed:
            yield DatabaseResult(
                success=False, error=conn_result.error or "Failed to establish connection"
            )
            return

        if self.async_session_factory is None:
            yield DatabaseResult(success=False, error="Session factory not initialized")
            return

        session = None
        try:
            session = self.async_session_factory()
            yield session
            await session.commit()
        except Exception:
            if session:
                await session.rollback()
            raise
        finally:
            if session:
                await session.close()

    @asynccontextmanager
    async def get_session_with_transaction(self):
        """Get an SQLAlchemy async session with automatic transaction management"""
        async with self.get_session() as session:
            if isinstance(session, DatabaseResult):
                yield session
                return
            try:
                async with session.begin():
                    yield session
            except Exception:
                await session.rollback()
                raise

    # Health check method
    async def health_check(self) -> DatabaseResult:
        """Perform a comprehensive health check with detailed diagnostics"""
        try:
            if self._state != DatabaseState.CONNECTED:
                return DatabaseResult(
                    success=False, error=f"Database not connected (state: {self._state.value})"
                )

            # Test basic connectivity with timeout
            try:
                async with timeout(5):
                    test_result = await self.test_connection()
                    if not test_result:
                        return DatabaseResult(success=False, error="Connection test failed")
            except asyncioTimeoutError:
                return DatabaseResult(success=False, error="Health check timed out")

            # Get health information
            health_info = {
                "state": self._state.value,
                "circuit_breaker_open": self._circuit_open,
                "total_queries": self.metrics.total_queries,
                "failed_queries": self.metrics.failed_queries,
                "success_rate": (
                    (self.metrics.total_queries - self.metrics.failed_queries)
                    / self.metrics.total_queries
                    * 100
                    if self.metrics.total_queries > 0
                    else 100
                ),
                "average_query_time": self.metrics.average_query_time,
            }

            return DatabaseResult(success=True, data=health_info)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return DatabaseResult(success=False, error=f"Health check failed: {e}")

    async def create_tables(self) -> DatabaseResult:
        """Create all tables defined in SQLAlchemy models"""
        conn_result = await self._ensure_connected()
        if conn_result.failed:
            return DatabaseResult(
                success=False, error=conn_result.error or "Failed to establish connection"
            )

        if self.engine is None:
            return DatabaseResult(success=False, error="Engine not available")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
            return DatabaseResult(success=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("❌ Failed to create tables: %s", e)
            return DatabaseResult(success=False, error=f"Failed to create tables: {e}")

    async def drop_tables(self) -> DatabaseResult:
        """Drop all tables defined in SQLAlchemy models"""
        conn_result = await self._ensure_connected()
        if conn_result.failed:
            return DatabaseResult(
                success=False, error=conn_result.error or "Failed to establish connection"
            )

        if self.engine is None:
            return DatabaseResult(success=False, error="Engine not available")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("✅ Database tables dropped successfully")
            return DatabaseResult(success=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("❌ Failed to drop tables: %s", e)
            return DatabaseResult(success=False, error=f"Failed to drop tables: {e}")


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
