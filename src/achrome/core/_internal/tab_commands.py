from __future__ import annotations

import base64
from textwrap import dedent
from typing import Final

NOT_FOUND_SENTINEL: Final[str] = "__ACHROME_NOT_FOUND__"


def _indent_lines(text: str, *, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else line for line in text.splitlines())


def build_find_window_and_tab_index_script(window_id: int, tab_id: int) -> str:
    return dedent(
        f"""
        set targetWindowId to {window_id}
        set targetTabId to {tab_id}
        set targetWindow to missing value
        set tabIndex to 0

        repeat with w in windows
            if ((id of w) as integer) is targetWindowId then
                set targetWindow to w
                exit repeat
            end if
        end repeat

        if targetWindow is missing value then
            return "{NOT_FOUND_SENTINEL}"
        end if

        set tabCount to count of tabs of targetWindow
        repeat with candidateIndex from 1 to tabCount
            set t to tab candidateIndex of targetWindow
            if ((id of t) as integer) is targetTabId then
                set tabIndex to candidateIndex
                exit repeat
            end if
        end repeat

        if tabIndex is 0 then
            return "{NOT_FOUND_SENTINEL}"
        end if
        """,
    ).strip()


def build_void_tab_command_script(
    window_id: int,
    tab_id: int,
    *,
    command_body: str,
) -> str:
    find_script = _indent_lines(build_find_window_and_tab_index_script(window_id, tab_id))
    command_lines = _indent_lines(dedent(command_body).strip())
    script = dedent(
        """
        use AppleScript version "2.8"
        use scripting additions

        tell application "Google Chrome"
        __ACHROME_FIND_SCRIPT__
            set t to tab tabIndex of targetWindow
        __ACHROME_COMMAND_BODY__
            return "ok"
        end tell
        """,
    ).strip()
    script = script.replace("__ACHROME_FIND_SCRIPT__", find_script)
    return script.replace("__ACHROME_COMMAND_BODY__", command_lines)


def build_execute_script(window_id: int, tab_id: int, javascript: str) -> str:
    javascript_base64 = base64.b64encode(javascript.encode("utf-8")).decode("ascii")
    find_script = _indent_lines(build_find_window_and_tab_index_script(window_id, tab_id))

    script = dedent(
        f"""
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        tell application "Google Chrome"
        __ACHROME_FIND_SCRIPT__
            set t to tab tabIndex of targetWindow
            set jsBase64 to "{javascript_base64}"
            set jsData to current application's NSData's alloc()'s ¬
                initWithBase64EncodedString:jsBase64 options:0
            if jsData is missing value then
                set jsText to ""
            else
                set jsText to (current application's NSString's alloc()'s ¬
                    initWithData:jsData encoding:(current application's NSUTF8StringEncoding)) as text
            end if

            set resultValue to execute t javascript jsText
            try
                return resultValue as text
            on error
                return ""
            end try
        end tell
        """,
    ).strip()
    return script.replace("__ACHROME_FIND_SCRIPT__", find_script)
