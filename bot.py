# bot.py
"""Main bot entry point"""

from asyncio import CancelledError, run
from os import getenv

from dotenv import load_dotenv

from core.bot import CoreBot
from utils.logging_config import setup_logging

load_dotenv()


async def main():
    """Main bot runner"""
    # Setup logging before anything else
    logger = setup_logging()
    logger.info("Starting bot...")

    # Create bot instance
    bot = CoreBot()

    token = getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable is not set. Exiting.")
        return

    try:
        await bot.start(token)
    except CancelledError:
        print("Bot shutdown gracefully (CancelledError).")
    except KeyboardInterrupt:
        print("Bot interrupted by user (KeyboardInterrupt).")
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
