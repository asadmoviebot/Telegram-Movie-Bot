"""Repositories for Movie, Category and Genre aggregates."""
from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Category, Genre, Movie


class MovieRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _base_query(self):
        return select(Movie).options(
            selectinload(Movie.category), selectinload(Movie.genres)
        )

    def get_by_id(self, movie_id: int) -> Movie | None:
        stmt = self._base_query().where(Movie.id == movie_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_code(self, code: str) -> Movie | None:
        stmt = self._base_query().where(Movie.code == code.strip().upper())
        return self.session.execute(stmt).scalar_one_or_none()

    def search(self, query: str, limit: int = 20) -> list[Movie]:
        pattern = f"%{query.strip()}%"
        stmt = (
            self._base_query()
            .where(or_(Movie.title.ilike(pattern), Movie.description.ilike(pattern)))
            .order_by(Movie.views.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_by_category(self, category_id: int, limit: int = 20, offset: int = 0) -> list[Movie]:
        stmt = (
            self._base_query()
            .where(Movie.category_id == category_id)
            .order_by(Movie.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_by_genre(self, genre_id: int, limit: int = 20, offset: int = 0) -> list[Movie]:
        stmt = (
            self._base_query()
            .join(Movie.genres)
            .where(Genre.id == genre_id)
            .order_by(Movie.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def top_rated(self, limit: int = 10) -> list[Movie]:
        stmt = (
            self._base_query()
            .where(Movie.rating_count > 0)
            .order_by((Movie.rating_sum * 1.0 / Movie.rating_count).desc(), Movie.rating_count.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def latest(self, limit: int = 10) -> list[Movie]:
        stmt = self._base_query().order_by(Movie.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def random_movie(self) -> Movie | None:
        stmt = self._base_query()
        movies = list(self.session.execute(stmt).scalars().all())
        return random.choice(movies) if movies else None

    def most_favorited_genre_ids(self, movie_ids: list[int]) -> list[int]:
        if not movie_ids:
            return []
        stmt = (
            select(Genre.id)
            .join(Movie.genres)
            .where(Movie.id.in_(movie_ids))
            .group_by(Genre.id)
            .order_by(func.count(Genre.id).desc())
        )
        return [row[0] for row in self.session.execute(stmt).all()]

    def recommend_by_genres(self, genre_ids: list[int], exclude_ids: list[int], limit: int = 10) -> list[Movie]:
        if not genre_ids:
            return self.top_rated(limit)
        stmt = (
            self._base_query()
            .join(Movie.genres)
            .where(Genre.id.in_(genre_ids))
            .where(Movie.id.notin_(exclude_ids or [0]))
            .group_by(Movie.id)
            .order_by(func.count(Genre.id).desc(), Movie.rating_count.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().unique().all())

    def count(self) -> int:
        return self.session.execute(select(func.count(Movie.id))).scalar_one()

    def create(self, **kwargs) -> Movie:
        genre_ids: list[int] = kwargs.pop("genre_ids", [])
        movie = Movie(**kwargs)
        if genre_ids:
            movie.genres = list(
                self.session.execute(select(Genre).where(Genre.id.in_(genre_ids))).scalars().all()
            )
        self.session.add(movie)
        self.session.flush()
        return movie

    def update(self, movie_id: int, **kwargs) -> Movie | None:
        movie = self.get_by_id(movie_id)
        if movie is None:
            return None
        genre_ids = kwargs.pop("genre_ids", None)
        for key, value in kwargs.items():
            if value is not None and hasattr(movie, key):
                setattr(movie, key, value)
        if genre_ids is not None:
            movie.genres = list(
                self.session.execute(select(Genre).where(Genre.id.in_(genre_ids))).scalars().all()
            )
        self.session.flush()
        return movie

    def delete(self, movie_id: int) -> bool:
        movie = self.get_by_id(movie_id)
        if movie is None:
            return False
        self.session.delete(movie)
        return True

    def increment_views(self, movie_id: int) -> None:
        movie = self.get_by_id(movie_id)
        if movie:
            movie.views += 1

    def apply_rating(self, movie_id: int, delta_sum: int, delta_count: int) -> None:
        movie = self.get_by_id(movie_id)
        if movie:
            movie.rating_sum += delta_sum
            movie.rating_count += delta_count


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Category]:
        return list(self.session.execute(select(Category).order_by(Category.name_en)).scalars().all())

    def get_by_id(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def create(self, name_uz: str, name_en: str, name_ru: str) -> Category:
        category = Category(name_uz=name_uz, name_en=name_en, name_ru=name_ru)
        self.session.add(category)
        self.session.flush()
        return category

    def update(self, category_id: int, **kwargs) -> Category | None:
        category = self.get_by_id(category_id)
        if category is None:
            return None
        for key, value in kwargs.items():
            if value:
                setattr(category, key, value)
        return category

    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if category is None:
            return False
        self.session.delete(category)
        return True


class GenreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Genre]:
        return list(self.session.execute(select(Genre).order_by(Genre.name_en)).scalars().all())

    def get_by_id(self, genre_id: int) -> Genre | None:
        return self.session.get(Genre, genre_id)

    def create(self, name_uz: str, name_en: str, name_ru: str) -> Genre:
        genre = Genre(name_uz=name_uz, name_en=name_en, name_ru=name_ru)
        self.session.add(genre)
        self.session.flush()
        return genre

    def update(self, genre_id: int, **kwargs) -> Genre | None:
        genre = self.get_by_id(genre_id)
        if genre is None:
            return None
        for key, value in kwargs.items():
            if value:
                setattr(genre, key, value)
        return genre

    def delete(self, genre_id: int) -> bool:
        genre = self.get_by_id(genre_id)
        if genre is None:
            return False
        self.session.delete(genre)
        return True
