# database/models.py
# pylint: disable=too-few-public-methods
# SQLAlchemy ORM models typically only define attributes, not public methods.
"""
Database models/schemas for the Discord bot
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Cog(Base):
    """Cogs management table"""

    __tablename__ = "cogs"

    # Primary key - using the module name as PK
    cog_module: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Cog configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


class User(Base):
    """Users table for Discord users"""

    __tablename__ = "users"

    # Primary key - Discord user ID
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # User information
    nickname: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # IANA timezone
    birthday: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Game currency and progression
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Moderation
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps - using UTC timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class Game(Base):
    """Games table for different bot games/features"""

    __tablename__ = "games"

    # Primary key
    game_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Game information
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Event(Base):
    """Events table for bot events/activities"""

    __tablename__ = "events"

    # Primary key
    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Event details
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scheduling - using timezone-aware timestamps
    start_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Event data and tracking
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # Status options: 'pending', 'active', 'completed', 'cancelled'


class EventLog(Base):
    """Event logs for tracking event activities"""

    __tablename__ = "event_logs"

    # Primary key
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign keys
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.event_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Log data
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp - timezone aware
    logged_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )


class Profile(Base):
    """User profiles for different games"""

    __tablename__ = "profiles"

    __table_args__ = (Index("idx_profiles_user_id", "user_id"),)

    # Primary key
    profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.game_id"), nullable=False)

    # Profile details
    profile_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Game-specific data

    # Timestamps - timezone aware
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class BotRole(Base):
    """Bot roles for permission management"""

    __tablename__ = "bot_roles"

    # Primary key
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Role information
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Permission bitmask
    bit_value: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CommandUsage(Base):
    """Command usage tracking"""

    __tablename__ = "command_usage"

    # Primary key
    usage_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Command details
    command_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp - timezone aware
    executed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )


class Achievement(Base):
    """Achievements that users can unlock"""

    __tablename__ = "achievements"

    # Primary key
    achievement_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Achievement details
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Achievement properties
    rarity: Mapped[str] = mapped_column(String(20), default="common", nullable=False)
    # Rarity options: 'common', 'uncommon', 'rare', 'epic', 'legendary'

    # Rewards
    coin_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    icon_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Hidden until unlocked

    # Timestamps - timezone aware
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )


class UserAchievement(Base):
    """Junction table for user achievements"""

    __tablename__ = "user_achievements"

    __table_args__ = (Index("idx_user_achievements_user", "user_id"),)

    # Composite primary key
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    achievement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("achievements.achievement_id"), primary_key=True
    )

    # Achievement unlock details
    progress: Mapped[float] = mapped_column(
        Integer, default=100, nullable=False
    )  # Percentage of completion

    # Timestamp - timezone aware
    unlocked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Optional metadata for how it was achieved
    unlock_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
