from __future__ import annotations

from typing import Any

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.sdef import SDEFCommand


class AppleScriptSDEFCommandRunner:
    def __init__(self, executor: AppleScriptExecutor) -> None:
        self._executor = executor

    def run(self, command: SDEFCommand) -> Any:
        script = self._generate_applescript(command)
        result = self._executor.execute(script)

    def _generate_applescript(self, command: SDEFCommand) -> str:
        raise NotImplementedError
