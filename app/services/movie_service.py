"""Business logic for movies, categories and genres."""
from __future__ import annotations

import re

from app.database.models import Category, Genre, Movie
from app.database.session import get_session
from app.repositories.movie_repository import CategoryRepository, GenreRepository, MovieRepository
from app.repositories.user_repository import FavoriteRepository, HistoryRepository


def _generate_code(title: str, session) -> str:
    repo = MovieRepository(session)

    movies = repo.latest(limit=100000)

    max_code = 99

    for movie in movies:
        if movie.code and str(movie.code).isdigit():
            number = int(movie.code)
            if number > max_code:
                max_code = number

    return str(max_code + 1)


class MovieService:
    def search(self, query: str) -> list[Movie]:
        with get_session() as session:
            return MovieRepository(session).search(query)

    def get_by_code(self, code: str) -> Movie | None:
        with get_session() as session:
            return MovieRepository(session).get_by_code(code)

    def get_by_id(self, movie_id: int) -> Movie | None:
        with get_session() as session:
            return MovieRepository(session).get_by_id(movie_id)

    def top_rated(self, limit: int = 10) -> list[Movie]:
        with get_session() as session:
            return MovieRepository(session).top_rated(limit)

    def latest(self, limit: int = 10) -> list[Movie]:
        with get_session() as session:
            return MovieRepository(session).latest(limit)

    def random_movie(self) -> Movie | None:
        with get_session() as session:
            return MovieRepository(session).random_movie()

    def list_by_category(self, category_id: int, page: int = 0, page_size: int = 10) -> list[Movie]:
        with get_session() as session:
            return MovieRepository(session).list_by_category(category_id, page_size, page * page_size)

    def list_by_genre(self, genre_id: int, page: int = 0, page_size: int = 10) -> list[Movie]:
        with get_session() as session:
            return MovieRepository(session).list_by_genre(genre_id, page_size, page * page_size)

    def watch(self, movie_id: int, user_id: int) -> Movie | None:
        with get_session() as session:
            repo = MovieRepository(session)
            repo.increment_views(movie_id)
            HistoryRepository(session).record(user_id, movie_id)
            return repo.get_by_id(movie_id)

    def recommend_for_user(self, user_id: int, limit: int = 10) -> list[Movie]:
        with get_session() as session:
            movie_repo = MovieRepository(session)
            fav_repo = FavoriteRepository(session)
            hist_repo = HistoryRepository(session)
            seed_ids = fav_repo.movie_ids_for_user(user_id) + hist_repo.recent_movie_ids_for_user(user_id)
            if not seed_ids:
                return movie_repo.top_rated(limit)
            genre_ids = movie_repo.most_favorited_genre_ids(seed_ids)
            return movie_repo.recommend_by_genres(genre_ids, exclude_ids=seed_ids, limit=limit)

    def create(
        self,
        title: str,
        description: str,
        year: int,
        duration_minutes: int,
        quality: str,
        file_id: str,
        poster_file_id: str | None,
        category_id: int | None,
        genre_ids: list[int],
        is_premium: bool,
        code: str | None = None,
    ) -> Movie:
        with get_session() as session:
            final_code = code or _generate_code(title, session)
            return MovieRepository(session).create(
                code=final_code,
                title=title,
                description=description,
                year=year,
                duration_minutes=duration_minutes,
                quality=quality,
                file_id=file_id,
                poster_file_id=poster_file_id,
                category_id=category_id,
                genre_ids=genre_ids,
                is_premium=is_premium,
            )

    def update(self, movie_id: int, **fields) -> Movie | None:
        with get_session() as session:
            return MovieRepository(session).update(movie_id, **fields)

    def delete(self, movie_id: int) -> bool:
        with get_session() as session:
            return MovieRepository(session).delete(movie_id)

    def count(self) -> int:
        with get_session() as session:
            return MovieRepository(session).count()


class CategoryService:
    def list_all(self) -> list[Category]:
        with get_session() as session:
            return CategoryRepository(session).list_all()

    def get(self, category_id: int) -> Category | None:
        with get_session() as session:
            return CategoryRepository(session).get_by_id(category_id)

    def create(self, name_uz: str, name_en: str, name_ru: str) -> Category:
        with get_session() as session:
            return CategoryRepository(session).create(name_uz, name_en, name_ru)

    def delete(self, category_id: int) -> bool:
        with get_session() as session:
            return CategoryRepository(session).delete(category_id)


class GenreService:
    def list_all(self) -> list[Genre]:
        with get_session() as session:
            return GenreRepository(session).list_all()

    def get(self, genre_id: int) -> Genre | None:
        with get_session() as session:
            return GenreRepository(session).get_by_id(genre_id)

    def create(self, name_uz: str, name_en: str, name_ru: str) -> Genre:
        with get_session() as session:
            return GenreRepository(session).create(name_uz, name_en, name_ru)

    def delete(self, genre_id: int) -> bool:
        with get_session() as session:
            return GenreRepository(session).delete(genre_id)
