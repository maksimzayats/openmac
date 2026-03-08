from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any

from bs4 import Tag
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
    element: Annotated[
        Tag,
        """<div class="Tab Tab--interactive Tab--active"><span class="Tab_inner">All Chats<span class="badge Tab__badge--active">43</span><i class="platform animate" style="transform: none;"></i></span></div>""",
    ]

    @property
    def name(self) -> str:
        return self.element.find("span", class_="Tab_inner").contents[0].text.strip()

    @property
    def number_of_unread_messages(self) -> int:
        badge = self.element.find("span", class_="badge")
        if badge is None:
            return 0
        return int(badge.text.strip())

    @property
    def chats(self) -> TelegramChatsManager:
        return TelegramChatsManager(folder=self, page=self.page)

    def click(self) -> None:
        """Click on the folder tab to activate it."""

        tab_getter = f"""
        [...document.querySelectorAll(".Tab--interactive")]
            .find(el => el.innerText.includes("{self.name}"))
        """

        self.page.real_click(tab_getter)

    def __repr__(self) -> str:
        return f"TelegramChatsFolder(name={self.name!r}, number_of_unread_messages={self.number_of_unread_messages})"


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
    def element(
        self,
    ) -> Annotated[
        Tag,
        """
        <div class="TabList no-scrollbar">
          <div class="Tab Tab--interactive">
            <span class="Tab_inner">
              Work
              <span class="badge">3</span>
              <i class="platform" style="transform: none;"></i>
            </span>
          </div>

          <div class="Tab Tab--interactive">
            <span class="Tab_inner">
              Friends
              <span class="badge">12</span>
              <i class="platform"></i>
            </span>
          </div>

          <div class="Tab Tab--interactive">
            <span class="Tab_inner">
              Projects
              <span class="badge">7</span>
              <i class="platform"></i>
            </span>
          </div>

          <div class="Tab Tab--interactive">
            <span class="Tab_inner">
              Ideas
              <span class="badge">2</span>
              <i class="platform" style="transform: none;"></i>
            </span>
          </div>

          <div class="Tab Tab--interactive Tab--active">
            <span class="Tab_inner">
              All Messages
              <span class="badge Tab__badge--active">21</span>
              <i class="platform animate" style="transform: none;"></i>
            </span>
          </div>
        </div>
        """,
    ]:
        return self.page.snapshot.find("div", class_="TabList no-scrollbar")

    @property
    def active(self) -> TelegramChatsFolder:
        return TelegramChatsFolder(
            page=self.page,
            element=self.element.find("div", class_="Tab--active"),
        )

    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        for tag in self.element.find_all("div", class_="Tab"):
            yield TelegramChatsFolder(page=self.page, element=tag)


@dataclass(slots=True, kw_only=True)
class TelegramChatsManager(BaseManager[TelegramChat]):
    folder: TelegramChatsFolder
    page: TelegramPage

    @property
    def element(
        self,
    ) -> Annotated[
        Tag,
        """
        """,
    ]:
        raise NotImplementedError

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
