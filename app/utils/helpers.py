"""Small formatting and pagination helpers shared by handlers."""
from __future__ import annotations

from app.bot.locales import t
from app.database.models import Movie


def format_movie_card(movie: Movie, lang: str) -> str:
    return t(
        "movie_card",
        lang,
        title=movie.title,
        year=movie.year or "-",
        code=movie.code,
        quality=movie.quality,
        duration=movie.duration_minutes or "-",
        rating=movie.rating_avg,
        count=movie.rating_count,
        views=movie.views,
        description=(movie.description or "")[:600],
    )


def paginate(items: list, page: int, page_size: int) -> tuple[list, bool]:
    start = page * page_size
    chunk = items[start:start + page_size]
    has_next = len(items) > start + page_size
    return chunk, has_next


def chunk_list(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


PAGE_SIZE = 8
