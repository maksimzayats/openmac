from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from time import sleep
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
        self._wait_for_click_response()

    def _wait_for_click_response(self) -> None:
        for _ in range(10):
            active = self.page.folders.active
            if active.name == self.name:
                return

            sleep(0.1)

    def __repr__(self) -> str:
        return f"TelegramChatsFolder(name={self.name!r}, number_of_unread_messages={self.number_of_unread_messages})"


@dataclass(slots=True, kw_only=True)
class TelegramChat(BasePageElement):
    folder: TelegramChatsFolder
    element: Annotated[
        Tag,
        """
        <div class="ListItem Chat chat-item-clickable private has-ripple" style="top: 0px;">
              <a class="ListItem-button" href="#111111111" tabindex="0">
                <div class="ripple-container"></div>

                <div class="status status-clickable">
                  <div class="Avatar peer-color-2" data-peer-id="111111111" style="--_size: 54px;">
                    <div class="inner">
                      <span class="letters">A</span>
                    </div>
                  </div>
                </div>

                <div class="info">
                  <div class="info-row">
                    <div class="title">
                      <h3 class="fullName">Alice Johnson</h3>
                    </div>

                    <div class="separator"></div>

                    <div class="LastMessageMeta">
                      <span class="time">10:42</span>
                    </div>
                  </div>

                  <div class="subtitle">
                    <p class="last-message">
                      <span class="last-message-summary">
                        Let's push the release today 🚀
                      </span>
                    </p>

                    <div class="chat-badge-transition shown open">
                      <div>
                        <span>2</span>
                      </div>
                    </div>
                  </div>
                </div>
              </a>
            </div>
            """,
    ]

    @property
    def href(self) -> str:
        return self.element.find("a", class_="ListItem-button")["href"]

    @property
    def id(self) -> str:
        href = self.href
        if href.startswith("#"):
            return href[1:]

        raise ValueError(f"Unexpected chat href format: {href}")

    @property
    def is_forum(self) -> bool:
        return "forum" in self.element["class"]

    @property
    def name(self) -> str:
        return self.element.find("h3", class_="fullName").text.strip()

    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager(chat=self, page=self.folder.page)

    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager(chat=self, page=self.folder.page)

    def click(self) -> None:
        """Click on the chat to open it."""

        chat_getter = f"""
        document.querySelector('.chat-list.Transition_slide-active a[href="{self.href}"]')
        """

        self.folder.click()
        self.folder.page.real_click(chat_getter)
        self._wait_for_click_response()

    def _wait_for_click_response(self) -> None:
        for _ in range(10):
            if self.is_forum:
                element = self.folder.page.snapshot.select_one("#TopicListHeader .fullName")
            else:
                element = self.folder.page.snapshot.select_one(
                    ".MiddleHeader .Transition_slide-active .fullName",
                )

            if element and element.text.strip() == self.name:
                return

            sleep(0.1)

    def __repr__(self) -> str:
        return f"TelegramChat(id={self.id!r}, name={self.name!r}, is_forum={self.is_forum})"


@dataclass(slots=True, kw_only=True)
class TelegramForumTopic(TelegramChat):
    chat: TelegramChat

    @property
    def is_forum(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"TelegramForumTopic(id={self.id!r}, name={self.name!r})"


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
        <div class="Transition_slide chat-list custom-scroll Transition_slide-active">
          <div style="position: relative;">

            <!-- CHAT 1 -->
            <div class="ListItem Chat chat-item-clickable private has-ripple" style="top: 0px;">
              <a class="ListItem-button" href="#111111111" tabindex="0">
                <div class="ripple-container"></div>

                <div class="status status-clickable">
                  <div class="Avatar peer-color-2" data-peer-id="111111111" style="--_size: 54px;">
                    <div class="inner">
                      <span class="letters">A</span>
                    </div>
                  </div>
                </div>

                <div class="info">
                  <div class="info-row">
                    <div class="title">
                      <h3 class="fullName">Alice Johnson</h3>
                    </div>

                    <div class="separator"></div>

                    <div class="LastMessageMeta">
                      <span class="time">10:42</span>
                    </div>
                  </div>

                  <div class="subtitle">
                    <p class="last-message">
                      <span class="last-message-summary">
                        Let's push the release today 🚀
                      </span>
                    </p>

                    <div class="chat-badge-transition shown open">
                      <div>
                        <span>2</span>
                      </div>
                    </div>
                  </div>
                </div>
              </a>
            </div>


            <!-- CHAT 2 -->
            <div class="ListItem Chat chat-item-clickable group has-ripple" style="top: 72px;">
              <a class="ListItem-button" href="#-100222222222" tabindex="0">
                <div class="ripple-container"></div>

                <div class="status status-clickable">
                  <div class="Avatar peer-color-5" data-peer-id="-100222222222" style="--_size: 54px;">
                    <div class="inner">
                      <span class="letters">D</span>
                    </div>
                  </div>
                </div>

                <div class="info">
                  <div class="info-row">
                    <div class="title">
                      <h3 class="fullName">Dev Team</h3>
                    </div>

                    <i class="icon icon-muted"></i>

                    <div class="separator"></div>

                    <div class="LastMessageMeta">
                      <span class="time">09:17</span>
                    </div>
                  </div>

                  <div class="subtitle">
                    <p class="last-message">
                      <span class="sender-name">Mike</span>
                      <span class="colon">:</span>
                      <span class="last-message-summary">
                        CI pipeline finished successfully
                      </span>
                    </p>

                    <div class="chat-badge-transition shown open">
                      <div>
                        <span>18</span>
                      </div>
                    </div>
                  </div>
                </div>
              </a>
            </div>


            <!-- CHAT 3 -->
            <div class="ListItem Chat chat-item-clickable private has-ripple" style="top: 144px;">
              <a class="ListItem-button" href="#333333333" tabindex="0">
                <div class="ripple-container"></div>

                <div class="status status-clickable">
                  <div class="Avatar peer-color-8" data-peer-id="333333333" style="--_size: 54px;">
                    <div class="inner">
                      <span class="letters">S</span>
                    </div>
                  </div>
                </div>

                <div class="info">
                  <div class="info-row">
                    <div class="title">
                      <h3 class="fullName">Sarah Lee</h3>
                    </div>

                    <div class="separator"></div>

                    <div class="LastMessageMeta">
                      <span class="time">Yesterday</span>
                    </div>
                  </div>

                  <div class="subtitle">
                    <p class="last-message">
                      <span class="last-message-summary">
                        Are we still meeting tomorrow?
                      </span>
                    </p>
                  </div>
                </div>
              </a>
            </div>


            <!-- CHAT 4 -->
            <div class="ListItem Chat chat-item-clickable group has-ripple" style="top: 216px;">
              <a class="ListItem-button" href="#-100444444444" tabindex="0">

                <div class="ripple-container"></div>

                <div class="status status-clickable">
                  <div class="Avatar peer-color-3" data-peer-id="-100444444444" style="--_size: 54px;">
                    <div class="inner">
                      <span class="letters">P</span>
                    </div>
                  </div>
                </div>

                <div class="info">
                  <div class="info-row">
                    <div class="title">
                      <h3 class="fullName">Product Discussions</h3>
                    </div>

                    <div class="separator"></div>

                    <div class="LastMessageMeta">
                      <span class="time">Sun</span>
                    </div>
                  </div>

                  <div class="subtitle">
                    <p class="last-message">
                      <span class="sender-name">Anna</span>
                      <span class="colon">:</span>
                      <span class="last-message-summary">
                        Let's validate the idea with users first
                      </span>
                    </p>

                    <div class="chat-badge-transition shown open">
                      <div>
                        <span>5</span>
                      </div>
                    </div>
                  </div>
                </div>

              </a>
            </div>

          </div>
        </div>
        """,
    ]:
        self.folder.click()
        return self.page.snapshot.select_one(".chat-list.Transition_slide-active")

    def _iter_objects(self) -> Iterator[TelegramChat]:
        for tag in self.element.select("div.ListItem.Chat"):
            yield TelegramChat(folder=self.folder, element=tag)


@dataclass(slots=True, kw_only=True)
class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    chat: TelegramChat
    page: TelegramPage

    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        if not self.chat.is_forum:
            return

        self.chat.click()
        topics = self.page.snapshot.select(f".ListItem:has(a[href^='#{self.chat.id}_'])")
        try:
            for tag in topics:
                yield TelegramForumTopic(
                    folder=self.chat.folder,
                    chat=self.chat,
                    element=tag,
                )
        finally:
            # close the forum topics list to restore the original page state
            self.chat.click()


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    chat: TelegramChat
    page: TelegramPage

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        raise NotImplementedError


# endregion Managers
