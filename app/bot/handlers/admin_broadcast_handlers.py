"""Admin handlers for broadcast messaging, premium management, users and bans."""
from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.keyboards import admin_back_keyboard, yes_no_keyboard
from app.bot.states import BroadcastStates
from app.logging_config import get_logger
from app.services.admin_service import BroadcastService
from app.services.user_service import UserService
from app.utils.decorators import admin_only, run_blocking

logger = get_logger(__name__)
broadcast_service = BroadcastService()
user_service = UserService()


# --------------------------------------------------------------- Broadcast

@admin_only
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Send the message you want to broadcast to all users:")
    return BroadcastStates.WAITING_TEXT


@admin_only
async def broadcast_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["broadcast_text"] = update.message.text
    await update.message.reply_text(
        f"Preview:\n\n{update.message.text}\n\nSend to all users?",
        reply_markup=yes_no_keyboard("admin:broadcast:send", "admin:broadcast:cancel"),
    )
    return BroadcastStates.CONFIRM


@admin_only
async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("Sending...")
    text = context.user_data.pop("broadcast_text", "")
    result = await broadcast_service.send_to_all(context.bot, text)
    await query.edit_message_text(f"✅ Broadcast finished.\nTotal: {result.total}\nSent: {result.sent}\nFailed: {result.failed}")
    return ConversationHandler.END


@admin_only
async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("broadcast_text", None)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Broadcast cancelled.")
    return ConversationHandler.END


# ---------------------------------------------------------------- Premium

@admin_only
async def open_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💎 Premium Management\nUse /grant <telegram_id> <days> to grant premium\n"
        "Use /grant <telegram_id> 0 for lifetime premium\nUse /revoke <telegram_id> to revoke it",
        reply_markup=admin_back_keyboard(),
    )


@admin_only
async def grant_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /grant <telegram_id> <days> (0 = lifetime)")
        return
    telegram_id, days_raw = int(context.args[0]), int(context.args[1])
    days = None if days_raw == 0 else days_raw
    user = await run_blocking(user_service.grant_premium, telegram_id, days)
    if user is None:
        await update.message.reply_text("User not found.")
        return
    await update.message.reply_text(f"✅ Premium granted to {telegram_id}.")


@admin_only
async def revoke_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /revoke <telegram_id>")
        return
    telegram_id = int(context.args[0])
    user = await run_blocking(user_service.revoke_premium, telegram_id)
    if user is None:
        await update.message.reply_text("User not found.")
        return
    await update.message.reply_text(f"✅ Premium revoked for {telegram_id}.")


# ------------------------------------------------------------------ Users

@admin_only
async def open_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = await run_blocking(user_service.list_all, 0, 15)
    lines = [
        f"{'🚫' if u.is_banned else '✅'} {u.telegram_id} — {u.full_name or u.username or '-'} "
        f"{'💎' if u.is_premium else ''}"
        for u in users
    ]
    text = "👥 Recent users:\n" + "\n".join(lines) if lines else "No users yet."
    text += "\n\nUse /ban <telegram_id> or /unban <telegram_id>\nUse /finduser <query> to search."
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text, reply_markup=admin_back_keyboard())


@admin_only
async def find_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /finduser <name or username>")
        return
    users = await run_blocking(user_service.search, " ".join(context.args))
    if not users:
        await update.message.reply_text("No users found.")
        return
    lines = [f"{u.telegram_id} — {u.full_name or '-'} (@{u.username or '-'})" for u in users]
    await update.message.reply_text("\n".join(lines))


@admin_only
async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /ban <telegram_id>")
        return
    user = await run_blocking(user_service.set_ban, int(context.args[0]), True)
    await update.message.reply_text("✅ User banned." if user else "User not found.")


@admin_only
async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /unban <telegram_id>")
        return
    user = await run_blocking(user_service.set_ban, int(context.args[0]), False)
    await update.message.reply_text("✅ User unbanned." if user else "User not found.")


def register(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(open_premium_menu, pattern=r"^admin:premium$"))
    application.add_handler(CallbackQueryHandler(open_users_menu, pattern=r"^admin:users$"))
    application.add_handler(CommandHandler("grant", grant_premium_command))
    application.add_handler(CommandHandler("revoke", revoke_premium_command))
    application.add_handler(CommandHandler("ban", ban_user_command))
    application.add_handler(CommandHandler("unban", unban_user_command))
    application.add_handler(CommandHandler("finduser", find_user_command))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_broadcast, pattern=r"^admin:broadcast$")],
            states={
                BroadcastStates.WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_preview)],
                BroadcastStates.CONFIRM: [
                    CallbackQueryHandler(broadcast_send, pattern=r"^admin:broadcast:send$"),
                    CallbackQueryHandler(broadcast_cancel, pattern=r"^admin:broadcast:cancel$"),
                ],
            },
            fallbacks=[CommandHandler("cancel", broadcast_cancel)],
            name="broadcast_conversation",
        )
    )
