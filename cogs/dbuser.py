"""
testing cog for database user operations
"""

from datetime import date, datetime
from logging import getLogger
from typing import Optional

from discord import Interaction, User, app_commands
from discord.ext import commands

from database import UserService

logger = getLogger(__name__)

COG_METADATA = {
    "name": "DBUser",
    "is_cog": True,
    "enabled": True,
    "commands": {
        "adduser": {
            "help": "Add or update a user in the database",
            "aliases": [],
        },
    },
}


class DBUser(commands.Cog):
    """Cog for user database operations"""

    def __init__(self, bot):
        self.bot = bot
        logger.info("DBUser cog loaded")

    @app_commands.command(name="adduser", description=COG_METADATA["commands"]["adduser"]["help"])
    @app_commands.describe(
        user="Discord user to add/update (mention or leave blank for yourself)",
        nickname="User nickname",
        timezone="User timezone",
        birthday="User birthday (YYYY-MM-DD)",
    )
    async def adduser(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        interaction: Interaction,
        user: Optional[User] = None,
        nickname: Optional[str] = None,
        timezone: Optional[str] = None,
        birthday: Optional[str] = None,
    ):
        """Add or update a user in the database"""
        birthday_dt = None
        if birthday:
            try:
                birthday_obj = datetime.strptime(birthday, "%Y-%m-%d").date()
                if birthday_obj > date.today():
                    await interaction.response.send_message(
                        "❌ Invalid birthday: cannot be in the future.", ephemeral=True
                    )
                    return
                birthday_dt = datetime.combine(birthday_obj, datetime.min.time())
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid birthday format. Use YYYY-MM-DD.", ephemeral=True
                )
                return

        await interaction.response.defer()
        target_user = user or interaction.user
        user_id = target_user.id
        user_obj = await UserService.create_or_update_user(
            user_id=user_id,
            nickname=nickname,
            timezone=timezone,
            birthday=birthday_dt,
        )
        if user_obj:
            await interaction.followup.send(
                f"✅ User {user_id} added/updated (nickname: {user_obj.nickname})"
            )
        else:
            await interaction.followup.send(f"❌ Failed to add/update user {user_id}")


async def setup(bot):
    """Adds the DBUser cog"""
    cog = DBUser(bot)
    await bot.add_cog(cog)
