"""Repositories for User, Favorite and WatchHistory aggregates."""
from __future__ import annotations

import secrets
import string
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Favorite, Movie, User, WatchHistory


def generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username.lstrip("@"))
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_referral_code(self, code: str) -> User | None:
        stmt = select(User).where(User.referral_code == code)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        telegram_id: int,
        username: str | None,
        full_name: str,
        language: str,
        referred_by_id: int | None = None,
        is_admin: bool = False,
    ) -> User:
        code = generate_referral_code()
        while self.get_by_referral_code(code) is not None:
            code = generate_referral_code()
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            language=language,
            referral_code=code,
            referred_by_id=referred_by_id,
            is_admin=is_admin,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def touch_last_active(self, user: User) -> None:
        user.last_active_at = datetime.utcnow()

    def set_language(self, user: User, language: str) -> None:
        user.language = language

    def set_ban(self, user: User, banned: bool) -> None:
        user.is_banned = banned

    def grant_premium(self, user: User, until: datetime | None) -> None:
        user.is_premium = True
        user.premium_until = until

    def revoke_premium(self, user: User) -> None:
        user.is_premium = False
        user.premium_until = None

    def list_expired_premium(self, now: datetime) -> list[User]:
        stmt = select(User).where(User.is_premium.is_(True)).where(User.premium_until.is_not(None)).where(
            User.premium_until < now
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def search(self, query: str, limit: int = 20) -> list[User]:
        pattern = f"%{query.strip()}%"
        stmt = select(User).where(
            (User.username.ilike(pattern)) | (User.full_name.ilike(pattern))
        ).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.session.execute(select(func.count(User.id))).scalar_one()

    def count_premium(self) -> int:
        return self.session.execute(
            select(func.count(User.id)).where(User.is_premium.is_(True))
        ).scalar_one()

    def count_banned(self) -> int:
        return self.session.execute(
            select(func.count(User.id)).where(User.is_banned.is_(True))
        ).scalar_one()

    def count_referrals(self, user_id: int) -> int:
        return self.session.execute(
            select(func.count(User.id)).where(User.referred_by_id == user_id)
        ).scalar_one()

    def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        counts_stmt = (
            select(User.referred_by_id, func.count(User.id))
            .where(User.referred_by_id.is_not(None))
            .group_by(User.referred_by_id)
            .order_by(func.count(User.id).desc())
            .limit(limit)
        )
        rows = self.session.execute(counts_stmt).all()
        result: list[tuple[User, int]] = []
        for referrer_id, cnt in rows:
            referrer = self.get_by_id(referrer_id)
            if referrer:
                result.append((referrer, cnt))
        return result

    def all_telegram_ids(self) -> list[int]:
        return list(self.session.execute(select(User.telegram_id).where(User.is_banned.is_(False))).scalars().all())


class FavoriteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_favorite(self, user_id: int, movie_id: int) -> bool:
        stmt = select(Favorite).where(Favorite.user_id == user_id, Favorite.movie_id == movie_id)
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def add(self, user_id: int, movie_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, movie_id=movie_id)
        self.session.add(favorite)
        self.session.flush()
        return favorite

    def remove(self, user_id: int, movie_id: int) -> bool:
        stmt = select(Favorite).where(Favorite.user_id == user_id, Favorite.movie_id == movie_id)
        favorite = self.session.execute(stmt).scalar_one_or_none()
        if favorite is None:
            return False
        self.session.delete(favorite)
        return True

    def list_for_user(self, user_id: int, limit: int = 20, offset: int = 0) -> list[Movie]:
        stmt = (
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .where(Favorite.user_id == user_id)
            .options(selectinload(Movie.category), selectinload(Movie.genres))
            .order_by(Favorite.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def movie_ids_for_user(self, user_id: int) -> list[int]:
        stmt = select(Favorite.movie_id).where(Favorite.user_id == user_id)
        return list(self.session.execute(stmt).scalars().all())


class HistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, user_id: int, movie_id: int) -> WatchHistory:
        entry = WatchHistory(user_id=user_id, movie_id=movie_id)
        self.session.add(entry)
        self.session.flush()
        return entry

    def list_for_user(self, user_id: int, limit: int = 20, offset: int = 0) -> list[Movie]:
        stmt = (
            select(Movie)
            .join(WatchHistory, WatchHistory.movie_id == Movie.id)
            .where(WatchHistory.user_id == user_id)
            .options(selectinload(Movie.category), selectinload(Movie.genres))
            .order_by(WatchHistory.watched_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def recent_movie_ids_for_user(self, user_id: int, limit: int = 10) -> list[int]:
        stmt = (
            select(WatchHistory.movie_id)
            .where(WatchHistory.user_id == user_id)
            .order_by(WatchHistory.watched_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
