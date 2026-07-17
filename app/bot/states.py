"""Conversation state constants used across ConversationHandlers."""
from __future__ import annotations

from enum import IntEnum, auto


class SearchStates(IntEnum):
    WAITING_QUERY = auto()
    WAITING_CODE = auto()


class CommentStates(IntEnum):
    WAITING_TEXT = auto()


class MovieAdminStates(IntEnum):
    TITLE = auto()
    DESCRIPTION = auto()
    YEAR = auto()
    DURATION = auto()
    QUALITY = auto()
    CATEGORY = auto()
    GENRES = auto()
    PREMIUM = auto()
    POSTER = auto()
    VIDEO = auto()
    CONFIRM = auto()
    EDIT_FIELD = auto()
    EDIT_VALUE = auto()


class CategoryAdminStates(IntEnum):
    NAME_UZ = auto()
    NAME_EN = auto()
    NAME_RU = auto()


class GenreAdminStates(IntEnum):
    NAME_UZ = auto()
    NAME_EN = auto()
    NAME_RU = auto()


class BroadcastStates(IntEnum):
    WAITING_TEXT = auto()
    CONFIRM = auto()


class PremiumAdminStates(IntEnum):
    WAITING_USER = auto()
    WAITING_DAYS = auto()


class BanAdminStates(IntEnum):
    WAITING_USER = auto()


class AdvertisementAdminStates(IntEnum):
    TEXT = auto()
    BUTTON_TEXT = auto()
    BUTTON_URL = auto()


class ChannelAdminStates(IntEnum):
    WAITING_FORWARD = auto()


class RestoreStates(IntEnum):
    WAITING_FILE = auto()


CANCEL_COMMANDS = ("/cancel", "❌ Cancel", "❌ Bekor qilish", "❌ Отмена")
