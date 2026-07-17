"""Translation strings for Uzbek, English and Russian."""
from __future__ import annotations

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "welcome": {
        "uz": "Assalomu alaykum, {name}! 🎬 Kino platformasiga xush kelibsiz.",
        "en": "Hello, {name}! 🎬 Welcome to the Movie Platform.",
        "ru": "Привет, {name}! 🎬 Добро пожаловать на платформу фильмов.",
    },
    "choose_language": {
        "uz": "Tilni tanlang:",
        "en": "Choose your language:",
        "ru": "Выберите язык:",
    },
    "language_saved": {
        "uz": "Til o'zbek tiliga o'rnatildi ✅",
        "en": "Language set to English ✅",
        "ru": "Язык изменён на русский ✅",
    },
    "main_menu": {
        "uz": "Bosh menyu. Kerakli bo'limni tanlang:",
        "en": "Main menu. Choose an option:",
        "ru": "Главное меню. Выберите раздел:",
    },
    "btn_search": {"uz": "🔍 Qidirish", "en": "🔍 Search", "ru": "🔍 Поиск"},
    "btn_code": {"uz": "🔢 Kod orqali", "en": "🔢 Search by code", "ru": "🔢 По коду"},
    "btn_categories": {"uz": "🗂 Kategoriyalar", "en": "🗂 Categories", "ru": "🗂 Категории"},
    "btn_genres": {"uz": "🎭 Janrlar", "en": "🎭 Genres", "ru": "🎭 Жанры"},
    "btn_top": {"uz": "🏆 Top kinolar", "en": "🏆 Top Movies", "ru": "🏆 Топ фильмов"},
    "btn_latest": {"uz": "🆕 Yangi kinolar", "en": "🆕 Latest Movies", "ru": "🆕 Новинки"},
    "btn_random": {"uz": "🎲 Tasodifiy", "en": "🎲 Random Movie", "ru": "🎲 Случайный"},
    "btn_favorites": {"uz": "❤️ Sevimlilar", "en": "❤️ Favorites", "ru": "❤️ Избранное"},
    "btn_history": {"uz": "🕘 Tarix", "en": "🕘 Watch History", "ru": "🕘 История"},
    "btn_recommend": {"uz": "✨ Tavsiyalar", "en": "✨ Recommendations", "ru": "✨ Рекомендации"},
    "btn_profile": {"uz": "👤 Profil", "en": "👤 Profile", "ru": "👤 Профиль"},
    "btn_language": {"uz": "🌐 Til", "en": "🌐 Language", "ru": "🌐 Язык"},
    "btn_admin": {"uz": "⚙️ Admin panel", "en": "⚙️ Admin Panel", "ru": "⚙️ Админ-панель"},
    "btn_back": {"uz": "◀️ Orqaga", "en": "◀️ Back", "ru": "◀️ Назад"},
    "btn_next": {"uz": "Keyingi ▶️", "en": "Next ▶️", "ru": "Далее ▶️"},
    "btn_prev": {"uz": "◀️ Oldingi", "en": "◀️ Previous", "ru": "◀️ Назад"},
    "ask_search": {
        "uz": "Kino nomini kiriting:",
        "en": "Type the movie title to search:",
        "ru": "Введите название фильма:",
    },
    "ask_code": {
        "uz": "Kino kodini kiriting (masalan: MATRIX):",
        "en": "Enter the movie code (e.g. MATRIX):",
        "ru": "Введите код фильма (например: MATRIX):",
    },
    "not_found": {
        "uz": "Hech narsa topilmadi 😔",
        "en": "Nothing found 😔",
        "ru": "Ничего не найдено 😔",
    },
    "movie_card": {
        "uz": "🎬 <b>{title}</b> ({year})\nKod: <code>{code}</code>\nSifat: {quality} | Davomiyligi: {duration} daq\n⭐ {rating} ({count} baho) | 👁 {views}\n\n{description}",
        "en": "🎬 <b>{title}</b> ({year})\nCode: <code>{code}</code>\nQuality: {quality} | Duration: {duration} min\n⭐ {rating} ({count} ratings) | 👁 {views}\n\n{description}",
        "ru": "🎬 <b>{title}</b> ({year})\nКод: <code>{code}</code>\nКачество: {quality} | Длительность: {duration} мин\n⭐ {rating} ({count} оценок) | 👁 {views}\n\n{description}",
    },
    "premium_locked": {
        "uz": "Bu kino faqat Premium foydalanuvchilar uchun 🔒",
        "en": "This movie is Premium-only 🔒",
        "ru": "Этот фильм доступен только для Premium 🔒",
    },
    "added_favorite": {"uz": "Sevimlilarga qo'shildi ❤️", "en": "Added to favorites ❤️", "ru": "Добавлено в избранное ❤️"},
    "removed_favorite": {"uz": "Sevimlilardan olib tashlandi 💔", "en": "Removed from favorites 💔", "ru": "Удалено из избранного 💔"},
    "ask_rating": {"uz": "Bahoni tanlang (1-10):", "en": "Choose a rating (1-10):", "ru": "Выберите оценку (1-10):"},
    "rating_saved": {"uz": "Bahoyingiz saqlandi, rahmat!", "en": "Your rating has been saved, thanks!", "ru": "Ваша оценка сохранена, спасибо!"},
    "ask_comment": {"uz": "Sharhingizni yozing:", "en": "Write your comment:", "ru": "Напишите комментарий:"},
    "comment_saved": {"uz": "Sharh qo'shildi ✅", "en": "Comment added ✅", "ru": "Комментарий добавлен ✅"},
    "empty_list": {"uz": "Ro'yxat bo'sh", "en": "This list is empty", "ru": "Список пуст"},
    "profile_card": {
        "uz": "👤 <b>Profil</b>\nIsm: {name}\nTil: {lang}\nPremium: {premium}\nRo'yxatdan o'tgan: {joined}\nTakliflar: {referrals}",
        "en": "👤 <b>Profile</b>\nName: {name}\nLanguage: {lang}\nPremium: {premium}\nJoined: {joined}\nReferrals: {referrals}",
        "ru": "👤 <b>Профиль</b>\nИмя: {name}\nЯзык: {lang}\nPremium: {premium}\nРегистрация: {joined}\nРефералы: {referrals}",
    },
    "referral_message": {
        "uz": "🔗 Sizning taklif havolangiz:\n{link}\n\nDo'stlaringizni taklif qiling va Premium yutib oling!",
        "en": "🔗 Your referral link:\n{link}\n\nInvite friends and earn Premium rewards!",
        "ru": "🔗 Ваша реферальная ссылка:\n{link}\n\nПриглашайте друзей и получайте Premium!",
    },
    "banned": {
        "uz": "Siz bloklangansiz. Admin bilan bog'laning.",
        "en": "You are banned from using this bot. Contact the admin.",
        "ru": "Вы заблокированы. Свяжитесь с администратором.",
    },
    "subscribe_required": {
        "uz": "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
        "en": "Please subscribe to the following channels to use the bot:",
        "ru": "Подпишитесь на каналы ниже, чтобы пользоваться ботом:",
    },
    "subscribe_check": {"uz": "✅ Tekshirish", "en": "✅ I've subscribed", "ru": "✅ Проверить"},
    "still_not_subscribed": {
        "uz": "Siz hali barcha kanallarga a'zo bo'lmadingiz ❌",
        "en": "You haven't subscribed to all channels yet ❌",
        "ru": "Вы ещё не подписаны на все каналы ❌",
    },
    "admin_only": {"uz": "Bu buyruq faqat adminlar uchun.", "en": "This command is for admins only.", "ru": "Эта команда только для администраторов."},
    "admin_menu": {"uz": "⚙️ Admin panel", "en": "⚙️ Admin Panel", "ru": "⚙️ Админ-панель"},
    "cancelled": {"uz": "Bekor qilindi.", "en": "Cancelled.", "ru": "Отменено."},
}


def t(key: str, lang: str, **kwargs) -> str:
    entry = _TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get("en") or key
    return text.format(**kwargs) if kwargs else text
