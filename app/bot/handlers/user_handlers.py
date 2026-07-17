"""Handlers for /start, language selection, profile and main menu navigation."""
from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from app.bot.keyboards import language_keyboard, main_menu_keyboard
from app.bot.locales import t
from app.config import settings
from app.logging_config import get_logger
from app.services.user_service import UserService
from app.utils.decorators import registered_user, run_blocking

logger = get_logger(__name__)
user_service = UserService()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    referral_code = context.args[0] if context.args else None
    db_user = await run_blocking(
        user_service.get_or_create, tg_user.id, tg_user.username, tg_user.full_name, referral_code
    )
    context.user_data["db_user"] = db_user
    await update.message.reply_text(
        t("welcome", db_user.language, name=tg_user.first_name or "friend"),
        reply_markup=main_menu_keyboard(db_user.language, settings.is_admin(tg_user.id)),
    )
    logger.info("User started bot: %s", tg_user.id)


@registered_user
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    text = t("main_menu", db_user.language)
    markup = main_menu_keyboard(db_user.language, settings.is_admin(update.effective_user.id))
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text(text, reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)


@registered_user
async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("choose_language", db_user.language), reply_markup=language_keyboard())


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    lang = query.data.split(":")[1]
    tg_user = update.effective_user
    await run_blocking(user_service.set_language, tg_user.id, lang)
    db_user = await run_blocking(user_service.get_by_telegram_id, tg_user.id)
    context.user_data["db_user"] = db_user
    await query.answer(t("language_saved", lang))
    await query.edit_message_text(
        t("main_menu", lang), reply_markup=main_menu_keyboard(lang, settings.is_admin(tg_user.id))
    )


@registered_user
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    referral_count = await run_blocking(user_service.referral_count, db_user.id)
    link = user_service.referral_link(db_user)
    premium_status = "✅" if db_user.is_premium else "❌"
    text = t(
        "profile_card",
        lang,
        name=db_user.full_name or db_user.username or "-",
        lang=lang.upper(),
        premium=premium_status,
        joined=db_user.created_at.strftime("%Y-%m-%d"),
        referrals=referral_count,
    )
    text += "\n\n" + t("referral_message", lang, link=link)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang, settings.is_admin(update.effective_user.id)), parse_mode="HTML")


@registered_user
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # registered_user already re-validated the subscription before reaching here.
    db_user = context.user_data["db_user"]
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        t("main_menu", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language, settings.is_admin(update.effective_user.id)),
    )


def register(application: Application) -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern=r"^menu:home$"))
    application.add_handler(CallbackQueryHandler(show_language_menu, pattern=r"^menu:language$"))
    application.add_handler(CallbackQueryHandler(set_language, pattern=r"^lang:"))
    application.add_handler(CallbackQueryHandler(show_profile, pattern=r"^menu:profile$"))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern=r"^check_subscription$"))
