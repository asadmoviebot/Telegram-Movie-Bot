"""Registers every handler on the Application instance."""
from __future__ import annotations

from telegram.ext import Application

from app.bot.handlers import (
    admin_broadcast_handlers,
    admin_handlers,
    admin_system_handlers,
    movie_handlers,
    search_handlers,
    user_handlers,
)


def register_all(application: Application) -> None:
    user_handlers.register(application)
    search_handlers.register(application)
    movie_handlers.register(application)
    admin_handlers.register(application)
    admin_broadcast_handlers.register(application)
    admin_system_handlers.register(application)
