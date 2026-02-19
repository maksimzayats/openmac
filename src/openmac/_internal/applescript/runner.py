from __future__ import annotations

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.script_builder import AppleScriptSDEFScriptBuilder
from openmac._internal.sdef import SDEFCommand


class AppleScriptSDEFCommandRunner:
    def __init__(self, executor: AppleScriptExecutor) -> None:
        self._executor = executor

    def run(self, command: SDEFCommand) -> str:
        builder = AppleScriptSDEFScriptBuilder(command)
        script = builder.build_script()

        return self._executor.execute(script)
