from dataclasses import dataclass

from achrome.core.apple_script.executor import AppleScriptExecutor


@dataclass(kw_only=True, slots=True)
class ChromeAPI:
    """High-level API for controlling Chrome via AppleScript."""

    apple_script_executor: AppleScriptExecutor
