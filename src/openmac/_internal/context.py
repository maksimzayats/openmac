from __future__ import annotations

from dataclasses import dataclass

from openmac._internal.applescript.runner import AppleScriptRunner


@dataclass
class Context:
    runner: AppleScriptRunner
