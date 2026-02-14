import pytest

from achrome.core.chrome.api import ChromeAPI
from achrome.core.chrome.errors import (
    AmbiguousTabIdError,
    NoChromeWindowsError,
    TabNotFoundError,
)
from achrome.core.chrome.models import TabTarget, WindowTarget
from tests.fakes import FakeAppleScriptExecutor, err_envelope, ok_envelope


def test_list_tabs_and_tab_lookup_with_composite_id() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("list_tabs", ("1001",)): ok_envelope(
                [
                    {
                        "id": "2162",
                        "window_id": "1001",
                        "index": 2,
                        "title": "B",
                        "url": "https://b.example",
                        "loading": False,
                        "window_name": "W1",
                        "is_active": False,
                    },
                    {
                        "id": "2161",
                        "window_id": "1001",
                        "index": 1,
                        "title": "A",
                        "url": "https://a.example",
                        "loading": True,
                        "window_name": "W1",
                        "is_active": True,
                    },
                ]
            ),
            ("tab_info", ("1001:2161",)): ok_envelope(
                {
                    "id": "2161",
                    "window_id": "1001",
                    "index": 1,
                    "title": "A",
                    "url": "https://a.example",
                    "loading": True,
                    "window_name": "W1",
                    "is_active": True,
                }
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    tabs = api.list_tabs(window=WindowTarget(window_id="1001"))
    resolved = api.tab("1001:2161")

    assert [tab.id for tab in tabs] == ["2161", "2162"]
    assert tabs[0].composite_id == "1001:2161"
    assert tabs[0].is_active is True
    assert resolved.composite_id == "1001:2161"
    assert TabTarget.parse("1001:2161").to_cli() == "1001:2161"
    assert TabTarget.parse("2161").to_cli() == "2161"


def test_tab_lookup_unique_ambiguous_and_missing() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("tab_info", ("2161",)): err_envelope(
                code="ambiguous_tab",
                message="Ambiguous",
                details={"tab_id": "2161", "candidate_window_ids": ["1001", "1002"]},
            ),
            ("tab_info", ("9999",)): err_envelope(
                code="tab_not_found",
                message="Missing",
            ),
            ("tab_info", ("1001:2161",)): ok_envelope(
                {
                    "id": "2161",
                    "window_id": "1001",
                    "index": 1,
                    "title": "A",
                    "url": "https://a.example",
                    "loading": False,
                    "window_name": "W1",
                    "is_active": True,
                }
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(AmbiguousTabIdError) as ambiguous_error:
        api.tab("2161")
    assert ambiguous_error.value.candidate_window_ids == ("1001", "1002")
    assert "2161" in str(ambiguous_error.value)

    with pytest.raises(TabNotFoundError):
        api.tab("9999")

    resolved = api.tab(TabTarget(tab_id="2161", window_id="1001"))
    assert resolved.window_id == "1001"


def test_active_tab_no_windows_error() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "active_tab": err_envelope(code="no_windows", message="No windows"),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(NoChromeWindowsError):
        api.active_tab()


def test_tab_actions_route_arguments() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("activate_tab", ("1001:2161", "1")): ok_envelope(None),
            ("reload", ()): ok_envelope(None),
            ("go_back", ("1001:2161",)): ok_envelope(None),
            ("go_forward", ("1001:2161",)): ok_envelope(None),
            ("stop", ("1001:2161",)): ok_envelope(None),
            ("source", ("1001:2161",)): ok_envelope("<html></html>"),
            ("close_tab", ()): ok_envelope(None),
            ("close_tab", ("1001:2161",)): ok_envelope(None),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    target = "1001:2161"
    api.activate_tab(target, focus_window=True)
    api.reload()
    api.go_back(tab=target)
    api.go_forward(tab=target)
    api.stop(tab=target)
    source = api.source(tab=target)
    api.close_tab()
    api.close_tab(tab=target)

    assert source == "<html></html>"


def test_open_url_priority_rules() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("open_url", ("https://a.example", "tab", "1001:2161", "1")): ok_envelope(
                {
                    "id": "2161",
                    "window_id": "1001",
                    "index": 1,
                    "title": "A",
                    "url": "https://a.example",
                    "loading": False,
                    "window_name": "W1",
                    "is_active": True,
                }
            ),
            ("open_url", ("https://b.example", "new_window", "incognito", "1")): ok_envelope(
                {
                    "id": "3001",
                    "window_id": "2001",
                    "index": 1,
                    "title": "B",
                    "url": "https://b.example",
                    "loading": False,
                    "window_name": "W2",
                    "is_active": True,
                }
            ),
            ("open_url", ("https://c.example", "window", "1002", "0")): ok_envelope(
                {
                    "id": "3002",
                    "window_id": "1002",
                    "index": 4,
                    "title": "C",
                    "url": "https://c.example",
                    "loading": False,
                    "window_name": "W3",
                    "is_active": False,
                }
            ),
            ("open_url", ("https://d.example", "front", "", "1")): ok_envelope(
                {
                    "id": "3003",
                    "window_id": "1004",
                    "index": 2,
                    "title": "D",
                    "url": "https://d.example",
                    "loading": False,
                    "window_name": "W4",
                    "is_active": True,
                }
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    tab_target = TabTarget(tab_id="2161", window_id="1001")
    tab_a = api.open_url("https://a.example", tab=tab_target, new_window=True, incognito=True)
    tab_b = api.open_url("https://b.example", new_window=True, incognito=True)
    tab_c = api.open_url("https://c.example", window=WindowTarget(window_id="1002"), activate=False)
    tab_d = api.open_url("https://d.example")

    assert tab_a.composite_id == "1001:2161"
    assert tab_b.window_id == "2001"
    assert tab_c.is_active is False
    assert tab_d.url == "https://d.example"


def test_tab_target_rejects_empty_values() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        TabTarget.parse("")

    with pytest.raises(ValueError, match="Invalid tab target format"):
        TabTarget.parse("1001:")
