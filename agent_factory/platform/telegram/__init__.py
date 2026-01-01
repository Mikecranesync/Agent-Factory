"""
Telegram Adapter for Factory.io Platform

Provides Telegram bot integration for real-time Factory.io monitoring and control.

Usage:
    from agent_factory.platform.telegram import TelegramAdapter
    from telegram import Bot

    bot = Bot(token="YOUR_BOT_TOKEN")
    adapter = TelegramAdapter(state_manager, bot, machine_config, ...)
    await adapter.start()
"""

from agent_factory.platform.telegram.telegram_adapter import TelegramAdapter, MessageTracker

__all__ = ["TelegramAdapter", "MessageTracker"]
