from __future__ import annotations

from collections.abc import Generator
from contextlib import suppress
from time import sleep

import pytest
from appscript import CommandError

from openmac import IBrowserTab, Safari
from openmac.apps.browsers.pages.telegram.chat import TelegramWebChatPage


@pytest.fixture(scope="function")
def telegram_chat_tab(safari: Safari) -> Generator[IBrowserTab]:
    tab = safari.tabs.open("https://web.telegram.org/a/#850434834", wait_until_loaded=True)

    for _ in range(50):
        if 'id="LeftColumn"' in tab.source:
            break

        sleep(0.1)

    try:
        yield tab
    finally:
        with suppress(CommandError):
            tab.close()


@pytest.fixture(scope="function")
def telegram_chat_page(telegram_chat_tab: IBrowserTab) -> TelegramWebChatPage:
    return telegram_chat_tab.as_page(TelegramWebChatPage)


def test_chat_messages(telegram_chat_page: TelegramWebChatPage) -> None:
    messages = telegram_chat_page.messages.last(1000).all
    assert len(messages) > 0

    message_texts = [message.content for message in messages]
    assert "/start" in message_texts
