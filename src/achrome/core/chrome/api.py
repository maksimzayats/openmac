from dataclasses import dataclass

from achrome.core.applescript.executor import AppleScriptExecutor
from achrome.core.chrome.models import Tab


@dataclass(kw_only=True, slots=True)
class ChromeAPI:
    apple_script_executor: AppleScriptExecutor

    def list_tabs(self) -> list[Tab]:
        pass
