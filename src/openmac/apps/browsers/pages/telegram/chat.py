from __future__ import annotations

import logging
from collections.abc import Iterator
from copy import copy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Final, Self

from bs4 import BeautifulSoup, Tag

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement, must_get
from openmac.apps.browsers.pages.exceptions import InvalidDataError
from openmac.apps.shared.base import BaseManager, UniqueIterationTracker

LOCAL_TIMEZONE: Final = datetime.now().astimezone().tzinfo or UTC
TIME_ONLY_YEAR: Final = 1900
logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class TelegramWebChatPage(BasePage):
    @property
    def messages(self) -> TelegramChatMessagesManagerFactory:
        return TelegramChatMessagesManagerFactory(page=self)

    @classmethod
    def from_tab(cls, tab: IBrowserTab, **_kwargs: Any) -> Self:
        logger.info("Creating %s from tab url=%s", cls.__name__, tab.url)
        page = cls(tab=tab)

        _ = must_get(
            lambda: page.snapshot.select_one(".ChatInfo .fullName"),
            error_description="Chat title element not found, is this a valid Telegram Web chat page?",
        )

        logger.info("%s initialized successfully for tab url=%s", cls.__name__, tab.url)
        return page


@dataclass(slots=True, kw_only=True)
class TelegramChatMessage(BasePageElement):
    page: TelegramWebChatPage
    element: Tag

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
        raise InvalidDataError(msg)

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
class TelegramChatMessagesManagerFactory:
    page: TelegramWebChatPage

    def last(self, messages_limit: int) -> TelegramChatMessagesManager:
        logger.info("Preparing to load last %s Telegram messages", messages_limit)
        self._go_to_bottom()

        return TelegramChatMessagesManager(page=self.page, messages_limit=messages_limit)

    def _go_to_bottom(self) -> None:
        logger.info("Scrolling Telegram chat to the bottom before reading recent messages")
        _button = must_get(
            lambda: self.page.snapshot.select_one(
                ".middle-column-footer button:has(.icon-arrow-down)",
            ),
            error_description="Load more messages button not found at the bottom of the chat",
        )

        _opacity = must_get(
            lambda: self.page.tab.execute(
                'window.getComputedStyle(document.querySelector(".middle-column-footer button:has(.icon-arrow-down)").parentElement.parentElement).opacity',
            ),
            error_description="Failed to get opacity of the load more messages button container",
            exit_condition=lambda opacity: opacity == "1",
            tries=20,
            raise_error=False,
        )

        self.page.real_click(
            "document.querySelector('.middle-column-footer button:has(.icon-arrow-down)')",
        )

        _opacity = must_get(
            lambda: self.page.tab.execute(
                'window.getComputedStyle(document.querySelector(".middle-column-footer button:has(.icon-arrow-down)").parentElement.parentElement).opacity',
            ),
            error_description="Failed to get opacity of the load more messages button container after clicking it",
            exit_condition=lambda opacity: opacity == "0",
        )
        logger.debug("Telegram chat bottom jump completed")


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    _MAX_EMPTY_ITERATIONS_IN_A_ROW: ClassVar = 3

    page: TelegramWebChatPage
    messages_limit: int

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        logger.info("Enumerating up to %s Telegram messages", self.messages_limit)
        tracker = UniqueIterationTracker[str]()

        while len(tracker) < self.messages_limit:
            tracker.new_iteration()
            if tracker.empty_iterations_in_a_row > self._MAX_EMPTY_ITERATIONS_IN_A_ROW:
                logger.warning(
                    "Stopping Telegram message iteration after %s empty iterations",
                    tracker.empty_iterations_in_a_row,
                )
                return

            try:
                messages_tags = must_get(
                    lambda: self.page.snapshot.select(".messages-container .message-list-item"),
                    error_description="No messages found in the chat",
                    exit_condition=lambda msgs: len(msgs) > 0,
                )
            except InvalidDataError:
                logger.warning("No Telegram messages available to iterate")
                return

            message: TelegramChatMessage | None = None
            for message_tag in messages_tags[::-1]:
                message = TelegramChatMessage(
                    element=message_tag,
                    page=self.page,
                )

                if not tracker.add(message.id):
                    continue

                logger.debug("Yielding Telegram message id=%s", message.id)
                yield message
                if len(tracker) >= self.messages_limit:
                    return

            if message is not None:
                self._scroll_to_message(message)

    def _scroll_to_message(self, message: TelegramChatMessage) -> None:
        logger.debug("Scrolling Telegram chat to message id=%s", message.id)
        self.page.tab.execute(
            f'document.querySelector("#message-{message.id}").scrollIntoView()',
        )

        must_get(
            lambda: self.page.is_element_visible(
                f"document.querySelector('#message-{message.id}')",
            ),
            error_description=f"Failed to scroll to message with ID {message.id!r}",
            exit_condition=lambda visible: visible is True,
            tries=20,
            raise_error=False,
        )
        logger.debug("Finished scroll attempt to Telegram message id=%s", message.id)


def _parse_telegram_message_datetime(value: str | None) -> datetime | None:
    if value is None:
        logger.debug("Telegram message datetime parsing skipped for None value")
        return None

    normalized_value = value.strip()
    if not normalized_value:
        logger.debug("Telegram message datetime parsing skipped for empty value")
        return None

    logger.debug("Attempting to parse Telegram message datetime value=%r", normalized_value)
    parsed_datetime = _parse_telegram_message_datetime_value(normalized_value)
    if parsed_datetime is None:
        parsed_datetime = _parse_telegram_message_datetime_html_fallback(normalized_value)

    if parsed_datetime is not None:
        logger.debug(
            "Parsed Telegram message datetime value=%r into %s",
            normalized_value,
            parsed_datetime.isoformat(),
        )
    else:
        logger.warning("Failed to parse Telegram message datetime value=%r", normalized_value)

    return parsed_datetime


def _parse_telegram_message_datetime_value(value: str) -> datetime | None:
    parsed_datetime = _parse_telegram_iso_datetime(value)
    if parsed_datetime is not None:
        return parsed_datetime

    parsed_datetime = _parse_telegram_time_only_datetime(value)
    if parsed_datetime is not None:
        return parsed_datetime

    return _parse_telegram_absolute_datetime(value)


def _parse_telegram_message_datetime_html_fallback(value: str) -> datetime | None:
    soup = BeautifulSoup(value, "lxml")
    plain_text_value = soup.get_text(" ", strip=True)
    if plain_text_value == value:
        return None

    logger.debug(
        "Retrying Telegram datetime parsing with stripped HTML text value=%r",
        plain_text_value,
    )
    return _parse_telegram_message_datetime(plain_text_value)


def _parse_telegram_iso_datetime(value: str) -> datetime | None:
    try:
        parsed_datetime = datetime.fromisoformat(value)
    except ValueError:
        logger.debug("Telegram datetime value=%r is not ISO format", value)
        return None

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=LOCAL_TIMEZONE)

    return parsed_datetime


def _parse_telegram_time_only_datetime(value: str) -> datetime | None:
    parsed_datetime = _parse_telegram_datetime_with_formats(
        value,
        ("%H:%M", "%I:%M %p"),
    )
    if parsed_datetime is None or parsed_datetime.year != TIME_ONLY_YEAR:
        return parsed_datetime

    today = datetime.now(parsed_datetime.tzinfo)
    return parsed_datetime.replace(
        year=today.year,
        month=today.month,
        day=today.day,
    )


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
            logger.debug(
                "Trying Telegram datetime format %r for value=%r",
                date_format,
                value,
            )
            return datetime.strptime(value, date_format).replace(tzinfo=LOCAL_TIMEZONE)
        except ValueError:
            continue

    return None
