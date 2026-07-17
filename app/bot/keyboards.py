"""Inline keyboard builders for the bot and admin panel."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.locales import t
from app.database.models import Category, Channel, Genre, Movie


def language_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang:uz")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru")],
    ]
    return InlineKeyboardMarkup(rows)


def main_menu_keyboard(lang: str, is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(t("btn_search", lang), callback_data="menu:search"),
         InlineKeyboardButton(t("btn_code", lang), callback_data="menu:code")],
        [InlineKeyboardButton(t("btn_categories", lang), callback_data="menu:categories"),
         InlineKeyboardButton(t("btn_genres", lang), callback_data="menu:genres")],
        [InlineKeyboardButton(t("btn_top", lang), callback_data="menu:top"),
         InlineKeyboardButton(t("btn_latest", lang), callback_data="menu:latest")],
        [InlineKeyboardButton(t("btn_random", lang), callback_data="menu:random"),
         InlineKeyboardButton(t("btn_recommend", lang), callback_data="menu:recommend")],
        [InlineKeyboardButton(t("btn_favorites", lang), callback_data="menu:favorites"),
         InlineKeyboardButton(t("btn_history", lang), callback_data="menu:history")],
        [InlineKeyboardButton(t("btn_profile", lang), callback_data="menu:profile"),
         InlineKeyboardButton(t("btn_language", lang), callback_data="menu:language")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(t("btn_admin", lang), callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def back_button(lang: str, target: str = "menu:home") -> InlineKeyboardButton:
    return InlineKeyboardButton(t("btn_back", lang), callback_data=target)


def paginated_keyboard(
    items: list[tuple[str, str]], page: int, has_next: bool, lang: str, prefix: str, back_target: str = "menu:home"
) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=cb)] for label, cb in items]
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(t("btn_prev", lang), callback_data=f"{prefix}:page:{page - 1}"))
    if has_next:
        nav.append(InlineKeyboardButton(t("btn_next", lang), callback_data=f"{prefix}:page:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([back_button(lang, back_target)])
    return InlineKeyboardMarkup(rows)


def categories_keyboard(categories: list[Category], lang: str) -> InlineKeyboardMarkup:
    items = [(c.name(lang), f"category:{c.id}:0") for c in categories]
    rows = [[InlineKeyboardButton(label, callback_data=cb)] for label, cb in items]
    rows.append([back_button(lang)])
    return InlineKeyboardMarkup(rows)


def genres_keyboard(genres: list[Genre], lang: str) -> InlineKeyboardMarkup:
    items = [(g.name(lang), f"genre:{g.id}:0") for g in genres]
    rows = [[InlineKeyboardButton(label, callback_data=cb)] for label, cb in items]
    rows.append([back_button(lang)])
    return InlineKeyboardMarkup(rows)


def movie_list_keyboard(movies: list[Movie], lang: str, list_prefix: str, page: int, has_next: bool, back_target: str = "menu:home") -> InlineKeyboardMarkup:
    items = [(f"🎬 {m.title} ({m.year})", f"movie:{m.id}") for m in movies]
    return paginated_keyboard(items, page, has_next, lang, list_prefix, back_target)


def movie_detail_keyboard(movie: Movie, lang: str, is_favorite: bool, back_target: str) -> InlineKeyboardMarkup:
    fav_label = "💔" if is_favorite else "❤️"
    rows = [
        [InlineKeyboardButton("▶️ Watch", callback_data=f"watch:{movie.id}")],
        [InlineKeyboardButton(fav_label, callback_data=f"fav:{movie.id}"),
         InlineKeyboardButton("⭐ Rate", callback_data=f"rate:{movie.id}")],
        [InlineKeyboardButton("💬 Comment", callback_data=f"comment:{movie.id}"),
         InlineKeyboardButton("🗨 View comments", callback_data=f"comments:{movie.id}:0")],
        [back_button(lang, back_target)],
    ]
    return InlineKeyboardMarkup(rows)


def rating_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(str(i), callback_data=f"ratesave:{movie_id}:{i}") for i in range(1, 11)]
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
    return InlineKeyboardMarkup(rows)


def subscription_keyboard(channels: list[Channel], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = f"https://t.me/{channel.username}" if channel.username else f"https://t.me/c/{str(channel.chat_id)[4:]}"
        rows.append([InlineKeyboardButton(channel.title or "Channel", url=url)])
    rows.append([InlineKeyboardButton(t("subscribe_check", lang), callback_data="check_subscription")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard(lang: str, yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Yes", callback_data=yes_cb), InlineKeyboardButton("❌ No", callback_data=no_cb)]]
    )


# ---------------------------------------------------------------- Admin ----

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🎬 Movies", callback_data="admin:movies"),
         InlineKeyboardButton("🗂 Categories", callback_data="admin:categories")],
        [InlineKeyboardButton("🎭 Genres", callback_data="admin:genres"),
         InlineKeyboardButton("📊 Statistics", callback_data="admin:stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast"),
         InlineKeyboardButton("💎 Premium", callback_data="admin:premium")],
        [InlineKeyboardButton("📣 Advertisements", callback_data="admin:ads"),
         InlineKeyboardButton("🔗 Referral stats", callback_data="admin:referrals")],
        [InlineKeyboardButton("👥 Users", callback_data="admin:users"),
         InlineKeyboardButton("📡 Channels", callback_data="admin:channels")],
        [InlineKeyboardButton("💾 Backup DB", callback_data="admin:backup"),
         InlineKeyboardButton("♻️ Restore DB", callback_data="admin:restore")],
        [InlineKeyboardButton("📤 Export stats", callback_data="admin:export"),
         InlineKeyboardButton("📄 Logs", callback_data="admin:logs")],
        [InlineKeyboardButton("◀️ Close", callback_data="admin:close")],
    ]
    return InlineKeyboardMarkup(rows)


def admin_movies_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("➕ Add movie", callback_data="admin:movie:add")],
        [InlineKeyboardButton("✏️ Edit movie", callback_data="admin:movie:edit")],
        [InlineKeyboardButton("🗑 Delete movie", callback_data="admin:movie:delete")],
        [InlineKeyboardButton("◀️ Back", callback_data="admin:menu")],
    ]
    return InlineKeyboardMarkup(rows)


def admin_back_keyboard(target: str = "admin:menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data=target)]])


def admin_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{c.name_en} ❌", callback_data=f"admin:category:del:{c.id}")] for c in categories]
    rows.append([InlineKeyboardButton("➕ Add category", callback_data="admin:category:add")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def admin_genres_keyboard(genres: list[Genre]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{g.name_en} ❌", callback_data=f"admin:genre:del:{g.id}")] for g in genres]
    rows.append([InlineKeyboardButton("➕ Add genre", callback_data="admin:genre:add")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def genre_multiselect_keyboard(genres: list[Genre], selected: set[int]) -> InlineKeyboardMarkup:
    rows = []
    for g in genres:
        mark = "✅ " if g.id in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{g.name_en}", callback_data=f"admin:movie:genre:{g.id}")])
    rows.append([InlineKeyboardButton("✔️ Done", callback_data="admin:movie:genre:done")])
    return InlineKeyboardMarkup(rows)


def category_select_keyboard(categories: list[Category], callback_prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(c.name_en, callback_data=f"{callback_prefix}:{c.id}")] for c in categories]
    rows.append([InlineKeyboardButton("— none —", callback_data=f"{callback_prefix}:0")])
    return InlineKeyboardMarkup(rows)


def yes_no_keyboard(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Yes", callback_data=yes_cb), InlineKeyboardButton("❌ No", callback_data=no_cb)]])


def ads_admin_keyboard(ads) -> InlineKeyboardMarkup:
    rows = []
    for ad in ads:
        status = "🟢" if ad.is_active else "🔴"
        rows.append([
            InlineKeyboardButton(f"{status} #{ad.id} {ad.text[:20]}", callback_data=f"admin:ad:toggle:{ad.id}"),
            InlineKeyboardButton("🗑", callback_data=f"admin:ad:del:{ad.id}"),
        ])
    rows.append([InlineKeyboardButton("➕ Add ad", callback_data="admin:ad:add")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def channels_admin_keyboard(channels: list[Channel]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{c.title} ❌", callback_data=f"admin:channel:del:{c.id}")] for c in channels]
    rows.append([InlineKeyboardButton("➕ Add channel", callback_data="admin:channel:add")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)
