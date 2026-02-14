from dataclasses import dataclass


class ChromeError(RuntimeError):
    """Base error for Chrome API failures."""


class ChromeNotRunningError(ChromeError):
    """Raised when Chrome is not running."""


class NoChromeWindowsError(ChromeError):
    """Raised when Chrome has no windows."""


class WindowNotFoundError(ChromeError):
    """Raised when a window identifier cannot be resolved."""


class TabNotFoundError(ChromeError):
    """Raised when a tab identifier cannot be resolved."""


@dataclass(kw_only=True, frozen=True, slots=True)
class AmbiguousTabIdError(ChromeError):
    """Raised when tab id is ambiguous across windows."""

    tab_id: str
    candidate_window_ids: tuple[str, ...]

    def __str__(self) -> str:
        candidates = ", ".join(self.candidate_window_ids)
        return f"Tab id '{self.tab_id}' is ambiguous across windows: {candidates or 'unknown'}."


class JavaScriptNotAllowedError(ChromeError):
    """Raised when Chrome blocks JavaScript execution from Apple Events."""


@dataclass(kw_only=True, frozen=True, slots=True)
class AppleScriptDecodeError(ChromeError):
    """Raised when AppleScript output cannot be decoded."""

    raw_output: str
    message: str = "Invalid JSON output from AppleScript bridge."

    def __str__(self) -> str:
        return f"{self.message} Raw output: {self.raw_output!r}"
