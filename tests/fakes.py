from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

ResponseFactory: TypeAlias = Callable[[tuple[str, ...]], str]  # noqa: UP040
ResponseValue: TypeAlias = str | ResponseFactory  # noqa: UP040


@dataclass(kw_only=True, slots=True)
class FakeAppleScriptExecutor:
    responses: dict[tuple[str, tuple[str, ...]] | str, ResponseValue]
    calls: list[tuple[str, list[str]]] = field(default_factory=list)

    def run_applescript(self, script: str, args: list[str] | None = None) -> str:
        if args is None:
            msg = "Bridge args are required for FakeAppleScriptExecutor."
            raise AssertionError(msg)

        self.calls.append((script, args))
        if len(args) < 2:
            msg = "Expected [bundle_id, command, ...] args."
            raise AssertionError(msg)

        command = args[1]
        command_args = tuple(args[2:])
        exact_key = (command, command_args)
        if exact_key in self.responses:
            value = self.responses[exact_key]
        elif command in self.responses:
            value = self.responses[command]
        else:
            msg = f"Unhandled fake command: {command} {command_args!r}"
            raise AssertionError(msg)

        if callable(value):
            return value(command_args)
        return value


def ok_envelope(data: object) -> str:
    return json.dumps({"ok": True, "data": data})


def err_envelope(
    *,
    code: str,
    message: str,
    number: int | None = None,
    details: object = None,
) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "number": number,
                "details": details,
            },
        }
    )
