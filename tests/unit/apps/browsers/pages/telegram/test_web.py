from __future__ import annotations

from typing import cast

from bs4 import BeautifulSoup

from openmac.apps.browsers.pages.telegram.web import TelegramChat, TelegramChatsFolder


def _build_chat(html: str) -> TelegramChat:
    soup = BeautifulSoup(html, "html.parser")
    chat_element = soup.select_one(".chat-item")
    assert chat_element is not None

    return TelegramChat(folder=cast("TelegramChatsFolder", None), element=chat_element)


def test_unread_messages_parses_k_suffix_badge() -> None:
    chat = _build_chat(
        """
        <div class="chat-item">
            <div class="chat-badge-transition">
                <span>1.2K</span>
            </div>
        </div>
        """,
    )

    assert chat.unread_messages == 1200


def test_unread_messages_parses_plain_integer_badge_with_separators() -> None:
    chat = _build_chat(
        """
        <div class="chat-item">
            <div class="chat-badge-transition">
                <span>1,234</span>
            </div>
        </div>
        """,
    )

    assert chat.unread_messages == 1234


def test_unread_messages_returns_zero_when_badge_is_missing() -> None:
    chat = _build_chat('<div class="chat-item"></div>')

    assert chat.unread_messages == 0
