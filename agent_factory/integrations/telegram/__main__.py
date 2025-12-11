"""
Telegram bot entry point.

Run with: poetry run python -m agent_factory.integrations.telegram
"""

import asyncio
from .config import TelegramConfig
from .bot import TelegramBot


async def main():
    """Start the Telegram bot."""
    config = TelegramConfig.from_env()
    bot = TelegramBot(config)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
