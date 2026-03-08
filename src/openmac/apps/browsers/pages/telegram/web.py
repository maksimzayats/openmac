from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from typing_extensions import Self  # noqa: UP035

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement
from openmac.apps.shared.base import BaseManager


@dataclass(slots=True, kw_only=True)
class TelegramPage(BasePage):
    tab: IBrowserTab

    @classmethod
    def from_tab(cls, tab: IBrowserTab, **_kwargs: Any) -> Self:
        return cls(tab=tab)

    @property
    def folders(self) -> TelegramFoldersManager:
        return TelegramFoldersManager(page=self)

    @property
    def chats(self) -> TelegramChatsManager:
        return self.folders.last.chats


@dataclass(slots=True, kw_only=True)
class TelegramChatsFolder(BasePageElement):
    page: TelegramPage

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def number_of_unread_messages(self) -> int:
        raise NotImplementedError

    @property
    def chats(self) -> TelegramChatsManager:
        return TelegramChatsManager(folder=self, page=self.page)


@dataclass(slots=True, kw_only=True)
class TelegramChat(BasePageElement):
    folder: TelegramChatsFolder

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def is_forum(self) -> bool:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager(chat=self, page=self.folder.page)

    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager(chat=self, page=self.folder.page)


@dataclass(slots=True, kw_only=True)
class TelegramForumTopic(BasePageElement):
    chat: TelegramChat

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramChatMessage(BasePageElement):
    chat: TelegramChat

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def content(self) -> str:
        raise NotImplementedError

    @property
    def sent_at(self) -> datetime:
        raise NotImplementedError

    @property
    def sender(self) -> TelegramChatMessageSender:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramChatMessageSender(BasePageElement):
    message: TelegramChatMessage

    @property
    def name(self) -> str:
        raise NotImplementedError


# region Managers


@dataclass(slots=True, kw_only=True)
class TelegramFoldersManager(BaseManager[TelegramChatsFolder]):
    page: TelegramPage

    @property
    def active(self) -> TelegramChatsFolder:
        raise NotImplementedError

    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramChatsManager(BaseManager[TelegramChat]):
    folder: TelegramChatsFolder
    page: TelegramPage

    def _iter_objects(self) -> Iterator[TelegramChat]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    chat: TelegramChat
    page: TelegramPage

    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    chat: TelegramChat
    page: TelegramPage

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        raise NotImplementedError


# endregion Managers
