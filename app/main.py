"""Application entrypoint: python -m app.main"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from app.bot.handlers import register_all
from app.config import settings
from app.database.session import init_db
from app.logging_config import configure_logging, get_logger
from scheduler.jobs import build_scheduler

logger = get_logger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception while processing update: %s", context.error, exc_info=context.error)


async def on_startup(application: Application) -> None:
    scheduler = build_scheduler()
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logger.info("Scheduler started")


async def on_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler:
        scheduler.shutdown(wait=False)


def main() -> None:
    configure_logging()
    logger.info("Starting Telegram Movie Platform...")

    init_db()
    logger.info("Database ready")

    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    register_all(application)
    application.add_error_handler(on_error)

    logger.info("Bot is polling for updates")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
