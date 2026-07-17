"""Central application configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            ids.add(int(chunk))
    return ids


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    database_url: str
    default_language: str
    backup_dir: Path
    log_dir: Path
    log_level: str
    bot_username: str
    data_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_dir", Path("./data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "123456789:AAExampleTokenReplaceMe":
        raise RuntimeError(
            "BOT_TOKEN is not configured. Copy .env.example to .env and set a real bot token."
        )

    return Settings(
        bot_token=token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/movies.db"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
        backup_dir=Path(os.getenv("BACKUP_DIR", "./data/backups")),
        log_dir=Path(os.getenv("LOG_DIR", "./data/logs")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        bot_username=os.getenv("BOT_USERNAME", "YourMovieBot"),
    )


settings = load_settings()
