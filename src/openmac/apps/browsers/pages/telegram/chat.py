from __future__ import annotations

from collections.abc import Iterator
from copy import copy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, Final, Self

from bs4 import BeautifulSoup, Tag

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement, must_get
from openmac.apps.shared.base import BaseManager

LOCAL_TIMEZONE: Final = datetime.now().astimezone().tzinfo or UTC


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
            lambda: _get_tag_attribute_string(self.element, "data-message-id"),
            error_description="Message ID not found in message element",
            tries=1,
        )

    @property
    def content(self) -> str:
        text_content = self.element.select_one(".text-content")
        if text_content is None:
            return ""

        detached_text_content = copy(text_content)
        for removable in detached_text_content.select(".MessageMeta, .Reactions"):
            removable.decompose()

        return detached_text_content.get_text(" ", strip=True)

    @property
    def sent_at(self) -> datetime:
        time_element = must_get(
            lambda: self.element.select_one(".message-time"),
            error_description="Message time not found in message element",
            tries=1,
        )

        candidate_values = [
            _get_tag_attribute_string(time_element, "datetime"),
            _get_tag_attribute_string(time_element, "title"),
            _get_tag_attribute_string(time_element, "aria-label"),
            _get_tag_attribute_string(time_element.parent, "title")
            if isinstance(time_element.parent, Tag)
            else None,
            _get_tag_attribute_string(time_element.parent, "aria-label")
            if isinstance(time_element.parent, Tag)
            else None,
            time_element.text.strip(),
        ]

        for value in candidate_values:
            parsed_datetime = _parse_telegram_message_datetime(value)
            if parsed_datetime is not None:
                return parsed_datetime

        msg = f"Unsupported Telegram message timestamp format: {time_element.text.strip()!r}"
        raise RuntimeError(msg)

    @property
    def sender(self) -> TelegramChatMessageSender:
        return TelegramChatMessageSender(message=self)

    @property
    def reply_preview(self) -> TelegramChatMessageReplyPreview | None:
        reply_element = self.element.select_one(".message-subheader .EmbeddedMessage")
        if reply_element is None:
            return None

        return TelegramChatMessageReplyPreview(
            message=self,
            element=reply_element,
        )

    def __repr__(self) -> str:
        return f"TelegramChatMessage(id={self.id!r} content={self.content!r})"


@dataclass(slots=True, kw_only=True)
class TelegramChatMessageSender(BasePageElement):
    message: TelegramChatMessage

    @property
    def name(self) -> str:
        sender_title = must_get(
            lambda: self.message.element.select_one(".sender-title"),
            error_description="Sender name not found in message element",
            tries=1,
        )

        return sender_title.text.strip()


@dataclass(slots=True, kw_only=True)
class TelegramChatMessageReplyPreview(BasePageElement):
    message: TelegramChatMessage
    element: Tag

    @property
    def content(self) -> str:
        embedded_text = must_get(
            lambda: self.element.select_one(".embedded-text-wrapper"),
            error_description="Reply preview content not found in message element",
            tries=1,
        )

        return embedded_text.get_text(" ", strip=True)

    @property
    def sender_name(self) -> str:
        embedded_sender = must_get(
            lambda: self.element.select_one(".embedded-sender"),
            error_description="Reply preview sender not found in message element",
            tries=1,
        )

        return embedded_sender.text.strip()

    def __repr__(self) -> str:
        return (
            "TelegramChatMessageReplyPreview("
            f"sender_name={self.sender_name!r}, content={self.content!r})"
        )


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


def _parse_telegram_message_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    normalized_value = value.strip()
    if not normalized_value:
        return None

    parsed_datetime: datetime | None = None

    try:
        parsed_datetime = datetime.fromisoformat(normalized_value)
        if parsed_datetime.tzinfo is None:
            parsed_datetime = parsed_datetime.replace(tzinfo=LOCAL_TIMEZONE)
    except ValueError:
        pass

    if parsed_datetime is None:
        parsed_datetime = _parse_telegram_datetime_with_formats(
            normalized_value,
            ("%H:%M", "%I:%M %p"),
        )

    if parsed_datetime is None:
        parsed_datetime = _parse_telegram_absolute_datetime(normalized_value)

    if parsed_datetime is None:
        soup = BeautifulSoup(normalized_value, "lxml")
        plain_text_value = soup.get_text(" ", strip=True)
        if plain_text_value != normalized_value:
            parsed_datetime = _parse_telegram_message_datetime(plain_text_value)

    return parsed_datetime


def _get_tag_attribute_string(tag: Tag, attribute: str) -> str | None:
    value = tag.get(attribute)
    if value is None:
        return None
    if isinstance(value, list):
        return " ".join(value)

    return value


def _parse_telegram_absolute_datetime(value: str) -> datetime | None:
    supported_formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y, %H:%M",
        "%b %d, %Y at %H:%M",
        "%B %d, %Y at %H:%M",
        "%b %d, %Y, %H:%M",
        "%B %d, %Y, %H:%M",
    )

    return _parse_telegram_datetime_with_formats(value, supported_formats)


def _parse_telegram_datetime_with_formats(
    value: str,
    formats: tuple[str, ...],
) -> datetime | None:
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=LOCAL_TIMEZONE)
        except ValueError:
            continue

    return None
