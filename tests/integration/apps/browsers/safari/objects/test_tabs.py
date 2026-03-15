from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import suppress

import pytest
from appscript import CommandError

from openmac.apps.browsers.safari.objects.application import Safari
from openmac.apps.browsers.safari.objects.tabs import SafariTab


@pytest.fixture(scope="function")
def tab(safari: Safari) -> Generator[SafariTab]:
    window = safari.windows.new(url="https://www.google.com", preserve_focus=False)
    tab = window.current_tab
    tab.wait_until_loaded()

    try:
        yield tab
    finally:
        with suppress(CommandError):
            window.close()


@pytest.fixture(scope="function")
def new_tab_no_wait(safari: Safari) -> Generator[SafariTab]:
    window = safari.windows.new(url="https://www.google.com", preserve_focus=False)
    tab = window.current_tab

    try:
        yield tab
    finally:
        with suppress(CommandError):
            window.close()


def test_tab_wait_until_loaded(new_tab_no_wait: SafariTab) -> None:
    assert new_tab_no_wait.url == "https://www.google.com/"

    new_tab_no_wait.wait_until_loaded(timeout=10)

    assert new_tab_no_wait.url == "https://www.google.com/"
    assert not new_tab_no_wait.loading


def test_tab_close(new_tab_no_wait: SafariTab) -> None:
    assert new_tab_no_wait.url == "https://www.google.com/"

    new_tab_no_wait.close()

    deadline = time.perf_counter() + 2

    while True:
        try:
            _ = new_tab_no_wait.title
        except CommandError:
            return

        if time.perf_counter() > deadline:
            pytest.fail("Safari tab reference remained valid after close().")

        time.sleep(0.1)
