from __future__ import annotations

from dataclasses import dataclass

from openmac._internal.applescript.executor import AppleScriptExecutor


@dataclass
class Context:
    executor: AppleScriptExecutor
