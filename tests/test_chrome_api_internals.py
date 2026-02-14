import pytest

from achrome.core.chrome import api as api_module
from achrome.core.chrome.api import ChromeAPI
from achrome.core.chrome.errors import ChromeError
from achrome.core.chrome.models import WindowBounds
from tests.fakes import FakeAppleScriptExecutor, ok_envelope


def test_api_methods_cover_default_paths_and_window_ordering() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("active_tab", ()): ok_envelope(
                {
                    "id": "2",
                    "window_id": "1001",
                    "index": 1,
                    "title": "Active",
                    "url": "https://active",
                    "loading": False,
                    "window_name": "W1",
                    "is_active": True,
                }
            ),
            ("list_tabs", ()): ok_envelope(
                [
                    {
                        "id": "t2",
                        "window_id": "1002",
                        "index": 1,
                        "title": "Second window tab",
                        "url": "https://two",
                        "loading": False,
                        "window_name": "W2",
                        "is_active": True,
                    },
                    {
                        "id": "t1",
                        "window_id": "1001",
                        "index": 2,
                        "title": "First window tab",
                        "url": "https://one",
                        "loading": False,
                        "window_name": "W1",
                        "is_active": False,
                    },
                ]
            ),
            ("list_windows", ()): ok_envelope(
                [
                    {
                        "id": "1002",
                        "index": 2,
                        "name": "W2",
                        "given_name": "",
                        "bounds": {"left": 0, "top": 0, "right": 100, "bottom": 100},
                        "closeable": True,
                        "minimizable": True,
                        "minimized": False,
                        "resizable": True,
                        "visible": True,
                        "zoomable": True,
                        "zoomed": False,
                        "mode": "normal",
                        "active_tab_index": 1,
                        "active_tab_id": "t2",
                        "tab_count": 1,
                    },
                    {
                        "id": "1001",
                        "index": 1,
                        "name": "W1",
                        "given_name": "",
                        "bounds": {"left": 0, "top": 0, "right": 100, "bottom": 100},
                        "closeable": True,
                        "minimizable": True,
                        "minimized": False,
                        "resizable": True,
                        "visible": True,
                        "zoomable": True,
                        "zoomed": False,
                        "mode": "normal",
                        "active_tab_index": 2,
                        "active_tab_id": "t1",
                        "tab_count": 2,
                    },
                ]
            ),
            ("source", ()): ok_envelope("<html>default</html>"),
            ("execute_js", ("1 + 2", "1001:t1")): ok_envelope("3"),
            ("get_window_bounds", ()): ok_envelope(
                {"left": 0, "top": 0, "right": 300, "bottom": 200}
            ),
            ("set_window_bounds", ("", "1", "2", "3", "4")): ok_envelope(None),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    assert api.active_tab().id == "2"
    assert [tab.window_id for tab in api.list_tabs()] == ["1001", "1002"]
    assert api.source() == "<html>default</html>"
    assert api.execute_javascript("1 + 2", tab="1001:t1") == "3"
    assert api.window_bounds() == WindowBounds(left=0, top=0, right=300, bottom=200)
    api.set_window_bounds(WindowBounds(left=1, top=2, right=3, bottom=4))


def test_api_internal_parsers_raise_for_invalid_shapes() -> None:
    api = ChromeAPI(apple_script_executor=FakeAppleScriptExecutor(responses={}))

    with pytest.raises(ChromeError):
        api._coerce_json_value({1: "bad"})
    with pytest.raises(ChromeError):
        api._coerce_json_value(object())

    with pytest.raises(ChromeError):
        api_module._as_dict(value=[], context="x")
    with pytest.raises(ChromeError):
        api_module._as_list(value={}, context="x")
    with pytest.raises(ChromeError):
        api_module._as_str(value=None, field_name="x")

    assert api_module._as_id(value=1, field_name="id") == "1"
    with pytest.raises(ChromeError):
        api_module._as_id(value=True, field_name="id")
    with pytest.raises(ChromeError):
        api_module._as_id(value=None, field_name="id")

    assert api_module._as_int(value="10", field_name="int") == 10
    with pytest.raises(ChromeError):
        api_module._as_int(value=True, field_name="int")
    with pytest.raises(ChromeError):
        api_module._as_int(value="bad", field_name="int")
    with pytest.raises(ChromeError):
        api_module._as_int(value=None, field_name="int")

    assert api_module._as_bool(value=True, field_name="bool") is True
    assert api_module._as_bool(value="1", field_name="bool") is True
    assert api_module._as_bool(value="0", field_name="bool") is False
    assert api_module._as_bool(value=1, field_name="bool") is True
    assert api_module._as_bool(value=0, field_name="bool") is False
    with pytest.raises(ChromeError):
        api_module._as_bool(value=2, field_name="bool")
    with pytest.raises(ChromeError):
        api_module._as_bool(value="maybe", field_name="bool")

    assert api_module._bool_arg(value=True) == "1"
    assert api_module._bool_arg(value=False) == "0"
