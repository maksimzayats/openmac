from __future__ import annotations

from dataclasses import dataclass

from achrome.core._internal.apple_script import AppleScriptRunner


@dataclass
class Context:
    runner: AppleScriptRunner
