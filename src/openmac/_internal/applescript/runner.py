from __future__ import annotations

from typing import TypeVar, cast, get_args, get_origin

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.script_builder import AppleScriptSDEFScriptBuilder
from openmac._internal.applescript.serializer import loads
from openmac._internal.sdef import SDEFCommand

_ResultT = TypeVar("_ResultT")


class AppleScriptSDEFCommandRunner:
    def __init__(self, executor: AppleScriptExecutor) -> None:
        self._executor = executor

    def run_raw(self, command: SDEFCommand[object]) -> str:
        builder = AppleScriptSDEFScriptBuilder(command)
        script = builder.build_script()
        return self._executor.execute(script)

    def run(self, command: SDEFCommand[_ResultT]) -> _ResultT:
        expected = _infer_command_result_type(command)
        stdout = self.run_raw(cast("SDEFCommand[object]", command))
        if expected is None or expected is type(None):
            return cast("_ResultT", None)
        return cast("_ResultT", loads(stdout, expected=expected))


def _infer_command_result_type(command: SDEFCommand[object]) -> object:
    command_class = command.__class__

    for candidate in command_class.__mro__:
        pydantic_meta: object = getattr(candidate, "__pydantic_generic_metadata__", None)
        if isinstance(pydantic_meta, dict) and pydantic_meta.get("origin") is SDEFCommand:
            args = pydantic_meta.get("args")
            if isinstance(args, tuple) and len(args) == 1:
                return args[0]

    for candidate in command_class.__mro__:
        for base in getattr(candidate, "__orig_bases__", ()):
            if get_origin(base) is SDEFCommand:
                args = get_args(base)
                if len(args) == 1:
                    return args[0]

    msg = (
        f"Command class {command_class.__qualname__!r} must inherit from "
        "SDEFCommand[TResult] so the expected return type can be inferred."
    )
    raise ValueError(msg)
