from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from time import sleep
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

    # region Properties

    @property
    def name(self) -> str:
        folder_data = self.page.get_object(
            selector=self.selector,
            values={
                "name": "element ? element.innerText.split('\\n')[0] : ''",
            },
        )

        return folder_data["name"]

    @property
    def number_of_unread_messages(self) -> int:
        data = self.page.get_object(
            selector=f"{self.selector} > .Tab_inner > .badge",
            values={
                "count": "element ? element.innerText : '0'",
            },
        )

        try:
            return int(data["count"])
        except ValueError:
            return 0

    # endregion Properties

    def click(
        self,
        *,
        wait_until_loaded: bool = True,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> Self:
        self.page.real_click(self.selector)

        if wait_until_loaded:
            start_time = time.perf_counter()

            while time.perf_counter() - start_time < timeout:
                if self.name == self.page.folders.active.name:
                    return self

                sleep(delay)

        return self

    @property
    def chats(self) -> TelegramChatsManager:
        return TelegramChatsManager(folder=self)


@dataclass(slots=True, kw_only=True)
class TelegramChat(BasePageElement):
    id: str
    folder: TelegramChatsFolder
    is_forum: bool

    @property
    def name(self) -> str:
        chat_data = self.folder.page.get_object(
            selector=f'a[href="#{self.id}"] .fullName',
            values={
                "name": "element ? element.innerText : null",
            },
        )

        name = chat_data["name"]

        if not name:
            raise ValueError("chat is unavailable")

        return name

    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager(chat=self)

    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager(chat=self)

    def _click(
        self,
        *,
        wait_until_loaded: bool = True,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> Self:
        self.folder.page.real_click(f"{self.selector} > a")

        if wait_until_loaded:
            start_time = time.perf_counter()

            while time.perf_counter() - start_time < timeout:
                print(f"{self.folder.chats.active.name = }")
                print(f"{self.name = }")
                if self.name == self.folder.chats.active.name:
                    return self

                sleep(delay)

        return self


@dataclass(slots=True, kw_only=True)
class TelegramForumTopic(BasePageElement):
    id: str
    chat: TelegramChat

    @property
    def name(self) -> str:
        pass


class TelegramChatMessage(BasePageElement):
    pass


# region Managers


@dataclass(slots=True, kw_only=True)
class TelegramFoldersManager(BaseManager[TelegramChatsFolder]):
    page: TelegramPage

    @property
    def active(self) -> TelegramChatsFolder:
        return TelegramChatsFolder(
            page=self.page,
            selector=".Tab--active",
        )

    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        folders_data = self.page.get_objects(
            selector=".Tab",
            values={
                "selector": "`.Tab:nth-of-type(${index + 1})`",
            },
        )

        for folder in folders_data:
            yield TelegramChatsFolder(
                page=self.page,
                selector=folder["selector"],
            )


@dataclass(slots=True, kw_only=True)
class TelegramChatsManager(BaseManager[TelegramChat]):
    folder: TelegramChatsFolder

    def _iter_objects(self) -> Iterator[TelegramChat]:
        chats_data = self.folder.page.get_objects(
            selector=".Transition_slide-active > div > .ListItem.Chat",
            values={
                "is_forum": "element.classList.contains('forum')",
                "href": "element.querySelector('a') ? element.querySelector('a').getAttribute('href') : ''",
            },
        )

        for chat in chats_data:
            yield TelegramChat(
                id=chat["href"].split("#")[-1],
                folder=self.folder,
                selector=f".ListItem.Chat:has(a[href={chat['href']}])",
                is_forum=chat["is_forum"],
            )


@dataclass(slots=True, kw_only=True)
class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    chat: TelegramChat

    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        if not self.chat.is_forum:
            return

        self.chat.folder.page.real_click(f'a[href="#{self.chat.id}"]')

        topics_data = self.chat.folder.page.get_objects(
            selector=f"a[href^='#{self.chat.id}_']",
            values={
                "href": "element.getAttribute('href') || ''",
                "selector": "`a[href='${element.getAttribute('href') || ''}']`",
            },
        )

        for topic in topics_data:
            yield TelegramForumTopic(
                id=topic["href"].split("#")[-1],
                selector=topic["selector"],
                chat=self.chat,
            )


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    chat: TelegramChat

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        raise NotImplementedError


# endregion Managers
