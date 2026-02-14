import json

import pytest

from achrome import (
    ChromeSnapshot as PublicChromeSnapshot,
    ChromeSnapshotRef as PublicChromeSnapshotRef,
)
from achrome.core.chrome.api import ChromeAPI
from achrome.core.chrome.errors import ChromeError
from achrome.core.chrome.models import ChromeSnapshot, ChromeSnapshotRef, TabTarget
from tests.fakes import FakeAppleScriptExecutor, ok_envelope


def _snapshot_response(payload: object) -> str:
    return ok_envelope(json.dumps(payload))


def test_snapshot_returns_typed_models() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response(
                {
                    "tree": '- heading "Example Domain" [ref=e1]',
                    "refs": {
                        "e1": {
                            "selector": 'getByRole("heading", { name: "Example Domain" })',
                            "role": "heading",
                            "name": "Example Domain",
                        }
                    },
                }
            )
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    snapshot = api.snapshot()

    assert snapshot == ChromeSnapshot(
        tree='- heading "Example Domain" [ref=e1]',
        refs={
            "e1": ChromeSnapshotRef(
                selector='getByRole("heading", { name: "Example Domain" })',
                role="heading",
                name="Example Domain",
            )
        },
    )


def test_snapshot_forwards_all_options_into_javascript() -> None:
    captured_args: list[tuple[str, ...]] = []

    def execute_js_response(command_args: tuple[str, ...]) -> str:
        captured_args.append(command_args)
        return _snapshot_response({"tree": "- button [ref=e1]", "refs": {"e1": _ref("button")}})

    executor = FakeAppleScriptExecutor(responses={"execute_js": execute_js_response})
    api = ChromeAPI(apple_script_executor=executor)

    snapshot = api.snapshot(
        interactive=True,
        cursor=True,
        max_depth=5,
        compact=True,
        selector="  #main  ",
    )

    assert snapshot.tree == "- button [ref=e1]"
    assert captured_args
    javascript = captured_args[0][0]
    assert '"interactive":true' in javascript
    assert '"cursor":true' in javascript
    assert '"maxDepth":5' in javascript
    assert '"compact":true' in javascript
    assert '"selector":"#main"' in javascript


def test_snapshot_routes_optional_tab_target() -> None:
    captured_args: list[tuple[str, ...]] = []

    def execute_js_response(command_args: tuple[str, ...]) -> str:
        captured_args.append(command_args)
        return _snapshot_response({"tree": "- button [ref=e1]", "refs": {"e1": _ref("button")}})

    executor = FakeAppleScriptExecutor(responses={"execute_js": execute_js_response})
    api = ChromeAPI(apple_script_executor=executor)

    api.snapshot(tab=TabTarget(window_id="1001", tab_id="2161"))

    assert len(captured_args) == 1
    assert captured_args[0][1] == "1001:2161"


def test_snapshot_rejects_negative_max_depth() -> None:
    api = ChromeAPI(apple_script_executor=FakeAppleScriptExecutor(responses={}))

    with pytest.raises(ValueError, match="max_depth"):
        api.snapshot(max_depth=-1)


def test_snapshot_rejects_blank_selector() -> None:
    api = ChromeAPI(apple_script_executor=FakeAppleScriptExecutor(responses={}))

    with pytest.raises(ValueError, match="selector"):
        api.snapshot(selector="  ")


def test_snapshot_decode_failure_is_chrome_error() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": ok_envelope("not-json"),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(ChromeError, match="snapshot JavaScript"):
        api.snapshot()


def test_snapshot_rejects_non_object_payload() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response([]),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(ChromeError, match="Expected object for snapshot"):
        api.snapshot()


def test_snapshot_cursor_contract_and_duplicate_nth_contract() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response(
                {
                    "tree": (
                        '- button "Save" [ref=e1]\n'
                        '- button "Save" [ref=e2] [nth=1]\n'
                        "# Cursor-interactive elements:\n"
                        '- clickable "Open menu" [ref=e3] [cursor:pointer, onclick]'
                    ),
                    "refs": {
                        "e1": _ref("button", name="Save", nth=0),
                        "e2": _ref("button", name="Save", nth=1),
                        "e3": _ref(
                            "clickable",
                            name="Open menu",
                            selector="#menu > div:nth-of-type(1)",
                        ),
                        "e4": _ref("button", name="Cancel"),
                    },
                }
            )
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    snapshot = api.snapshot(cursor=True, interactive=True)

    assert "# Cursor-interactive elements:" in snapshot.tree
    assert snapshot.refs["e1"].nth == 0
    assert snapshot.refs["e2"].nth == 1
    assert snapshot.refs["e3"].nth is None
    assert snapshot.refs["e4"].nth is None


def test_snapshot_rejects_missing_and_unexpected_fields() -> None:
    missing_executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response({"tree": "x"}),
        }
    )
    api_missing = ChromeAPI(apple_script_executor=missing_executor)
    with pytest.raises(ChromeError, match="Missing required field"):
        api_missing.snapshot()

    extra_executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response(
                {"tree": "x", "refs": {"e1": _ref("button")}, "extra": True}
            ),
        }
    )
    api_extra = ChromeAPI(apple_script_executor=extra_executor)
    with pytest.raises(ChromeError, match="Unexpected field"):
        api_extra.snapshot()


def test_snapshot_rejects_invalid_ref_shape() -> None:
    invalid_key_executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response({"tree": "x", "refs": {"x1": _ref("button")}}),
        }
    )
    api_invalid_key = ChromeAPI(apple_script_executor=invalid_key_executor)
    with pytest.raises(ChromeError, match="ref id"):
        api_invalid_key.snapshot()

    invalid_ref_executor = FakeAppleScriptExecutor(
        responses={
            "execute_js": _snapshot_response(
                {
                    "tree": "x",
                    "refs": {
                        "e1": {"selector": "getByRole('button')", "role": "button", "nth": -1}
                    },
                }
            ),
        }
    )
    api_invalid_ref = ChromeAPI(apple_script_executor=invalid_ref_executor)
    with pytest.raises(ChromeError, match="non-negative"):
        api_invalid_ref.snapshot()


def test_snapshot_public_exports() -> None:
    assert PublicChromeSnapshot is ChromeSnapshot
    assert PublicChromeSnapshotRef is ChromeSnapshotRef


def _ref(
    role: str, *, name: str | None = None, selector: str | None = None, nth: int | None = None
) -> dict[str, object]:
    data: dict[str, object] = {
        "selector": selector or f"getByRole('{role}')",
        "role": role,
    }
    if name is not None:
        data["name"] = name
    if nth is not None:
        data["nth"] = nth
    return data
