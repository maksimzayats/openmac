from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from achrome.core.apple_script.executor import AppleScriptExecutorLike
from achrome.core.chrome.applescript_bridge import CHROME_BRIDGE_SCRIPT
from achrome.core.chrome.errors import (
    AmbiguousTabIdError,
    AppleScriptDecodeError,
    ChromeError,
    JavaScriptNotAllowedError,
    NoChromeWindowsError,
    TabNotFoundError,
    WindowNotFoundError,
)
from achrome.core.chrome.models import JsonValue


@dataclass(kw_only=True, slots=True)
class ChromeAppleScriptBackend:
    """Runs bridge commands and maps JSON envelopes to typed errors."""

    apple_script_executor: AppleScriptExecutorLike
    bundle_identifier: str

    def run(self, command: str, *args: str) -> JsonValue:
        """Run a bridge command and return decoded `data` payload."""
        raw_output = self.apple_script_executor.run_applescript(
            CHROME_BRIDGE_SCRIPT,
            [self.bundle_identifier, command, *args],
        )
        envelope = self._decode_envelope(raw_output=raw_output)
        if envelope.ok:
            if envelope.data is None:
                return None
            return envelope.data
        if envelope.error is None:
            msg = "Bridge returned an error without payload."
            raise ChromeError(msg)
        self._raise_mapped_error(error_value=envelope.error)
        msg = "Bridge returned an unknown error state."
        raise ChromeError(msg)

    def _decode_envelope(self, *, raw_output: str) -> _BridgeEnvelope:
        try:
            decoded = cast("object", json.loads(raw_output))
        except json.JSONDecodeError as exc:
            raise AppleScriptDecodeError(raw_output=raw_output) from exc
        if not isinstance(decoded, dict):
            raise AppleScriptDecodeError(raw_output=raw_output)

        ok_value = decoded.get("ok")
        if not isinstance(ok_value, bool):
            raise AppleScriptDecodeError(raw_output=raw_output)

        if ok_value:
            return _BridgeEnvelope(
                ok=True, data=self._coerce_json_value(decoded.get("data")), error=None
            )

        error_value = decoded.get("error")
        if not isinstance(error_value, dict):
            raise AppleScriptDecodeError(raw_output=raw_output)
        return _BridgeEnvelope(ok=False, data=None, error=error_value)

    def _raise_mapped_error(self, *, error_value: dict[str, object]) -> None:
        code = _as_str(value=error_value.get("code"), fallback="applescript_error")
        message = _as_str(value=error_value.get("message"), fallback="AppleScript bridge failed.")
        details = error_value.get("details")

        if code == "no_windows":
            raise NoChromeWindowsError(message)
        if code == "window_not_found":
            raise WindowNotFoundError(message)
        if code == "tab_not_found":
            raise TabNotFoundError(message)
        if code == "js_not_allowed":
            raise JavaScriptNotAllowedError(message)
        if code == "ambiguous_tab":
            candidate_window_ids = _candidate_window_ids(details=details)
            tab_id = _tab_id_from_details(details=details)
            raise AmbiguousTabIdError(tab_id=tab_id, candidate_window_ids=candidate_window_ids)
        if code == "applescript_error":
            number = _as_int(value=error_value.get("number"))
            if number is not None:
                error_message = f"{message} (AppleScript error {number})"
                raise ChromeError(error_message)
            raise ChromeError(message)
        raise ChromeError(message)

    def _coerce_json_value(self, value: object) -> JsonValue:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [self._coerce_json_value(item) for item in value]
        if isinstance(value, dict):
            mapped: dict[str, JsonValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    msg = f"Expected string key in JSON object, got {type(key)!r}."
                    raise ChromeError(msg)
                mapped[key] = self._coerce_json_value(item)
            return mapped
        msg = f"Unsupported JSON value type: {type(value)!r}."
        raise ChromeError(msg)


@dataclass(kw_only=True, frozen=True, slots=True)
class _BridgeEnvelope:
    ok: bool
    data: JsonValue | None
    error: dict[str, object] | None


def _as_str(*, value: object, fallback: str) -> str:
    if isinstance(value, str):
        return value
    return fallback


def _as_int(*, value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _tab_id_from_details(*, details: object) -> str:
    if not isinstance(details, dict):
        return "unknown"
    value = details.get("tab_id")
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return "unknown"


def _candidate_window_ids(*, details: object) -> tuple[str, ...]:
    if not isinstance(details, dict):
        return ()
    raw_candidates = details.get("candidate_window_ids")
    if not isinstance(raw_candidates, list):
        return ()
    candidates: list[str] = []
    for candidate in raw_candidates:
        if isinstance(candidate, str):
            candidates.append(candidate)
        elif isinstance(candidate, int):
            candidates.append(str(candidate))
    return tuple(candidates)
