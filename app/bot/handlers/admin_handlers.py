"""Admin panel navigation plus movie, category and genre management."""
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

from app.bot.keyboards import (
    admin_back_keyboard,
    admin_categories_keyboard,
    admin_genres_keyboard,
    admin_menu_keyboard,
    admin_movies_keyboard,
    category_select_keyboard,
    genre_multiselect_keyboard,
    yes_no_keyboard,
)
from app.bot.states import CategoryAdminStates, GenreAdminStates, MovieAdminStates
from app.logging_config import get_logger
from app.services.movie_service import CategoryService, GenreService, MovieService
from app.utils.decorators import admin_only, run_blocking

logger = get_logger(__name__)
movie_service = MovieService()
category_service = CategoryService()
genre_service = GenreService()


@admin_only
async def open_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("⚙️ Admin Panel", reply_markup=admin_menu_keyboard())
    else:
        await update.message.reply_text("⚙️ Admin Panel", reply_markup=admin_menu_keyboard())


@admin_only
async def close_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Admin panel closed.")


@admin_only
async def open_movies_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎬 Movie Management", reply_markup=admin_movies_keyboard())


# ------------------------------------------------------------ Categories --

@admin_only
async def open_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    categories = await run_blocking(category_service.list_all)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🗂 Categories", reply_markup=admin_categories_keyboard(categories))


@admin_only
async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter category name in Uzbek:")
    return CategoryAdminStates.NAME_UZ


@admin_only
async def category_name_uz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cat_name_uz"] = update.message.text.strip()
    await update.message.reply_text("Now enter it in English:")
    return CategoryAdminStates.NAME_EN


@admin_only
async def category_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cat_name_en"] = update.message.text.strip()
    await update.message.reply_text("Now enter it in Russian:")
    return CategoryAdminStates.NAME_RU


@admin_only
async def category_name_ru(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name_ru = update.message.text.strip()
    await run_blocking(
        category_service.create, context.user_data.pop("cat_name_uz"), context.user_data.pop("cat_name_en"), name_ru
    )
    await update.message.reply_text("✅ Category created.")
    categories = await run_blocking(category_service.list_all)
    await update.message.reply_text("🗂 Categories", reply_markup=admin_categories_keyboard(categories))
    return ConversationHandler.END


@admin_only
async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    category_id = int(update.callback_query.data.split(":")[-1])
    await run_blocking(category_service.delete, category_id)
    categories = await run_blocking(category_service.list_all)
    query = update.callback_query
    await query.answer("Deleted.")
    await query.edit_message_text("🗂 Categories", reply_markup=admin_categories_keyboard(categories))


# ----------------------------------------------------------------- Genres --

@admin_only
async def open_genres_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genres = await run_blocking(genre_service.list_all)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎭 Genres", reply_markup=admin_genres_keyboard(genres))


@admin_only
async def start_add_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter genre name in Uzbek:")
    return GenreAdminStates.NAME_UZ


@admin_only
async def genre_name_uz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["genre_name_uz"] = update.message.text.strip()
    await update.message.reply_text("Now in English:")
    return GenreAdminStates.NAME_EN


@admin_only
async def genre_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["genre_name_en"] = update.message.text.strip()
    await update.message.reply_text("Now in Russian:")
    return GenreAdminStates.NAME_RU


@admin_only
async def genre_name_ru(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name_ru = update.message.text.strip()
    await run_blocking(
        genre_service.create, context.user_data.pop("genre_name_uz"), context.user_data.pop("genre_name_en"), name_ru
    )
    await update.message.reply_text("✅ Genre created.")
    genres = await run_blocking(genre_service.list_all)
    await update.message.reply_text("🎭 Genres", reply_markup=admin_genres_keyboard(genres))
    return ConversationHandler.END


@admin_only
async def delete_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genre_id = int(update.callback_query.data.split(":")[-1])
    await run_blocking(genre_service.delete, genre_id)
    genres = await run_blocking(genre_service.list_all)
    query = update.callback_query
    await query.answer("Deleted.")
    await query.edit_message_text("🎭 Genres", reply_markup=admin_genres_keyboard(genres))


# ------------------------------------------------------------ Add movie ---

@admin_only
async def start_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_movie", None)
    context.user_data.pop("selected_genres", None)
    context.user_data["new_movie"] = {}
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter movie title:")
    return MovieAdminStates.TITLE


async def movie_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_movie"]["title"] = update.message.text.strip()
    await update.message.reply_text("Enter description:")
    return MovieAdminStates.DESCRIPTION


async def movie_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_movie"]["description"] = update.message.text.strip()
    await update.message.reply_text("Enter release year (e.g. 2024):")
    return MovieAdminStates.YEAR


async def movie_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["new_movie"]["year"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Please send a valid year, e.g. 2024:")
        return MovieAdminStates.YEAR
    await update.message.reply_text("Enter duration in minutes:")
    return MovieAdminStates.DURATION


async def movie_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["new_movie"]["duration_minutes"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Please send a valid number of minutes:")
        return MovieAdminStates.DURATION
    await update.message.reply_text("Enter quality (e.g. HD, FHD, 4K):")
    return MovieAdminStates.QUALITY


async def movie_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_movie"]["quality"] = update.message.text.strip().upper()
    categories = await run_blocking(category_service.list_all)
    await update.message.reply_text("Choose a category:", reply_markup=category_select_keyboard(categories, "admin:movie:cat"))
    return MovieAdminStates.CATEGORY


async def movie_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_id = int(update.callback_query.data.split(":")[-1])
    context.user_data["new_movie"]["category_id"] = category_id or None
    context.user_data["selected_genres"] = set()
    genres = await run_blocking(genre_service.list_all)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Select genres, then tap Done:", reply_markup=genre_multiselect_keyboard(genres, set()))
    return MovieAdminStates.GENRES


async def movie_genre_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    value = query.data.split(":")[-1]
    if value == "done":
        await query.answer()
        await query.edit_message_text("Is this a Premium-only movie?", reply_markup=yes_no_keyboard("admin:movie:premium:yes", "admin:movie:premium:no"))
        return MovieAdminStates.PREMIUM

    genre_id = int(value)
    selected: set[int] = context.user_data.setdefault("selected_genres", set())
    if genre_id in selected:
        selected.remove(genre_id)
    else:
        selected.add(genre_id)
    genres = await run_blocking(genre_service.list_all)
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=genre_multiselect_keyboard(genres, selected))
    return MovieAdminStates.GENRES


async def movie_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_movie"]["is_premium"] = query.data.endswith("yes")
    context.user_data["new_movie"]["genre_ids"] = list(context.user_data.get("selected_genres", set()))
    await query.answer()
    await query.edit_message_text("Send the poster image (or /skip):")
    return MovieAdminStates.POSTER


async def movie_poster(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1] if update.message.photo else None
    context.user_data["new_movie"]["poster_file_id"] = photo.file_id if photo else None
    await update.message.reply_text("Now send the movie video file:")
    return MovieAdminStates.VIDEO


async def movie_skip_poster(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_movie"]["poster_file_id"] = None
    await update.message.reply_text("Now send the movie video file:")
    return MovieAdminStates.VIDEO


async def movie_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    video = update.message.video or update.message.document
    if video is None:
        await update.message.reply_text("Please send a video file:")
        return MovieAdminStates.VIDEO
    data = context.user_data["new_movie"]
    data["file_id"] = video.file_id
    movie = await run_blocking(movie_service.create, **data)
    await update.message.reply_text(f"✅ Movie saved!\nCode: <code>{movie.code}</code>", parse_mode="HTML")
    context.user_data.pop("new_movie", None)
    context.user_data.pop("selected_genres", None)
    return ConversationHandler.END


async def cancel_movie_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_movie", None)
    context.user_data.pop("selected_genres", None)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ----------------------------------------------------------- Edit movie ---

@admin_only
async def start_edit_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the movie code to edit:")
    return MovieAdminStates.EDIT_FIELD


async def edit_movie_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    movie = await run_blocking(movie_service.get_by_code, update.message.text.strip())
    if movie is None:
        await update.message.reply_text("Movie not found. Send another code or /cancel.")
        return MovieAdminStates.EDIT_FIELD
    context.user_data["edit_movie_id"] = movie.id
    await update.message.reply_text(
        "Which field to edit? Send one of: title, description, year, duration_minutes, quality, is_premium"
    )
    return MovieAdminStates.EDIT_VALUE


async def edit_movie_field_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    field = update.message.text.strip().lower()
    allowed = {"title", "description", "year", "duration_minutes", "quality", "is_premium"}
    if field not in allowed:
        await update.message.reply_text(f"Unknown field. Choose one of: {', '.join(allowed)}")
        return MovieAdminStates.EDIT_VALUE
    context.user_data["edit_field"] = field
    await update.message.reply_text(f"Send the new value for {field}:")
    return MovieAdminStates.CONFIRM


async def edit_movie_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    field = context.user_data.pop("edit_field")
    movie_id = context.user_data.pop("edit_movie_id")
    raw = update.message.text.strip()
    value: object = raw
    if field in {"year", "duration_minutes"}:
        try:
            value = int(raw)
        except ValueError:
            await update.message.reply_text("Please send a valid number.")
            return ConversationHandler.END
    elif field == "is_premium":
        value = raw.lower() in {"yes", "true", "1", "ha"}
    await run_blocking(movie_service.update, movie_id, **{field: value})
    await update.message.reply_text("✅ Movie updated.")
    return ConversationHandler.END


# --------------------------------------------------------- Delete movie ---

@admin_only
async def start_delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the movie code to delete:")
    return MovieAdminStates.CONFIRM


async def delete_movie_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    movie = await run_blocking(movie_service.get_by_code, update.message.text.strip())
    if movie is None:
        await update.message.reply_text("Movie not found.")
        return ConversationHandler.END
    await run_blocking(movie_service.delete, movie.id)
    await update.message.reply_text(f"🗑 Deleted movie '{movie.title}'.")
    return ConversationHandler.END


# ------------------------------------------------------------- Register ---

async def register(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(open_admin_menu, pattern=r"^admin:menu$"))
    application.add_handler(CallbackQueryHandler(close_admin_menu, pattern=r"^admin:close$"))
    application.add_handler(CallbackQueryHandler(open_movies_menu, pattern=r"^admin:movies$"))
    application.add_handler(CallbackQueryHandler(open_categories_menu, pattern=r"^admin:categories$"))
    application.add_handler(CallbackQueryHandler(open_genres_menu, pattern=r"^admin:genres$"))
    application.add_handler(CallbackQueryHandler(delete_category, pattern=r"^admin:category:del:\d+$"))
    application.add_handler(CallbackQueryHandler(delete_genre, pattern=r"^admin:genre:del:\d+$"))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_add_category, pattern=r"^admin:category:add$")],
            states={
                CategoryAdminStates.NAME_UZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name_uz)],
                CategoryAdminStates.NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name_en)],
                CategoryAdminStates.NAME_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name_ru)],
            },
            fallbacks=[CommandHandler("cancel", cancel_movie_wizard)],
            name="add_category_conversation",
        )
    )
    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_add_genre, pattern=r"^admin:genre:add$")],
            states={
                GenreAdminStates.NAME_UZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, genre_name_uz)],
                GenreAdminStates.NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, genre_name_en)],
                GenreAdminStates.NAME_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, genre_name_ru)],
            },
            fallbacks=[CommandHandler("cancel", cancel_movie_wizard)],
            name="add_genre_conversation",
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_edit_movie, pattern=r"^admin:movie:edit$")],
            states={
                MovieAdminStates.EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_movie_lookup)],
                MovieAdminStates.EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_movie_field_choice)],
                MovieAdminStates.CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_movie_save)],
            },
            fallbacks=[CommandHandler("cancel", cancel_movie_wizard)],
            name="edit_movie_conversation",
            conversation_timeout=300,
            allow_reentry=True,
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_delete_movie, pattern=r"^admin:movie:delete$")],
            states={MovieAdminStates.CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_movie_confirm)]},
            fallbacks=[CommandHandler("cancel", cancel_movie_wizard)],
            name="delete_movie_conversation",
            conversation_timeout=300,
            allow_reentry=True,
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(start_add_movie, pattern=r"^admin:movie:add$")
            ],
            states={
                MovieAdminStates.TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, movie_title)
                ],
                MovieAdminStates.DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, movie_description)
                ],
                MovieAdminStates.YEAR: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, movie_year)
                ],
                MovieAdminStates.DURATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, movie_duration)
                ],
                MovieAdminStates.QUALITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, movie_quality)
                ],
                MovieAdminStates.CATEGORY: [
                    CallbackQueryHandler(movie_category, pattern=r"^admin:movie:cat:\d+$")
                ],
                MovieAdminStates.GENRES: [
                    CallbackQueryHandler(movie_genre_toggle, pattern=r"^admin:movie:genre:")
                ],
                MovieAdminStates.PREMIUM: [
                    CallbackQueryHandler(movie_premium, pattern=r"^admin:movie:premium:")
                ],
                MovieAdminStates.POSTER: [
                    MessageHandler(filters.PHOTO, movie_poster),
                    CommandHandler("skip", movie_skip_poster),
                ],
                MovieAdminStates.VIDEO: [
                    MessageHandler(filters.VIDEO | filters.Document.VIDEO, movie_video),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_movie_wizard)],
            name="add_movie_conversation",
            conversation_timeout=300,
            allow_reentry=True,
        )
    )