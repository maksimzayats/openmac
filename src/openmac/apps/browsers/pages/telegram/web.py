from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from json import dumps
from typing import Any, ClassVar

from bs4 import Tag
from typing_extensions import Self  # noqa: UP035

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement, must_get
from openmac.apps.browsers.pages.exceptions import InvalidDataError
from openmac.apps.browsers.pages.telegram.chat import TelegramWebChatPage
from openmac.apps.shared.base import BaseManager, UniqueIterationTracker

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class TelegramWebPage(BasePage):
    tab: IBrowserTab

    @classmethod
    def from_tab(cls, tab: IBrowserTab, **_kwargs: Any) -> Self:
        logger.info("Creating %s from tab url=%s", cls.__name__, tab.url)
        page = cls(tab=tab)

        _ = must_get(
            lambda: page.snapshot.select(".Spinner__inner"),
            exit_condition=lambda spinners: len(spinners) == 0,
            error_description="Loading spinners still found on the page, Telegram web might still be loading",
        )

        logger.info("%s initialized successfully for tab url=%s", cls.__name__, tab.url)
        return page

    @property
    def folders(self) -> TelegramFoldersManager:
        return TelegramFoldersManager(page=self)

    @property
    def chats(self) -> TelegramFolderChatsManager:
        return self.folders.all_chats.chats


@dataclass(slots=True, kw_only=True)
class TelegramChatsFolder(BasePageElement):
    page: TelegramWebPage
    element: Tag

    @property
    def name(self) -> str:
        tab_inner = must_get(
            lambda: self.element.find("span", class_="Tab_inner"),
            error_description="No Tab_inner element found in the folder tab",
        )

        try:
            return tab_inner.contents[0].text.strip()
        except IndexError as e:
            raise InvalidDataError(
                "No text content found in the Tab_inner element of the folder tab",
            ) from e

    @property
    def unread_messages(self) -> int:
        badge = self.element.find("span", class_="badge")
        if badge is None:
            return 0
        return int(badge.text.strip())

    @property
    def chats(self) -> TelegramFolderChatsManager:
        return TelegramFolderChatsManager(folder=self, page=self.page)

    def __repr__(self) -> str:
        return f"TelegramChatsFolder(name={self.name!r}, unread_messages={self.unread_messages})"


@dataclass(slots=True, kw_only=True)
class TelegramChat(BasePageElement):
    folder: TelegramChatsFolder
    element: Tag

    @property
    def href(self) -> str:
        button = must_get(
            lambda: self.element.find("a", class_="ListItem-button"),
            error_description="No ListItem-button link found in the chat element",
            tries=1,
        )

        return str(button["href"])

    @property
    def id(self) -> str:
        href = self.href
        if href.startswith("#"):
            return href[1:]

        raise InvalidDataError(f"Unexpected chat href format: {href}")

    @property
    def is_forum(self) -> bool:
        return "forum" in self.element["class"]

    @property
    def name(self) -> str:
        h3 = must_get(
            lambda: self.element.find("h3", class_="fullName"),
            error_description="No fullName element found in the chat element",
            tries=1,
        )

        return h3.text.strip()

    @property
    def unread_messages(self) -> int:
        badges = self.element.select(".chat-badge-transition span")
        if not badges:
            return 0

        badge = badges[
            -1
        ].text.strip()  # The last badge is the one with the number of unread messages

        if badge.endswith("K"):
            numeric_badge = re.sub(r"[^\d.]", "", badge[:-1])
            badge = float(numeric_badge) * 1000
        else:
            badge = re.sub(r"\D", "", badge)

        return int(badge)

    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager(chat=self, page=self.folder.page)

    def open(self) -> TelegramWebChatPage:
        logger.info("Opening Telegram chat id=%s name=%r href=%s", self.id, self.name, self.href)
        return self.folder.page.tab.window.tabs.open(
            url=f"https://web.telegram.org/a/{self.href}",
            wait_until_loaded=True,
        ).as_page(TelegramWebChatPage)

    def __repr__(self) -> str:
        return f"TelegramChat(id={self.id!r}, name={self.name!r}, unread_messages={self.unread_messages}, is_forum={self.is_forum})"


@dataclass(slots=True, kw_only=True)
class TelegramForumTopic(TelegramChat):
    chat: TelegramChat

    @property
    def is_forum(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"TelegramForumTopic(id={self.id!r}, name={self.name!r})"


# region Managers


@dataclass(slots=True, kw_only=True)
class TelegramFoldersManager(BaseManager[TelegramChatsFolder]):
    page: TelegramWebPage

    @property
    def active(self) -> TelegramChatsFolder:
        logger.debug("Resolving active Telegram folder")
        active_tab = must_get(
            lambda: self.page.snapshot.find("div", class_="Tab--active"),
            error_description="No active folder tab found",
        )

        return TelegramChatsFolder(
            page=self.page,
            element=active_tab,
        )

    @property
    def all_chats(self) -> TelegramChatsFolder:
        logger.debug("Selecting Telegram folder with the largest chat collection")
        return max(
            self.all,
            key=lambda folder: folder.chats.count,
        )

    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        logger.debug("Enumerating Telegram folders")
        folders = must_get(
            lambda: self.page.snapshot.find_all("div", class_="Tab"),
            error_description="No folder tabs found on the page",
            exit_condition=lambda tabs: len(tabs) > 0,
        )

        for tag in folders:
            yield TelegramChatsFolder(page=self.page, element=tag)


@dataclass(slots=True, kw_only=True)
class TelegramFolderChatsManager(BaseManager[TelegramChat]):
    _MAX_EMPTY_ITERATIONS_IN_A_ROW: ClassVar = 3
    """Define a maximum number of consecutive iterations without finding new chats before stopping the iteration. This is needed to avoid infinite loops in case of unexpected page structure changes or loading issues."""

    folder: TelegramChatsFolder
    page: TelegramWebPage

    def _iter_objects(self) -> Iterator[TelegramChat]:
        logger.info("Enumerating chats for Telegram folder name=%r", self.folder.name)
        tracker = UniqueIterationTracker[str]()

        self._click_folder()

        while True:
            tracker.new_iteration()
            if tracker.empty_iterations_in_a_row > self._MAX_EMPTY_ITERATIONS_IN_A_ROW:
                logger.warning(
                    "Stopping Telegram chat iteration for folder name=%r after %s empty iterations",
                    self.folder.name,
                    tracker.empty_iterations_in_a_row,
                )
                return

            chat_list = must_get(
                lambda: self.page.snapshot.select_one(".chat-list.Transition_slide-active"),
                error_description="No chat list found after clicking on the folder",
            )

            chats = must_get(
                lambda: chat_list.select("div.ListItem.Chat"),  # noqa: B023
                error_description="No chats found in the active folder",
            )

            for tag in chats:
                chat = TelegramChat(folder=self.folder, element=tag)
                if not tracker.add(chat.id):
                    continue
                logger.debug("Yielding Telegram chat id=%s name=%r", chat.id, chat.name)
                yield chat

            self._scroll_chat_list()

    def _click_folder(self) -> None:
        """Click on the folder tab to activate it."""

        logger.info("Activating Telegram folder name=%r", self.folder.name)
        folder_name = dumps(self.folder.name)
        tab_getter = f"""
        [...document.querySelectorAll(".Tab--interactive")]
            .find(
                el => el.querySelector(".Tab_inner")?.firstChild?.textContent?.trim() === {folder_name}
            )
        """

        self.page.real_click(tab_getter)

        must_get(
            lambda: self.page.folders.active,
            error_description="No active folder found after clicking on the folder tab",
            exit_condition=lambda active_tab: active_tab.name == self.folder.name,
        )
        logger.debug("Telegram folder name=%r is active", self.folder.name)

    def _scroll_chat_list(self) -> None:
        logger.debug("Scrolling Telegram chat list for folder name=%r", self.folder.name)
        self.page.tab.execute(
            """
            document.querySelector('.chat-list.Transition_slide-active').scrollTop += 1000;
            """,
        )


@dataclass(slots=True, kw_only=True)
class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    chat: TelegramChat
    page: TelegramWebPage

    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        if not self.chat.is_forum:
            logger.debug(
                "Telegram chat id=%s is not a forum; skipping topics iteration",
                self.chat.id,
            )
            return

        logger.info(
            "Enumerating forum topics for Telegram chat id=%s name=%r",
            self.chat.id,
            self.chat.name,
        )
        self._open_forum()

        topics = self.page.snapshot.select(f".ListItem:has(a[href^='#{self.chat.id}_'])")
        try:
            for tag in topics:
                topic = TelegramForumTopic(
                    folder=self.chat.folder,
                    chat=self.chat,
                    element=tag,
                )
                logger.debug("Yielding Telegram forum topic id=%s name=%r", topic.id, topic.name)
                yield topic
        finally:
            # close the forum topics list to restore the original page state
            self._close_forum()

    def _open_forum(self) -> None:
        logger.info(
            "Opening Telegram forum topics for chat id=%s name=%r",
            self.chat.id,
            self.chat.name,
        )
        chat_getter = f"""
        document.querySelector('.chat-list.Transition_slide-active a[href="{self.chat.href}"]')
        """

        self.page.real_click(chat_getter)

        _ = must_get(
            lambda: self.page.snapshot.select_one("#TopicListHeader .fullName"),
            error_description="No topic list header found after clicking on the forum chat",
            exit_condition=lambda header: (
                header is not None and header.text.strip() == self.chat.name
            ),
        )
        logger.debug("Telegram forum topics opened for chat id=%s", self.chat.id)

    def _close_forum(self) -> None:
        logger.debug("Closing Telegram forum topics for chat id=%s", self.chat.id)
        chat_getter = f"""
        document.querySelector('.chat-list.Transition_slide-active a[href="{self.chat.href}"]')
        """

        self.page.real_click(chat_getter)

        _ = must_get(
            lambda: self.page.snapshot.select_one("#TopicListHeader .fullName"),
            error_description="Topic list header still found after clicking on the forum chat to close it",
            exit_condition=lambda header: header is None,
        )
        logger.debug("Telegram forum topics closed for chat id=%s", self.chat.id)


# endregion Managers
