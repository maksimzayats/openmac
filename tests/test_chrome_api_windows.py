import json

import pytest

from achrome.core.chrome.api import ChromeAPI
from achrome.core.chrome.errors import ChromeError, NoChromeWindowsError, WindowNotFoundError
from achrome.core.chrome.models import WindowBounds, WindowTarget
from tests.fakes import FakeAppleScriptExecutor, err_envelope, ok_envelope


def test_application_info_and_window_listing_are_typed_and_sorted() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "app_info": ok_envelope(
                {"name": "Google Chrome", "version": "123.0", "frontmost": True}
            ),
            "list_windows": ok_envelope(
                [
                    {
                        "id": 1002,
                        "index": 2,
                        "name": "Second",
                        "given_name": "",
                        "bounds": {"left": 10, "top": 20, "right": 210, "bottom": 220},
                        "closeable": True,
                        "minimizable": True,
                        "minimized": False,
                        "resizable": True,
                        "visible": True,
                        "zoomable": True,
                        "zoomed": False,
                        "mode": "normal",
                        "active_tab_index": 1,
                        "active_tab_id": 11,
                        "tab_count": 1,
                    },
                    {
                        "id": "1001",
                        "index": 1,
                        "name": "First",
                        "given_name": "Given",
                        "bounds": {"left": 0, "top": 0, "right": 100, "bottom": 80},
                        "closeable": True,
                        "minimizable": True,
                        "minimized": False,
                        "resizable": True,
                        "visible": True,
                        "zoomable": True,
                        "zoomed": False,
                        "mode": "incognito",
                        "active_tab_index": "2",
                        "active_tab_id": "22",
                        "tab_count": 2,
                    },
                ]
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    app_info = api.application_info()
    windows = api.list_windows()

    assert app_info.name == "Google Chrome"
    assert app_info.version == "123.0"
    assert app_info.frontmost is True
    assert [window.id for window in windows] == ["1001", "1002"]
    assert windows[0].mode == "incognito"
    assert windows[0].bounds.width == 100
    assert windows[0].bounds.height == 80


def test_window_bounds_get_and_set_routes_arguments() -> None:
    target = WindowTarget(window_id="1001")
    executor = FakeAppleScriptExecutor(
        responses={
            ("get_window_bounds", ("1001",)): ok_envelope(
                {"left": 1, "top": 2, "right": 101, "bottom": 202}
            ),
            ("set_window_bounds", ("1001", "1", "2", "101", "202")): ok_envelope(None),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    bounds = api.window_bounds(window=target)
    api.set_window_bounds(bounds, window=target)

    assert bounds == WindowBounds(left=1, top=2, right=101, bottom=202)


def test_close_window_defaults_to_front_window() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("close_window", ()): ok_envelope(None),
            ("close_window", ("1002",)): ok_envelope(None),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    api.close_window()
    api.close_window(window=WindowTarget(window_id="1002"))

    calls = [(args[1], tuple(args[2:])) for _, args in executor.calls]
    assert calls == [("close_window", ()), ("close_window", ("1002",))]


@pytest.mark.parametrize(
    ("code", "expected_exception"),
    [
        ("window_not_found", WindowNotFoundError),
        ("no_windows", NoChromeWindowsError),
        ("applescript_error", ChromeError),
    ],
)
def test_window_related_errors_are_mapped(
    code: str,
    expected_exception: type[Exception],
) -> None:
    envelope = err_envelope(code=code, message="failed", number=17)
    executor = FakeAppleScriptExecutor(
        responses={
            "list_windows": envelope,
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(expected_exception):
        api.list_windows()


def test_invalid_envelope_raises_decode_error() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "application_info": json.dumps({"ok": True, "oops": "bad"}),
            "app_info": "not-json",
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(ChromeError):
        api.application_info()
