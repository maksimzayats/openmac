from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Self

from bs4 import Tag

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement, must_get
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
    page: TelegramWebChatPage
    element: Annotated[
        Tag,
        """
        <div id="message-999999" class="Message message-list-item first-in-group allow-selection last-in-group has-reply shown open" data-message-id="999999">

          <div class="bottom-marker" data-message-id="999999"></div>

          <div class="message-select-control no-selection"></div>

          <div class="message-content-wrapper can-select-text">

            <div class="message-content peer-color-4 text has-subheader has-reactions has-shadow has-solid-background has-appendix has-footer" dir="auto">

              <div class="content-inner with-subheader">

                <!-- SENDER -->
                <div class="message-title">
                  <span class="message-title-name-container interactive">
                    <span class="forward-title-container"></span>
                    <span class="message-title-name">
                      <span class="sender-title">John Dev</span>
                    </span>
                  </span>
                  <div class="title-spacer"></div>
                </div>

                <!-- REPLY PREVIEW -->
                <div class="message-subheader">

                  <div class="EmbeddedMessage no-selection">

                    <div class="message-text">

                      <p class="embedded-text-wrapper">
                        Do you know a good coworking near the beach?
                      </p>

                      <div class="message-title">
                        <span class="embedded-sender-wrapper">
                          <span class="embedded-sender">Anna</span>
                        </span>
                      </div>

                    </div>

                  </div>

                </div>

                <!-- MESSAGE TEXT -->
                <div class="text-content clearfix with-meta">

                  I heard Phuket has some nice remote-worker cafés ☕

                  <!-- REACTIONS -->
                  <div class="Reactions">

                    <button class="Button message-reaction tiny primary">

                      <div class="ReactionStaticEmoji">

                        👍

                      </div>

                    </button>

                    <span class="MessageMeta reactions-offset">
                      <span class="message-time">14:21</span>
                    </span>

                  </div>

                </div>

              </div>

            </div>

          </div>

        </div>
        """,
    ]

    @property
    def id(self) -> str:
        return must_get(
            lambda: self.element["data-message-id"],
            error_description="Message ID not found in message element",
            tries=1,
        )

    @property
    def content(self) -> str:
        raise NotImplementedError

    @property
    def sent_at(self) -> datetime:
        raise NotImplementedError

    @property
    def sender(self) -> TelegramChatMessageSender:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"TelegramChatMessage(id={self.id!r} content={self.content!r})"


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
        try:
            messages = must_get(
                lambda: self.page.snapshot.select(".messages-container .message-list-item"),
                error_description="No messages found in the chat",
                exit_condition=lambda msgs: len(msgs) > 0,
            )
        except RuntimeError:
            return

        for message in messages:
            yield TelegramChatMessage(
                element=message,
                page=self.page,
            )
