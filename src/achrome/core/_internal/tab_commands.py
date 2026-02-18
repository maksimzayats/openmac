from __future__ import annotations

import base64
from textwrap import dedent
from typing import Final

NOT_FOUND_SENTINEL: Final[str] = "__ACHROME_NOT_FOUND__"
EXECUTE_MISSING_RESULT_SENTINEL: Final[str] = "__ACHROME_EXECUTE_MISSING_RESULT__"


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
            if resultValue is missing value then
                return "{EXECUTE_MISSING_RESULT_SENTINEL}"
            end if
            try
                return resultValue as text
            on error
                return ""
            end try
        end tell
        """,
    ).strip()
    return script.replace("__ACHROME_FIND_SCRIPT__", find_script)


def build_tab_info_script(window_id: int, tab_id: int) -> str:
    """Build an AppleScript that returns fresh tab info as JSON.

    Returns:
        str: JSON object with `title`, `url`, `loading`, `is_active`, or NOT_FOUND_SENTINEL.

    """
    find_script = _indent_lines(build_find_window_and_tab_index_script(window_id, tab_id))
    script = dedent(
        """
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        on boolOrFalse(v)
            if v is missing value then
                return false
            end if
            try
                return (v is true)
            on error
                return false
            end try
        end boolOrFalse

        on nsBool(v)
            return current application's NSNumber's numberWithBool:(my boolOrFalse(v))
        end nsBool

        on textOrEmpty(v)
            if v is missing value then
                return ""
            end if
            try
                return v as text
            on error
                return ""
            end try
        end textOrEmpty

        tell application "Google Chrome"
        __ACHROME_FIND_SCRIPT__
            set activeTabIndex to active tab index of targetWindow
            set t to tab tabIndex of targetWindow

            set tabRec to current application's NSMutableDictionary's dictionary()
            tabRec's setObject:(my textOrEmpty(title of t)) forKey:"title"
            tabRec's setObject:(my textOrEmpty(URL of t)) forKey:"url"
            tabRec's setObject:(my nsBool(loading of t)) forKey:"loading"
            tabRec's setObject:(my nsBool(tabIndex is activeTabIndex)) forKey:"is_active"

            set {jsonData, jsonError} to current application's NSJSONSerialization's ¬
                dataWithJSONObject:tabRec options:0 |error|:(reference)

            if jsonData is missing value then
                return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
            end if

            set jsonString to (current application's NSString's alloc()'s ¬
                initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

            return jsonString
        end tell
        """,
    ).strip()
    return script.replace("__ACHROME_FIND_SCRIPT__", find_script)


def build_tabs_info_list_script(window_id: int) -> str:
    """Build an AppleScript that returns tab info records for a window as JSON."""
    return dedent(
        f"""
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        on integerOrZero(v)
            if v is missing value then
                return 0
            end if
            try
                return v as integer
            on error
                return 0
            end try
        end integerOrZero

        on boolOrFalse(v)
            if v is missing value then
                return false
            end if
            try
                return (v is true)
            on error
                return false
            end try
        end boolOrFalse

        on nsBool(v)
            return current application's NSNumber's numberWithBool:(my boolOrFalse(v))
        end nsBool

        on textOrEmpty(v)
            if v is missing value then
                return ""
            end if
            try
                return v as text
            on error
                return ""
            end try
        end textOrEmpty

        set targetWindowId to {window_id}
        set tabRecs to current application's NSMutableArray's array()

        tell application "Google Chrome"
            set targetWindow to missing value

            repeat with w in windows
                if ((id of w) as integer) is targetWindowId then
                    set targetWindow to w
                    exit repeat
                end if
            end repeat

            if targetWindow is missing value then
                return "[]"
            end if

            set activeTabIndex to active tab index of targetWindow
            set tabCount to (count of tabs of targetWindow)

            repeat with tabIndex from 1 to tabCount
                set t to tab tabIndex of targetWindow

                set rawId to missing value
                set rawTitle to missing value
                set rawUrl to missing value
                set rawLoading to missing value

                set tabRec to current application's NSMutableDictionary's dictionary()

                try
                    set rawId to id of t
                end try
                tabRec's setObject:(my integerOrZero(rawId)) forKey:"id"

                try
                    set rawTitle to title of t
                end try
                tabRec's setObject:(my textOrEmpty(rawTitle)) forKey:"title"

                try
                    set rawUrl to URL of t
                end try
                tabRec's setObject:(my textOrEmpty(rawUrl)) forKey:"url"

                try
                    set rawLoading to loading of t
                end try
                tabRec's setObject:(my nsBool(rawLoading)) forKey:"loading"

                tabRec's setObject:(my nsBool(tabIndex is activeTabIndex)) forKey:"is_active"

                tabRecs's addObject:tabRec
            end repeat
        end tell

        set {{jsonData, jsonError}} to current application's NSJSONSerialization's ¬
            dataWithJSONObject:tabRecs options:0 |error|:(reference)

        if jsonData is missing value then
            return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
        end if

        set jsonString to (current application's NSString's alloc()'s ¬
            initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

        return jsonString
        """,
    ).strip()
