from __future__ import annotations

from collections.abc import Generator
from contextlib import suppress
from time import sleep

import pytest
from appscript import CommandError

from openmac import IBrowserTab, Safari
from openmac.apps.browsers.pages.telegram.web import TelegramWebPage


@pytest.fixture(scope="function")
def telegram_tab(safari: Safari) -> Generator[IBrowserTab]:
    tab = safari.tabs.open("https://web.telegram.org/a/", wait_until_loaded=True)

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
def telegram_page(telegram_tab: IBrowserTab) -> TelegramWebPage:
    return telegram_tab.as_page(TelegramWebPage)


def test_chat_folders(telegram_page: TelegramWebPage) -> None:
    folder_names = [folder.name for folder in telegram_page.folders]

    assert "All Chats" in folder_names


def test_click_chat_folder(telegram_page: TelegramWebPage) -> None:
    active_folder_name_before = telegram_page.folders.active.name

    all_chats_folder = telegram_page.folders.filter(name="All Chats").first
    all_chats_folder.click()

    active_folder_name_after = telegram_page.folders.active.name

    assert active_folder_name_before != active_folder_name_after
