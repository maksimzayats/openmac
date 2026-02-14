import json

import pytest

from achrome.core.chrome import backend as backend_module
from achrome.core.chrome.backend import ChromeAppleScriptBackend, _BridgeEnvelope
from achrome.core.chrome.errors import (
    AmbiguousTabIdError,
    AppleScriptDecodeError,
    ChromeError,
    JavaScriptNotAllowedError,
    NoChromeWindowsError,
    TabNotFoundError,
    WindowNotFoundError,
)
from tests.fakes import FakeAppleScriptExecutor, err_envelope, ok_envelope


def test_backend_success_and_none_payload() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            ("alpha", ("1",)): ok_envelope({"value": 1}),
            ("beta", ()): ok_envelope(None),
        }
    )
    backend = ChromeAppleScriptBackend(
        apple_script_executor=executor,
        bundle_identifier="com.google.Chrome",
    )

    assert backend.run("alpha", "1") == {"value": 1}
    assert backend.run("beta") is None


def test_backend_error_mapping() -> None:
    mapping_cases: list[tuple[str, type[Exception], dict[str, object] | None]] = [
        ("no_windows", NoChromeWindowsError, None),
        ("window_not_found", WindowNotFoundError, None),
        ("tab_not_found", TabNotFoundError, None),
        ("js_not_allowed", JavaScriptNotAllowedError, None),
        (
            "ambiguous_tab",
            AmbiguousTabIdError,
            {"tab_id": "12", "candidate_window_ids": [1001, "1002"]},
        ),
    ]
    for code, exception_type, details in mapping_cases:
        executor = FakeAppleScriptExecutor(
            responses={
                "cmd": err_envelope(code=code, message="failed", details=details),
            }
        )
        backend = ChromeAppleScriptBackend(
            apple_script_executor=executor,
            bundle_identifier="com.google.Chrome",
        )
        with pytest.raises(exception_type):
            backend.run("cmd")


def test_backend_applescript_and_unknown_errors() -> None:
    numbered_executor = FakeAppleScriptExecutor(
        responses={"cmd": err_envelope(code="applescript_error", message="oops", number=42)}
    )
    numbered_backend = ChromeAppleScriptBackend(
        apple_script_executor=numbered_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(ChromeError, match="42"):
        numbered_backend.run("cmd")

    plain_executor = FakeAppleScriptExecutor(
        responses={"cmd": err_envelope(code="applescript_error", message="oops")}
    )
    plain_backend = ChromeAppleScriptBackend(
        apple_script_executor=plain_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(ChromeError, match="oops"):
        plain_backend.run("cmd")

    unknown_executor = FakeAppleScriptExecutor(
        responses={"cmd": err_envelope(code="unexpected", message="unknown")}
    )
    unknown_backend = ChromeAppleScriptBackend(
        apple_script_executor=unknown_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(ChromeError, match="unknown"):
        unknown_backend.run("cmd")


def test_backend_decode_envelope_validation_failures() -> None:
    bad_json_executor = FakeAppleScriptExecutor(responses={"cmd": "not-json"})
    bad_json_backend = ChromeAppleScriptBackend(
        apple_script_executor=bad_json_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(AppleScriptDecodeError):
        bad_json_backend.run("cmd")

    bad_shape_executor = FakeAppleScriptExecutor(responses={"cmd": json.dumps(["bad"])})
    bad_shape_backend = ChromeAppleScriptBackend(
        apple_script_executor=bad_shape_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(AppleScriptDecodeError):
        bad_shape_backend.run("cmd")

    bad_ok_executor = FakeAppleScriptExecutor(
        responses={"cmd": json.dumps({"ok": "yes", "data": {}})}
    )
    bad_ok_backend = ChromeAppleScriptBackend(
        apple_script_executor=bad_ok_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(AppleScriptDecodeError):
        bad_ok_backend.run("cmd")

    bad_error_executor = FakeAppleScriptExecutor(
        responses={"cmd": json.dumps({"ok": False, "error": "bad"})}
    )
    bad_error_backend = ChromeAppleScriptBackend(
        apple_script_executor=bad_error_executor,
        bundle_identifier="com.google.Chrome",
    )
    with pytest.raises(AppleScriptDecodeError):
        bad_error_backend.run("cmd")


def test_backend_handles_missing_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = FakeAppleScriptExecutor(responses={"cmd": ok_envelope({})})
    backend = ChromeAppleScriptBackend(
        apple_script_executor=executor,
        bundle_identifier="com.google.Chrome",
    )

    def fake_decode(self: ChromeAppleScriptBackend, *, raw_output: str) -> _BridgeEnvelope:
        return _BridgeEnvelope(ok=False, data=None, error=None)

    monkeypatch.setattr(ChromeAppleScriptBackend, "_decode_envelope", fake_decode)
    with pytest.raises(ChromeError, match="without payload"):
        backend.run("cmd")


def test_backend_raises_unknown_state_when_mapper_does_not_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = FakeAppleScriptExecutor(responses={"cmd": ok_envelope({})})
    backend = ChromeAppleScriptBackend(
        apple_script_executor=executor,
        bundle_identifier="com.google.Chrome",
    )

    def fake_decode(self: ChromeAppleScriptBackend, *, raw_output: str) -> _BridgeEnvelope:
        return _BridgeEnvelope(ok=False, data=None, error={"code": "unknown", "message": "x"})

    def fake_mapper(self: ChromeAppleScriptBackend, *, error_value: dict[str, object]) -> None:
        return None

    monkeypatch.setattr(ChromeAppleScriptBackend, "_decode_envelope", fake_decode)
    monkeypatch.setattr(ChromeAppleScriptBackend, "_raise_mapped_error", fake_mapper)
    with pytest.raises(ChromeError, match="unknown error state"):
        backend.run("cmd")


def test_backend_internal_helpers() -> None:
    backend = ChromeAppleScriptBackend(
        apple_script_executor=FakeAppleScriptExecutor(responses={}),
        bundle_identifier="com.google.Chrome",
    )

    with pytest.raises(ChromeError):
        backend._coerce_json_value({1: "bad"})
    with pytest.raises(ChromeError):
        backend._coerce_json_value(object())

    assert backend_module._as_str(value="x", fallback="y") == "x"
    assert backend_module._as_str(value=1, fallback="y") == "y"

    assert backend_module._as_int(value=1) == 1
    assert backend_module._as_int(value="2") == 2
    assert backend_module._as_int(value="x") is None
    assert backend_module._as_int(value=True) is None

    assert backend_module._tab_id_from_details(details={"tab_id": "abc"}) == "abc"
    assert backend_module._tab_id_from_details(details={"tab_id": 9}) == "9"
    assert backend_module._tab_id_from_details(details={"tab_id": None}) == "unknown"
    assert backend_module._tab_id_from_details(details="bad") == "unknown"

    assert backend_module._candidate_window_ids(
        details={"candidate_window_ids": [1, "2", None]}
    ) == (
        "1",
        "2",
    )
    assert backend_module._candidate_window_ids(details={"candidate_window_ids": "bad"}) == ()
    assert backend_module._candidate_window_ids(details=None) == ()
