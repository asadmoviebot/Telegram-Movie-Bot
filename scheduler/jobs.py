"""APScheduler background jobs: automatic backups and premium expiry sweeps."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.logging_config import get_logger
from app.services.admin_service import BackupService
from app.services.user_service import UserService

logger = get_logger(__name__)
backup_service = BackupService()
user_service = UserService()


def _run_daily_backup() -> None:
    try:
        path = backup_service.create_backup()
        logger.info("Scheduled backup created at %s", path)
    except RuntimeError as exc:
        logger.warning("Scheduled backup skipped: %s", exc)


def _run_premium_sweep() -> None:
    count = user_service.downgrade_expired_premium()
    if count:
        logger.info("Downgraded %d expired premium subscriptions", count)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(_run_daily_backup, CronTrigger(hour=3, minute=0), id="daily_backup", replace_existing=True)
    scheduler.add_job(_run_premium_sweep, IntervalTrigger(hours=1), id="premium_sweep", replace_existing=True)
    return scheduler
