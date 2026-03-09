from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement
from openmac.apps.shared.base import BaseManager


@dataclass(slots=True, kw_only=True)
class TelegramWebChatPage(BasePage):
    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager(page=self)

    @classmethod
    def from_tab(cls, tab: IBrowserTab, **_kwargs: Any) -> Self:
        return cls(tab=tab)


@dataclass(slots=True, kw_only=True)
class TelegramChatMessage(BasePageElement):
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


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    page: TelegramWebChatPage

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        messages_container = self.page.snapshot.select_one(".messages-container")
        messages = messages_container.select(".message-content-wrapper")

        print(len(messages))

        return

        yield
