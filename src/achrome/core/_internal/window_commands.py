from __future__ import annotations

from textwrap import dedent

from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL


def _indent_lines(text: str, *, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else line for line in text.splitlines())


def build_find_window_script(window_id: int) -> str:
    return dedent(
        f"""
        set targetWindowId to {window_id}
        set targetWindow to missing value

        repeat with w in windows
            if ((id of w) as integer) is targetWindowId then
                set targetWindow to w
                exit repeat
            end if
        end repeat

        if targetWindow is missing value then
            return "{NOT_FOUND_SENTINEL}"
        end if
        """,
    ).strip()


def build_void_window_command_script(window_id: int, *, command_body: str) -> str:
    find_script = _indent_lines(build_find_window_script(window_id))
    command_lines = _indent_lines(dedent(command_body).strip())
    script = dedent(
        """
        use AppleScript version "2.8"
        use scripting additions

        tell application "Google Chrome"
        __ACHROME_FIND_SCRIPT__
        __ACHROME_COMMAND_BODY__
            return "ok"
        end tell
        """,
    ).strip()
    script = script.replace("__ACHROME_FIND_SCRIPT__", find_script)
    return script.replace("__ACHROME_COMMAND_BODY__", command_lines)
