"""Business logic for ratings and comments."""
from __future__ import annotations

from app.database.models import Comment, Rating, User
from app.database.session import get_session
from app.repositories.interaction_repository import CommentRepository, RatingRepository
from app.repositories.movie_repository import MovieRepository


class RatingService:
    def rate(self, user_id: int, movie_id: int, score: int) -> Rating:
        score = max(1, min(10, score))
        with get_session() as session:
            rating_repo = RatingRepository(session)
            rating, delta_sum, delta_count = rating_repo.upsert(user_id, movie_id, score)
            MovieRepository(session).apply_rating(movie_id, delta_sum, delta_count)
            return rating

    def get_user_rating(self, user_id: int, movie_id: int) -> Rating | None:
        with get_session() as session:
            return RatingRepository(session).get(user_id, movie_id)


class CommentService:
    def add(self, user_id: int, movie_id: int, text: str) -> Comment:
        with get_session() as session:
            return CommentRepository(session).add(user_id, movie_id, text)

    def list_for_movie(self, movie_id: int, page: int = 0, page_size: int = 5) -> list[tuple[Comment, User]]:
        with get_session() as session:
            return CommentRepository(session).list_for_movie(movie_id, page_size, page * page_size)

    def count_for_movie(self, movie_id: int) -> int:
        with get_session() as session:
            return CommentRepository(session).count_for_movie(movie_id)
