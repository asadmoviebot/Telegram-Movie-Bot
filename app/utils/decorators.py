"""Reusable decorators for Telegram handlers: admin gating, ban checks, subscription gating."""
from __future__ import annotations

import asyncio
import functools
from typing import Awaitable, Callable

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.bot.keyboards import subscription_keyboard
from app.bot.locales import t
from app.config import settings
from app.logging_config import get_logger
from app.services.admin_service import ChannelService
from app.services.user_service import UserService

logger = get_logger(__name__)
user_service = UserService()
channel_service = ChannelService()

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def admin_only(func: Handler) -> Handler:
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None or not settings.is_admin(user.id):
            lang = _current_lang(update)
            if update.callback_query:
                await update.callback_query.answer(t("admin_only", lang), show_alert=True)
            elif update.message:
                await update.message.reply_text(t("admin_only", lang))
            return
        return await func(update, context)

    return wrapper


def registered_user(func: Handler) -> Handler:
    """Ensures a User row exists, is not banned, and required channels are joined."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg_user = update.effective_user
        if tg_user is None:
            return
        db_user = user_service.get_by_telegram_id(tg_user.id)
        if db_user is None:
            db_user = user_service.get_or_create(tg_user.id, tg_user.username, tg_user.full_name)
        lang = db_user.language

        if db_user.is_banned:
            if update.callback_query:
                await update.callback_query.answer(t("banned", lang), show_alert=True)
            elif update.message:
                await update.message.reply_text(t("banned", lang))
            return

        required = channel_service.list_required()
        if required and not settings.is_admin(tg_user.id):
            not_subscribed = await _missing_subscriptions(context, tg_user.id, required)
            if not_subscribed:
                markup = subscription_keyboard(required, lang)
                if update.callback_query:
                    await update.callback_query.answer()
                    await update.effective_chat.send_message(t("subscribe_required", lang), reply_markup=markup)
                elif update.message:
                    await update.message.reply_text(t("subscribe_required", lang), reply_markup=markup)
                return

        context.user_data["db_user"] = db_user
        return await func(update, context)

    return wrapper


async def _missing_subscriptions(context: ContextTypes.DEFAULT_TYPE, telegram_id: int, channels) -> bool:
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel.chat_id, user_id=telegram_id)
            if member.status in ("left", "kicked"):
                return True
        except TelegramError as exc:
            logger.warning("Could not verify subscription for channel %s: %s", channel.chat_id, exc)
            return True
    return False


def _current_lang(update: Update) -> str:
    tg_user = update.effective_user
    if tg_user is None:
        return settings.default_language
    db_user = user_service.get_by_telegram_id(tg_user.id)
    return db_user.language if db_user else settings.default_language


def run_blocking(func, *args, **kwargs):
    """Runs a blocking (sync) service call off the event loop."""
    return asyncio.to_thread(func, *args, **kwargs)
