import pytest

from achrome.core.chrome.api import ChromeAPI
from achrome.core.chrome.errors import AppleScriptDecodeError, JavaScriptNotAllowedError
from tests.fakes import FakeAppleScriptExecutor, err_envelope, ok_envelope


def test_execute_javascript_returns_raw_string() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("execute_js", ("1 + 1",)): ok_envelope("2"),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    result = api.execute_javascript("1 + 1")

    assert result == "2"


def test_execute_javascript_json_wraps_and_parses_result() -> None:
    captured_args: list[tuple[str, ...]] = []

    def execute_js_response(command_args: tuple[str, ...]) -> str:
        captured_args.append(command_args)
        return ok_envelope('{"value":42,"items":[1,true,null]}')

    executor = FakeAppleScriptExecutor(responses={"execute_js": execute_js_response})
    api = ChromeAPI(apple_script_executor=executor)

    value = api.execute_javascript_json("1 + 1")

    assert value == {"value": 42, "items": [1, True, None]}
    assert captured_args
    assert "JSON.stringify((function(){ return (1 + 1); })())" in captured_args[0][0]


def test_execute_javascript_json_raises_decode_error_for_invalid_json() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            (
                "execute_js",
                ("JSON.stringify((function(){ return (window.location.href); })())",),
            ): ok_envelope("not-json"),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(AppleScriptDecodeError, match="Invalid JSON output"):
        api.execute_javascript_json("window.location.href")


def test_execute_javascript_error_mapping_for_js_permissions() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("execute_js", ("1",)): err_envelope(
                code="js_not_allowed",
                message="Enable JavaScript from Apple Events",
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    with pytest.raises(JavaScriptNotAllowedError):
        api.execute_javascript("1")
