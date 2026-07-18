"""Handlers for search, code search, categories, genres, top/latest/random and pagination."""
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

from app.bot.keyboards import categories_keyboard, genres_keyboard, movie_list_keyboard
from app.bot.locales import t
from app.bot.states import SearchStates
from app.services.movie_service import CategoryService, GenreService, MovieService
from app.services.user_service import FavoriteService, HistoryService
from app.utils.decorators import registered_user, run_blocking
from app.utils.helpers import PAGE_SIZE, paginate

movie_service = MovieService()
category_service = CategoryService()
genre_service = GenreService()
favorite_service = FavoriteService()
history_service = HistoryService()

LIST_TITLES = {
    "top": "btn_top",
    "latest": "btn_latest",
    "favorites": "btn_favorites",
    "history": "btn_history",
    "recommend": "btn_recommend",
    "search": None,
}

async def _fetch_movies(list_type: str, param: str, user_id: int) -> list:
    if list_type == "top":
        return await run_blocking(movie_service.top_rated, 200)
    if list_type == "latest":
        return await run_blocking(movie_service.latest, 200)
    if list_type == "favorites":
        return await run_blocking(favorite_service.list_for_user, user_id, 0, 500)
    if list_type == "history":
        return await run_blocking(history_service.list_for_user, user_id, 0, 500)
    if list_type == "recommend":
        return await run_blocking(movie_service.recommend_for_user, user_id, 30)
    if list_type == "category":
        return await run_blocking(movie_service.list_by_category, int(param), 0, 500)
    if list_type == "genre":
        return await run_blocking(movie_service.list_by_genre, int(param), 0, 500)
    if list_type == "search":
        return await run_blocking(movie_service.search, param)
    return []


async def send_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE, list_type: str, param: str, page: int) -> None:
    db_user = context.user_data["db_user"]
    lang = db_user.language
    movies = await _fetch_movies(list_type, param, db_user.id)
    chunk, has_next = paginate(movies, page, PAGE_SIZE)

    query = update.callback_query
    if not chunk:
        text = t("empty_list", lang) if movies == [] else t("not_found", lang)
        if query:
            await query.answer()
            await query.edit_message_text(text, reply_markup=movie_list_keyboard([], lang, f"list:{list_type}:{param}", page, False))
        else:
            await update.effective_message.reply_text(text)
        return

    title_key = LIST_TITLES.get(list_type)
    title = t(title_key, lang) if title_key else t("btn_search", lang)
    markup = movie_list_keyboard(chunk, lang, f"list:{list_type}:{param}", page, has_next)
    if query:
        await query.answer()
        try:
            await query.edit_message_text(title, reply_markup=markup)
        except Exception:
            await query.message.reply_text(title, reply_markup=markup)
    else:
        await update.effective_message.reply_text(title, reply_markup=markup)


@registered_user
async def handle_list_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # callback_data format: list:<type>:<param>:page:<n>
    parts = update.callback_query.data.split(":")
    list_type, param, _, page = parts[1], parts[2], parts[3], int(parts[4])
    await send_movie_list(update, context, list_type, param, page)


@registered_user
async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_movie_list(update, context, "top", "", 0)


@registered_user
async def show_latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_movie_list(update, context, "latest", "", 0)


@registered_user
async def show_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_movie_list(update, context, "recommend", "", 0)


@registered_user
async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_movie_list(update, context, "favorites", "", 0)


@registered_user
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_movie_list(update, context, "history", "", 0)


@registered_user
async def show_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    movie = await run_blocking(movie_service.random_movie)
    query = update.callback_query
    await query.answer()
    if movie is None:
        await query.edit_message_text(t("not_found", db_user.language))
        return
    from app.bot.handlers.movie_handlers import send_movie_detail

    await send_movie_detail(update, context, movie.id, edit=True)


@registered_user
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    categories = await run_blocking(category_service.list_all)
    query = update.callback_query
    await query.answer()
    if not categories:
        await query.edit_message_text(t("empty_list", db_user.language))
        return
    await query.edit_message_text(t("btn_categories", db_user.language), reply_markup=categories_keyboard(categories, db_user.language))


@registered_user
async def show_genres(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = context.user_data["db_user"]
    genres = await run_blocking(genre_service.list_all)
    query = update.callback_query
    await query.answer()
    if not genres:
        await query.edit_message_text(t("empty_list", db_user.language))
        return
    await query.edit_message_text(t("btn_genres", db_user.language), reply_markup=genres_keyboard(genres, db_user.language))


@registered_user
async def open_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _, category_id, page = update.callback_query.data.split(":")
    await send_movie_list(update, context, "category", category_id, int(page))


@registered_user
async def open_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _, genre_id, page = update.callback_query.data.split(":")
    await send_movie_list(update, context, "genre", genre_id, int(page))


# --------------------------------------------------------- Search flow ----

@registered_user
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = context.user_data["db_user"]
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎬 Film nomini yoki kodini kiriting.\n\n"
        "Masalan:\n"
        "• Avatar\n"
        "• John Wick\n"
        "• 100"
    )
    return SearchStates.WAITING_QUERY


@registered_user
async def receive_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    # Agar foydalanuvchi faqat raqam yozgan bo'lsa
    if text.isdigit():
        movie = await run_blocking(movie_service.get_by_code, text)

        if movie:
            from app.bot.handlers.movie_handlers import send_movie_detail
            await send_movie_detail(update, context, movie.id, edit=False)
            return ConversationHandler.END

    # Aks holda film nomi bo'yicha qidirish
    await send_movie_list(update, context, "search", text, 0)

    return ConversationHandler.END

@registered_user

async def start_code_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = context.user_data["db_user"]
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("ask_code", db_user.language))
    return SearchStates.WAITING_CODE



async def receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = context.user_data["db_user"]
    movie = await run_blocking(movie_service.get_by_code, update.message.text.strip())
    if movie is None:
        await update.message.reply_text(t("not_found", db_user.language))
        return ConversationHandler.END
    from app.bot.handlers.movie_handlers import send_movie_detail

    await send_movie_detail(update, context, movie.id, edit=False)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("OK")
    return ConversationHandler.END


def register(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(show_top, pattern=r"^menu:top$"))
    application.add_handler(CallbackQueryHandler(show_latest, pattern=r"^menu:latest$"))
    application.add_handler(CallbackQueryHandler(show_recommend, pattern=r"^menu:recommend$"))
    application.add_handler(CallbackQueryHandler(show_favorites, pattern=r"^menu:favorites$"))
    application.add_handler(CallbackQueryHandler(show_history, pattern=r"^menu:history$"))
    application.add_handler(CallbackQueryHandler(show_random, pattern=r"^menu:random$"))
    application.add_handler(CallbackQueryHandler(show_categories, pattern=r"^menu:categories$"))
    application.add_handler(CallbackQueryHandler(show_genres, pattern=r"^menu:genres$"))
    application.add_handler(CallbackQueryHandler(open_category, pattern=r"^category:"))
    application.add_handler(CallbackQueryHandler(open_genre, pattern=r"^genre:"))
    application.add_handler(CallbackQueryHandler(handle_list_pagination, pattern=r"^list:.+:page:\d+$"))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_search, pattern=r"^menu:search$")],
            states={SearchStates.WAITING_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_query)]},
            fallbacks=[CommandHandler("cancel", cancel)],
            name="search_conversation",
        )
    )
    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_code_search, pattern=r"^menu:code$")],
            states={SearchStates.WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code)]},
            fallbacks=[CommandHandler("cancel", cancel)],
            name="code_search_conversation",
        )
    )
