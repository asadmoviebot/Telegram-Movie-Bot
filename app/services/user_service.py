"""Business logic for users, favorites, watch history and premium/referrals."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database.models import Movie, User
from app.database.session import get_session
from app.repositories.user_repository import FavoriteRepository, HistoryRepository, UserRepository


class UserService:
    def get_or_create(
        self, telegram_id: int, username: str | None, full_name: str, referral_code: str | None = None
    ) -> User:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_telegram_id(telegram_id)
            if user is not None:
                repo.touch_last_active(user)
                if username and username != user.username:
                    user.username = username
                return user

            referred_by = None
            if referral_code:
                referrer = repo.get_by_referral_code(referral_code)
                if referrer is not None and referrer.telegram_id != telegram_id:
                    referred_by = referrer.id

            return repo.create(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                language=settings.default_language,
                referred_by_id=referred_by,
                is_admin=settings.is_admin(telegram_id),
            )

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        with get_session() as session:
            return UserRepository(session).get_by_telegram_id(telegram_id)

    def set_language(self, telegram_id: int, language: str) -> None:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_telegram_id(telegram_id)
            if user:
                repo.set_language(user, language)

    def referral_link(self, user: User) -> str:
        return f"https://t.me/{settings.bot_username}?start={user.referral_code}"

    def referral_count(self, user_id: int) -> int:
        with get_session() as session:
            return UserRepository(session).count_referrals(user_id)

    def grant_premium(self, telegram_id: int, days: int | None) -> User | None:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            until = None if days is None else datetime.utcnow() + timedelta(days=days)
            repo.grant_premium(user, until)
            return user

    def revoke_premium(self, telegram_id: int) -> User | None:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            repo.revoke_premium(user)
            return user

    def set_ban(self, telegram_id: int, banned: bool) -> User | None:
        with get_session() as session:
            repo = UserRepository(session)
            user = repo.get_by_telegram_id(telegram_id)
            if user is None:
                return None
            repo.set_ban(user, banned)
            return user

    def search(self, query: str) -> list[User]:
        with get_session() as session:
            return UserRepository(session).search(query)

    def list_all(self, page: int = 0, page_size: int = 10) -> list[User]:
        with get_session() as session:
            return UserRepository(session).list_all(page_size, page * page_size)

    def downgrade_expired_premium(self) -> int:
        with get_session() as session:
            repo = UserRepository(session)
            expired = repo.list_expired_premium(datetime.utcnow())
            for user in expired:
                repo.revoke_premium(user)
            return len(expired)

    def all_active_telegram_ids(self) -> list[int]:
        with get_session() as session:
            return UserRepository(session).all_telegram_ids()

    def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        with get_session() as session:
            return UserRepository(session).top_referrers(limit)


class FavoriteService:
    def toggle(self, user_id: int, movie_id: int) -> bool:
        """Returns True if the movie is now a favorite, False if it was removed."""
        with get_session() as session:
            repo = FavoriteRepository(session)
            if repo.is_favorite(user_id, movie_id):
                repo.remove(user_id, movie_id)
                return False
            repo.add(user_id, movie_id)
            return True

    def is_favorite(self, user_id: int, movie_id: int) -> bool:
        with get_session() as session:
            return FavoriteRepository(session).is_favorite(user_id, movie_id)

    def list_for_user(self, user_id: int, page: int = 0, page_size: int = 10) -> list[Movie]:
        with get_session() as session:
            return FavoriteRepository(session).list_for_user(user_id, page_size, page * page_size)


class HistoryService:
    def list_for_user(self, user_id: int, page: int = 0, page_size: int = 10) -> list[Movie]:
        with get_session() as session:
            return HistoryRepository(session).list_for_user(user_id, page_size, page * page_size)
