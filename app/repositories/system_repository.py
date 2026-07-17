"""Repositories for Advertisement and Channel aggregates."""
from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Advertisement, Channel


class AdvertisementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Advertisement]:
        return list(self.session.execute(select(Advertisement).order_by(Advertisement.created_at.desc())).scalars().all())

    def list_active(self) -> list[Advertisement]:
        stmt = select(Advertisement).where(Advertisement.is_active.is_(True))
        return list(self.session.execute(stmt).scalars().all())

    def random_active(self) -> Advertisement | None:
        ads = self.list_active()
        return random.choice(ads) if ads else None

    def get_by_id(self, ad_id: int) -> Advertisement | None:
        return self.session.get(Advertisement, ad_id)

    def create(self, text: str, button_text: str | None, button_url: str | None) -> Advertisement:
        ad = Advertisement(text=text, button_text=button_text, button_url=button_url)
        self.session.add(ad)
        self.session.flush()
        return ad

    def toggle_active(self, ad_id: int) -> Advertisement | None:
        ad = self.get_by_id(ad_id)
        if ad is None:
            return None
        ad.is_active = not ad.is_active
        return ad

    def delete(self, ad_id: int) -> bool:
        ad = self.get_by_id(ad_id)
        if ad is None:
            return False
        self.session.delete(ad)
        return True


class ChannelRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Channel]:
        return list(self.session.execute(select(Channel)).scalars().all())

    def list_required(self) -> list[Channel]:
        stmt = select(Channel).where(Channel.is_required.is_(True))
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, channel_id: int) -> Channel | None:
        return self.session.get(Channel, channel_id)

    def create(self, chat_id: int, username: str | None, title: str) -> Channel:
        channel = Channel(chat_id=chat_id, username=username, title=title)
        self.session.add(channel)
        self.session.flush()
        return channel

    def delete(self, channel_id: int) -> bool:
        channel = self.get_by_id(channel_id)
        if channel is None:
            return False
        self.session.delete(channel)
        return True
