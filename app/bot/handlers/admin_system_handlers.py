"""Admin handlers for statistics, backup/restore, export, logs, ads, channels and referrals."""
from __future__ import annotations

import io

from telegram import InputFile, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.keyboards import admin_back_keyboard, ads_admin_keyboard, channels_admin_keyboard
from app.bot.states import AdvertisementAdminStates, ChannelAdminStates, RestoreStates
from app.config import settings
from app.logging_config import get_logger
from app.services.admin_service import AdvertisementService, BackupService, ChannelService, StatisticsService
from app.services.user_service import UserService
from app.utils.decorators import admin_only, run_blocking

logger = get_logger(__name__)
stats_service = StatisticsService()
backup_service = BackupService()
ads_service = AdvertisementService()
channel_service = ChannelService()
user_service = UserService()


# ------------------------------------------------------------- Statistics

@admin_only
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await run_blocking(stats_service.snapshot)
    text = (
        "📊 <b>Statistics</b>\n\n"
        f"👥 Users: {data['total_users']}\n"
        f"💎 Premium: {data['premium_users']}\n"
        f"🚫 Banned: {data['banned_users']}\n"
        f"🎬 Movies: {data['total_movies']}\n"
        f"🗂 Categories: {data['total_categories']}\n"
        f"🎭 Genres: {data['total_genres']}"
    )
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())


@admin_only
async def show_referral_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    top = await run_blocking(user_service.top_referrers, 10)
    if not top:
        text = "No referrals yet."
    else:
        lines = [f"{i+1}. {u.full_name or u.username or u.telegram_id} — {count} invites" for i, (u, count) in enumerate(top)]
        text = "🔗 <b>Top Referrers</b>\n\n" + "\n".join(lines)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())


# ------------------------------------------------------------------ Backup

@admin_only
async def do_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Creating backup...")
    try:
        path = await run_blocking(backup_service.create_backup)
    except RuntimeError as exc:
        await query.edit_message_text(str(exc), reply_markup=admin_back_keyboard())
        return
    await update.effective_chat.send_document(document=InputFile(open(path, "rb"), filename=path.name))
    await query.edit_message_text("✅ Backup created and sent above.", reply_markup=admin_back_keyboard())


@admin_only
async def start_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Send the .db backup file to restore (this overwrites the current database):")
    return RestoreStates.WAITING_FILE


@admin_only
async def restore_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if document is None:
        await update.message.reply_text("Please send a valid .db file.")
        return RestoreStates.WAITING_FILE
    tg_file = await document.get_file()
    dest = settings.backup_dir / f"restore_upload_{document.file_unique_id}.db"
    await tg_file.download_to_drive(custom_path=str(dest))
    await run_blocking(backup_service.restore_backup, dest)
    await update.message.reply_text("✅ Database restored. Please restart the bot for changes to fully apply.")
    return ConversationHandler.END


# ------------------------------------------------------------------ Export

@admin_only
async def do_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Preparing export...")
    payload = await run_blocking(stats_service.export_csv)
    await update.effective_chat.send_document(document=InputFile(io.BytesIO(payload), filename="movies_export.csv"))
    await query.edit_message_text("✅ Export sent above.", reply_markup=admin_back_keyboard())


# -------------------------------------------------------------------- Logs

@admin_only
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log_path = settings.log_dir / "bot.log"
    query = update.callback_query
    await query.answer()
    if not log_path.exists():
        await query.edit_message_text("No logs yet.", reply_markup=admin_back_keyboard())
        return
    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-30:]
    text = "📄 Last 30 log lines:\n\n" + "\n".join(lines) if lines else "Log file is empty."
    if len(text) > 3800:
        await update.effective_chat.send_document(document=InputFile(io.BytesIO(text.encode("utf-8")), filename="bot.log"))
        text = "📄 Log file attached above (too long to show inline)."
    await query.edit_message_text(text, reply_markup=admin_back_keyboard())


# -------------------------------------------------------------- Advertisements

@admin_only
async def open_ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ads = await run_blocking(ads_service.list_all)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📣 Advertisements", reply_markup=ads_admin_keyboard(ads))


@admin_only
async def start_add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the advertisement text:")
    return AdvertisementAdminStates.TEXT


async def ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ad_text"] = update.message.text
    await update.message.reply_text("Enter a button label, or /skip:")
    return AdvertisementAdminStates.BUTTON_TEXT


async def ad_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ad_button_text"] = update.message.text.strip()
    await update.message.reply_text("Enter the button URL:")
    return AdvertisementAdminStates.BUTTON_URL


async def ad_skip_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ad_button_text"] = None
    context.user_data["ad_button_url"] = None
    return await _save_ad(update, context)


async def ad_button_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ad_button_url"] = update.message.text.strip()
    return await _save_ad(update, context)


async def _save_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await run_blocking(
        ads_service.create,
        context.user_data.pop("ad_text"),
        context.user_data.pop("ad_button_text", None),
        context.user_data.pop("ad_button_url", None),
    )
    await update.message.reply_text("✅ Advertisement created.")
    ads = await run_blocking(ads_service.list_all)
    await update.message.reply_text("📣 Advertisements", reply_markup=ads_admin_keyboard(ads))
    return ConversationHandler.END


@admin_only
async def toggle_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ad_id = int(update.callback_query.data.split(":")[-1])
    await run_blocking(ads_service.toggle, ad_id)
    ads = await run_blocking(ads_service.list_all)
    query = update.callback_query
    await query.answer("Updated.")
    await query.edit_message_text("📣 Advertisements", reply_markup=ads_admin_keyboard(ads))


@admin_only
async def delete_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ad_id = int(update.callback_query.data.split(":")[-1])
    await run_blocking(ads_service.delete, ad_id)
    ads = await run_blocking(ads_service.list_all)
    query = update.callback_query
    await query.answer("Deleted.")
    await query.edit_message_text("📣 Advertisements", reply_markup=ads_admin_keyboard(ads))


# ------------------------------------------------------------------ Channels

@admin_only
async def open_channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    channels = await run_blocking(channel_service.list_all)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📡 Required Channels (users must join to use the bot)", reply_markup=channels_admin_keyboard(channels)
    )


@admin_only
async def start_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Add the bot as admin to your channel, then send its numeric chat ID "
        "(e.g. -1001234567890). You can get it by forwarding a channel post to @userinfobot."
    )
    return ChannelAdminStates.WAITING_FORWARD


async def add_channel_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        chat_id = int(text)
    except ValueError:
        await update.message.reply_text("Please send a valid numeric chat ID, e.g. -1001234567890.")
        return ChannelAdminStates.WAITING_FORWARD
    try:
        chat = await context.bot.get_chat(chat_id)
        title = chat.title or str(chat_id)
        username = chat.username
    except Exception:
        title = str(chat_id)
        username = None
    await run_blocking(channel_service.add, chat_id, username, title)
    await update.message.reply_text(f"✅ Channel '{title}' added as required.")
    return ConversationHandler.END


@admin_only
async def delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    channel_id = int(update.callback_query.data.split(":")[-1])
    await run_blocking(channel_service.delete, channel_id)
    channels = await run_blocking(channel_service.list_all)
    query = update.callback_query
    await query.answer("Removed.")
    await query.edit_message_text("📡 Required Channels", reply_markup=channels_admin_keyboard(channels))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def register(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(show_stats, pattern=r"^admin:stats$"))
    application.add_handler(CallbackQueryHandler(show_referral_stats, pattern=r"^admin:referrals$"))
    application.add_handler(CallbackQueryHandler(do_backup, pattern=r"^admin:backup$"))
    application.add_handler(CallbackQueryHandler(do_export, pattern=r"^admin:export$"))
    application.add_handler(CallbackQueryHandler(show_logs, pattern=r"^admin:logs$"))
    application.add_handler(CallbackQueryHandler(open_ads_menu, pattern=r"^admin:ads$"))
    application.add_handler(CallbackQueryHandler(toggle_ad, pattern=r"^admin:ad:toggle:\d+$"))
    application.add_handler(CallbackQueryHandler(delete_ad, pattern=r"^admin:ad:del:\d+$"))
    application.add_handler(CallbackQueryHandler(open_channels_menu, pattern=r"^admin:channels$"))
    application.add_handler(CallbackQueryHandler(delete_channel, pattern=r"^admin:channel:del:\d+$"))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_restore, pattern=r"^admin:restore$")],
            states={RestoreStates.WAITING_FILE: [MessageHandler(filters.Document.ALL, restore_receive_file)]},
            fallbacks=[CommandHandler("cancel", cancel)],
            name="restore_conversation",
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_add_ad, pattern=r"^admin:ad:add$")],
            states={
                AdvertisementAdminStates.TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_text)],
                AdvertisementAdminStates.BUTTON_TEXT: [
                    CommandHandler("skip", ad_skip_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, ad_button_text),
                ],
                AdvertisementAdminStates.BUTTON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_button_url)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            name="add_ad_conversation",
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_add_channel, pattern=r"^admin:channel:add$")],
            states={ChannelAdminStates.WAITING_FORWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_receive)]},
            fallbacks=[CommandHandler("cancel", cancel)],
            name="add_channel_conversation",
        )
    )
