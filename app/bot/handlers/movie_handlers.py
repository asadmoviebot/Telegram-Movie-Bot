"""Handlers for movie detail view, watching, favorites, ratings and comments."""
from __future__ import annotations

from telegram import InputMediaPhoto, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.keyboards import movie_detail_keyboard, rating_keyboard
from app.bot.locales import t
from app.bot.states import CommentStates
from app.logging_config import get_logger
from app.services.interaction_service import CommentService, RatingService
from app.services.movie_service import MovieService
from app.services.user_service import FavoriteService
from app.utils.decorators import registered_user, run_blocking
from app.utils.helpers import format_movie_card

logger = get_logger(__name__)
movie_service = MovieService()
favorite_service = FavoriteService()
rating_service = RatingService()
comment_service = CommentService()


async def send_movie_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_id: int, edit: bool) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    movie = await run_blocking(movie_service.get_by_id, movie_id)
    query = update.callback_query
    if movie is None:
        text = t("not_found", lang)
        if query:
            await query.answer()
            await query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)
        return

    is_fav = await run_blocking(favorite_service.is_favorite, db_user.id, movie.id)
    caption = format_movie_card(movie, lang)
    markup = movie_detail_keyboard(movie, lang, is_fav, back_target="menu:home")

    if query:
        await query.answer()

    if movie.poster_file_id:
        chat = update.effective_chat
        await chat.send_photo(photo=movie.poster_file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
    else:
        target = update.effective_message
        await target.reply_text(caption, reply_markup=markup, parse_mode="HTML")


@registered_user
async def open_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    movie_id = int(update.callback_query.data.split(":")[1])
    await send_movie_detail(update, context, movie_id, edit=True)


@registered_user
async def watch_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    movie_id = int(update.callback_query.data.split(":")[1])
    query = update.callback_query

    movie = await run_blocking(movie_service.get_by_id, movie_id)
    if movie is None:
        await query.answer(t("not_found", lang), show_alert=True)
        return
    if movie.is_premium and not db_user.is_premium:
        await query.answer(t("premium_locked", lang), show_alert=True)
        return

    await query.answer()
    await run_blocking(movie_service.watch, movie_id, db_user.id)
    await update.effective_chat.send_video(
        video=movie.file_id, caption=f"🎬 {movie.title} ({movie.year})", supports_streaming=True
    )


@registered_user
async def toggle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    movie_id = int(update.callback_query.data.split(":")[1])
    query = update.callback_query
    now_favorite = await run_blocking(favorite_service.toggle, db_user.id, movie_id)
    await query.answer(t("added_favorite", lang) if now_favorite else t("removed_favorite", lang))

    movie = await run_blocking(movie_service.get_by_id, movie_id)
    if movie is None:
        return
    markup = movie_detail_keyboard(movie, lang, now_favorite, back_target="menu:home")
    try:
        await query.edit_message_reply_markup(reply_markup=markup)
    except BadRequest:
        pass


@registered_user
async def start_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    movie_id = int(update.callback_query.data.split(":")[1])
    query = update.callback_query
    await query.answer()
    await update.effective_chat.send_message(t("ask_rating", db_user.language), reply_markup=rating_keyboard(movie_id))


@registered_user
async def save_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    _, movie_id, score = update.callback_query.data.split(":")
    query = update.callback_query
    await run_blocking(rating_service.rate, db_user.id, int(movie_id), int(score))
    await query.answer(t("rating_saved", db_user.language), show_alert=True)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except BadRequest:
        pass


@registered_user
async def start_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = context.user_data["db_user"]
    movie_id = int(update.callback_query.data.split(":")[1])
    context.user_data["comment_movie_id"] = movie_id
    query = update.callback_query
    await query.answer()
    await update.effective_chat.send_message(t("ask_comment", db_user.language))
    return CommentStates.WAITING_TEXT


@registered_user
async def save_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = context.user_data["db_user"]
    movie_id = context.user_data.get("comment_movie_id")
    if movie_id is None:
        return ConversationHandler.END
    await run_blocking(comment_service.add, db_user.id, movie_id, update.message.text)
    await update.message.reply_text(t("comment_saved", db_user.language))
    return ConversationHandler.END


@registered_user
async def view_comments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    _, movie_id, page = update.callback_query.data.split(":")
    pairs = await run_blocking(comment_service.list_for_movie, int(movie_id), int(page), 5)
    query = update.callback_query
    await query.answer()
    if not pairs:
        await update.effective_chat.send_message(t("empty_list", lang))
        return
    lines = [f"👤 <b>{u.full_name or u.username or 'User'}</b>: {c.text}" for c, u in pairs]
    await update.effective_chat.send_message("\n\n".join(lines), parse_mode="HTML")


async def cancel_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(t("cancelled", "en"))
    return ConversationHandler.END


def register(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(open_movie, pattern=r"^movie:\d+$"))
    application.add_handler(CallbackQueryHandler(watch_movie, pattern=r"^watch:\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_favorite, pattern=r"^fav:\d+$"))
    application.add_handler(CallbackQueryHandler(start_rating, pattern=r"^rate:\d+$"))
    application.add_handler(CallbackQueryHandler(save_rating, pattern=r"^ratesave:\d+:\d+$"))
    application.add_handler(CallbackQueryHandler(view_comments, pattern=r"^comments:\d+:\d+$"))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_comment, pattern=r"^comment:\d+$")],
            states={CommentStates.WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_comment)]},
            fallbacks=[CommandHandler("cancel", cancel_comment)],
            name="comment_conversation",
        )
    )
