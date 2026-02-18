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


def build_window_info_script(window_id: int) -> str:
    """Build an AppleScript that returns fresh window info as JSON.

    Returns:
        str: JSON object (window fields excluding id), or NOT_FOUND_SENTINEL.

    """
    find_script = _indent_lines(build_find_window_script(window_id))
    script = dedent(
        """
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

        on boundsOrZero(rawBounds)
            if rawBounds is missing value then
                return {0, 0, 0, 0}
            end if
            try
                if (count of rawBounds) is not 4 then
                    return {0, 0, 0, 0}
                end if
                return {¬
                    my integerOrZero(item 1 of rawBounds), ¬
                    my integerOrZero(item 2 of rawBounds), ¬
                    my integerOrZero(item 3 of rawBounds), ¬
                    my integerOrZero(item 4 of rawBounds)}
            on error
                return {0, 0, 0, 0}
            end try
        end boundsOrZero

        tell application "Google Chrome"
        __ACHROME_FIND_SCRIPT__
            set windowRec to current application's NSMutableDictionary's dictionary()

            set rawBounds to missing value
            set rawName to missing value
            set rawMode to missing value
            set rawIndex to missing value
            set rawCloseable to missing value
            set rawMinimizable to missing value
            set rawMinimized to missing value
            set rawResizable to missing value
            set rawVisible to missing value
            set rawZoomable to missing value
            set rawZoomed to missing value
            set rawActiveTabIndex to missing value
            set rawPresenting to missing value
            set rawActiveTabId to missing value

            try
                set rawName to name of targetWindow
            end try
            windowRec's setObject:(my textOrEmpty(rawName)) forKey:"name"

            try
                set rawBounds to bounds of targetWindow
            end try
            windowRec's setObject:(my boundsOrZero(rawBounds)) forKey:"bounds"

            try
                set rawIndex to index of targetWindow
            end try
            windowRec's setObject:(my integerOrZero(rawIndex)) forKey:"index"

            try
                set rawCloseable to closeable of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawCloseable)) forKey:"closeable"

            try
                set rawMinimizable to minimizable of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawMinimizable)) forKey:"minimizable"

            try
                set rawMinimized to minimized of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawMinimized)) forKey:"minimized"

            try
                set rawResizable to resizable of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawResizable)) forKey:"resizable"

            try
                set rawVisible to visible of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawVisible)) forKey:"visible"

            try
                set rawZoomable to zoomable of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawZoomable)) forKey:"zoomable"

            try
                set rawZoomed to zoomed of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawZoomed)) forKey:"zoomed"

            try
                set rawMode to mode of targetWindow
            end try
            windowRec's setObject:(my textOrEmpty(rawMode)) forKey:"mode"

            try
                set rawActiveTabIndex to active tab index of targetWindow
            end try
            windowRec's setObject:(my integerOrZero(rawActiveTabIndex)) forKey:"active_tab_index"

            try
                set rawPresenting to presenting of targetWindow
            end try
            windowRec's setObject:(my nsBool(rawPresenting)) forKey:"presenting"

            try
                set rawActiveTabId to id of active tab of targetWindow
            end try
            windowRec's setObject:(my integerOrZero(rawActiveTabId)) forKey:"active_tab_id"

            set {jsonData, jsonError} to current application's NSJSONSerialization's ¬
                dataWithJSONObject:windowRec options:0 |error|:(reference)

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


def build_windows_info_list_script() -> str:
    """Build an AppleScript that returns all window info records as JSON."""
    return dedent(
        """
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

        on boundsOrZero(rawBounds)
            if rawBounds is missing value then
                return {0, 0, 0, 0}
            end if
            try
                if (count of rawBounds) is not 4 then
                    return {0, 0, 0, 0}
                end if
                return {¬
                    my integerOrZero(item 1 of rawBounds), ¬
                    my integerOrZero(item 2 of rawBounds), ¬
                    my integerOrZero(item 3 of rawBounds), ¬
                    my integerOrZero(item 4 of rawBounds)}
            on error
                return {0, 0, 0, 0}
            end try
        end boundsOrZero

        set windowRecs to current application's NSMutableArray's array()

        tell application "Google Chrome"
            repeat with w in windows
                set rawId to missing value
                set rawBounds to missing value
                set rawName to missing value
                set rawMode to missing value
                set rawIndex to missing value
                set rawCloseable to missing value
                set rawMinimizable to missing value
                set rawMinimized to missing value
                set rawResizable to missing value
                set rawVisible to missing value
                set rawZoomable to missing value
                set rawZoomed to missing value
                set rawActiveTabIndex to missing value
                set rawPresenting to missing value
                set rawActiveTabId to missing value

                set windowRec to current application's NSMutableDictionary's dictionary()

                try
                    set rawId to id of w
                end try
                windowRec's setObject:(my integerOrZero(rawId)) forKey:"id"

                try
                    set rawName to name of w
                end try
                windowRec's setObject:(my textOrEmpty(rawName)) forKey:"name"

                try
                    set rawBounds to bounds of w
                end try
                windowRec's setObject:(my boundsOrZero(rawBounds)) forKey:"bounds"

                try
                    set rawIndex to index of w
                end try
                windowRec's setObject:(my integerOrZero(rawIndex)) forKey:"index"

                try
                    set rawCloseable to closeable of w
                end try
                windowRec's setObject:(my nsBool(rawCloseable)) forKey:"closeable"

                try
                    set rawMinimizable to minimizable of w
                end try
                windowRec's setObject:(my nsBool(rawMinimizable)) forKey:"minimizable"

                try
                    set rawMinimized to minimized of w
                end try
                windowRec's setObject:(my nsBool(rawMinimized)) forKey:"minimized"

                try
                    set rawResizable to resizable of w
                end try
                windowRec's setObject:(my nsBool(rawResizable)) forKey:"resizable"

                try
                    set rawVisible to visible of w
                end try
                windowRec's setObject:(my nsBool(rawVisible)) forKey:"visible"

                try
                    set rawZoomable to zoomable of w
                end try
                windowRec's setObject:(my nsBool(rawZoomable)) forKey:"zoomable"

                try
                    set rawZoomed to zoomed of w
                end try
                windowRec's setObject:(my nsBool(rawZoomed)) forKey:"zoomed"

                try
                    set rawMode to mode of w
                end try
                windowRec's setObject:(my textOrEmpty(rawMode)) forKey:"mode"

                try
                    set rawActiveTabIndex to active tab index of w
                end try
                windowRec's setObject:(my integerOrZero(rawActiveTabIndex)) forKey:"active_tab_index"

                try
                    set rawPresenting to presenting of w
                end try
                windowRec's setObject:(my nsBool(rawPresenting)) forKey:"presenting"

                try
                    set rawActiveTabId to id of active tab of w
                end try
                windowRec's setObject:(my integerOrZero(rawActiveTabId)) forKey:"active_tab_id"

                windowRecs's addObject:windowRec
            end repeat
        end tell

        set {jsonData, jsonError} to current application's NSJSONSerialization's ¬
            dataWithJSONObject:windowRecs options:0 |error|:(reference)

        if jsonData is missing value then
            return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
        end if

        set jsonString to (current application's NSString's alloc()'s ¬
            initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

        return jsonString
        """,
    ).strip()
