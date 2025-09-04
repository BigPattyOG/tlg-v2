# database/services.py
"""
Database service layer for common operations
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select

from .connection import DatabaseResult, db
from .models import User

# TODO: add the rest of the impls # pylint: disable=fixme


class UserService:  # pylint: disable=too-few-public-methods
    """Service for user-related database operations"""

    @staticmethod
    async def create_or_update_user(
        user_id: int,
        nickname: Optional[str] = None,
        timezone: Optional[str] = None,
        birthday: Optional[datetime] = None,
    ) -> Optional[User]:
        """Create a new user or update existing one"""
        try:
            async with db.get_session() as session:

                if isinstance(session, DatabaseResult):
                    return None

                # Check if user exists
                result = await session.execute(select(User).where(User.user_id == user_id))
                user = result.scalar_one_or_none()

                if user:
                    # Update existing user
                    if nickname is not None:
                        user.nickname = nickname
                    if timezone is not None:
                        user.timezone = timezone
                    if birthday is not None:
                        user.birthday = birthday
                    user.updated_at = datetime.now()
                else:
                    # Create new user
                    user = User(
                        user_id=user_id,
                        nickname=nickname,
                        timezone=timezone,
                        birthday=birthday,
                    )
                    session.add(user)

                await session.commit()
                return user

        except Exception as e:  # pylint: disable=broad-except
            # TODO: handle this  # pylint: disable=fixme
            print(f"Error in create_or_update_user: {e}")
            return None
