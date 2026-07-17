"""Repositories for Rating and Comment aggregates."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Comment, Rating, User


class RatingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: int, movie_id: int) -> Rating | None:
        stmt = select(Rating).where(Rating.user_id == user_id, Rating.movie_id == movie_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert(self, user_id: int, movie_id: int, score: int) -> tuple[Rating, int, int]:
        """Create or update a rating. Returns (rating, delta_sum, delta_count) for aggregate updates."""
        existing = self.get(user_id, movie_id)
        if existing is None:
            rating = Rating(user_id=user_id, movie_id=movie_id, score=score)
            self.session.add(rating)
            self.session.flush()
            return rating, score, 1
        delta = score - existing.score
        existing.score = score
        return existing, delta, 0


class CommentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, user_id: int, movie_id: int, text: str) -> Comment:
        comment = Comment(user_id=user_id, movie_id=movie_id, text=text.strip()[:1000])
        self.session.add(comment)
        self.session.flush()
        return comment

    def list_for_movie(self, movie_id: int, limit: int = 10, offset: int = 0) -> list[tuple[Comment, User]]:
        stmt = (
            select(Comment, User)
            .join(User, User.id == Comment.user_id)
            .where(Comment.movie_id == movie_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [(c, u) for c, u in self.session.execute(stmt).all()]

    def count_for_movie(self, movie_id: int) -> int:
        stmt = select(Comment).where(Comment.movie_id == movie_id)
        return len(list(self.session.execute(stmt).scalars().all()))
