from __future__ import annotations

from collections.abc import Generator
from contextlib import suppress

import pytest
from appscript import CommandError

from openmac.apps.chrome.objects.application import Chrome
from openmac.apps.chrome.objects.tabs import ChromeTab


@pytest.fixture(scope="function")
def tab(chrome: Chrome) -> ChromeTab:
    return chrome.windows.first.tabs.first


@pytest.fixture(scope="function")
def new_tab_no_wait(chrome: Chrome) -> Generator[ChromeTab, None, None]:
    tab = chrome.windows.first.tabs.new(url="https://www.google.com", wait_until_loaded=False)

    try:
        yield tab
    finally:
        with suppress(CommandError):
            tab.close()


def test_tabs_properties_complete(tab: ChromeTab) -> None:
    properties = tab.properties
    properties_keys = set(properties.__dataclass_fields__.keys())

    ae_properties = tab.ae_tab.properties()
    ae_properties_keys = {keyword.AS_name for keyword in ae_properties}

    ae_properties_keys.remove("URL")
    ae_properties_keys.add("url")

    diff = properties_keys.symmetric_difference(ae_properties_keys)

    assert diff == {"class_"}


def test_tab_wait_until_loaded(new_tab_no_wait: ChromeTab) -> None:
    assert new_tab_no_wait.url == "https://www.google.com/"
    assert new_tab_no_wait.loading

    new_tab_no_wait.wait_until_loaded(timeout=10)

    assert new_tab_no_wait.url == "https://www.google.com/"
    assert not new_tab_no_wait.loading


def test_tab_close(new_tab_no_wait: ChromeTab) -> None:
    assert new_tab_no_wait.url == "https://www.google.com/"

    new_tab_no_wait.close()

    with pytest.raises(CommandError):
        _ = new_tab_no_wait.url
