"""Business logic for admin-only operations: broadcast, statistics, backups, ads, channels."""
from __future__ import annotations

import asyncio
import csv
import io
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from telegram import Bot
from telegram.error import Forbidden, TelegramError

from app.config import settings
from app.database.models import Advertisement, Channel
from app.database.session import engine, get_session
from app.logging_config import get_logger
from app.repositories.movie_repository import CategoryRepository, GenreRepository, MovieRepository
from app.repositories.system_repository import AdvertisementRepository, ChannelRepository
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


@dataclass
class BroadcastResult:
    total: int
    sent: int
    failed: int


class BroadcastService:
    async def send_to_all(self, bot: Bot, text: str) -> BroadcastResult:
        user_ids = _all_telegram_ids()
        sent = 0
        failed = 0
        for telegram_id in user_ids:
            try:
                await bot.send_message(chat_id=telegram_id, text=text)
                sent += 1
            except Forbidden:
                failed += 1
            except TelegramError as exc:
                logger.warning("Broadcast failed for %s: %s", telegram_id, exc)
                failed += 1
            await asyncio.sleep(0.05)
        return BroadcastResult(total=len(user_ids), sent=sent, failed=failed)


def _all_telegram_ids() -> list[int]:
    with get_session() as session:
        return UserRepository(session).all_telegram_ids()


class StatisticsService:
    def snapshot(self) -> dict:
        with get_session() as session:
            user_repo = UserRepository(session)
            movie_repo = MovieRepository(session)
            category_repo = CategoryRepository(session)
            genre_repo = GenreRepository(session)
            return {
                "total_users": user_repo.count(),
                "premium_users": user_repo.count_premium(),
                "banned_users": user_repo.count_banned(),
                "total_movies": movie_repo.count(),
                "total_categories": len(category_repo.list_all()),
                "total_genres": len(genre_repo.list_all()),
            }

    def export_csv(self) -> bytes:
        with get_session() as session:
            movies = MovieRepository(session).top_rated(limit=10_000) + MovieRepository(session).latest(
                limit=10_000
            )
        seen: dict[int, object] = {m.id: m for m in movies}
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "code", "title", "year", "views", "rating_avg", "rating_count", "is_premium"])
        for movie in seen.values():
            writer.writerow(
                [movie.id, movie.code, movie.title, movie.year, movie.views, movie.rating_avg, movie.rating_count, movie.is_premium]
            )
        return buffer.getvalue().encode("utf-8")


class BackupService:
    def _sqlite_path(self) -> Path | None:
        if not settings.database_url.startswith("sqlite"):
            return None
        raw = settings.database_url.split("sqlite:///")[-1]
        return Path(raw)

    def create_backup(self) -> Path:
        db_path = self._sqlite_path()
        if db_path is None or not db_path.exists():
            raise RuntimeError("Backup is only supported for SQLite databases in this deployment.")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = settings.backup_dir / f"backup_{timestamp}.db"
        engine.dispose()
        shutil.copy2(db_path, backup_path)
        return backup_path

    def list_backups(self) -> list[Path]:
        return sorted(settings.backup_dir.glob("backup_*.db"), reverse=True)

    def restore_backup(self, source: Path) -> None:
        db_path = self._sqlite_path()
        if db_path is None:
            raise RuntimeError("Restore is only supported for SQLite databases in this deployment.")
        engine.dispose()
        shutil.copy2(source, db_path)


class AdvertisementService:
    def list_all(self) -> list[Advertisement]:
        with get_session() as session:
            return AdvertisementRepository(session).list_all()

    def random_active(self) -> Advertisement | None:
        with get_session() as session:
            return AdvertisementRepository(session).random_active()

    def create(self, text: str, button_text: str | None, button_url: str | None) -> Advertisement:
        with get_session() as session:
            return AdvertisementRepository(session).create(text, button_text, button_url)

    def toggle(self, ad_id: int) -> Advertisement | None:
        with get_session() as session:
            return AdvertisementRepository(session).toggle_active(ad_id)

    def delete(self, ad_id: int) -> bool:
        with get_session() as session:
            return AdvertisementRepository(session).delete(ad_id)


class ChannelService:
    def list_all(self) -> list[Channel]:
        with get_session() as session:
            return ChannelRepository(session).list_all()

    def list_required(self) -> list[Channel]:
        with get_session() as session:
            return ChannelRepository(session).list_required()

    def add(self, chat_id: int, username: str | None, title: str) -> Channel:
        with get_session() as session:
            return ChannelRepository(session).create(chat_id, username, title)

    def delete(self, channel_id: int) -> bool:
        with get_session() as session:
            return ChannelRepository(session).delete(channel_id)
