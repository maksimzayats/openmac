from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class Tab:
    window_index: int
    tab_index: int
    title: str
    url: str


class ChromeAppleEvents:
    """
    Minimal Chrome controller using Apple Events via AppleScript.
    Mirrors the core vibe of chrome-cli:
      - list tabs
      - activate tab
      - open URL
      - eval JS in active tab
      - get HTML source (outerHTML)
    """

    _RS = chr(30)  # record separator
    _US = chr(31)  # unit separator

    def list_tabs(self) -> List[Tab]:
        script = r'''
on run argv
  set RS to ASCII character 30
  set US to ASCII character 31
  set out to ""

  tell application "Google Chrome"
    set wCount to count of windows
    repeat with wi from 1 to wCount
      set tCount to count of tabs of window wi
      repeat with ti from 1 to tCount
        set t to tab ti of window wi
        set rec to (wi as text) & US & (ti as text) & US & (title of t as text) & US & (URL of t as text)
        if out is "" then
          set out to rec
        else
          set out to out & RS & rec
        end if
      end repeat
    end repeat
  end tell

  return out
end run
'''
        raw = run_applescript(script)
        if not raw:
            return []

        tabs: List[Tab] = []
        for rec in raw.split(self._RS):
            parts = rec.split(self._US)
            if len(parts) != 4:
                continue
            wi_s, ti_s, title, url = parts
            try:
                wi = int(wi_s)
                ti = int(ti_s)
            except ValueError:
                continue
            tabs.append(Tab(window_index=wi, tab_index=ti, title=title, url=url))
        return tabs

    def active_tab(self) -> Tab:
        script = r'''
on run argv
  set US to ASCII character 31
  tell application "Google Chrome"
    if (count of windows) = 0 then
      make new window
    end if
    set t to active tab of front window
    set wi to 1
    set ti to active tab index of front window
    return (wi as text) & US & (ti as text) & US & (title of t as text) & US & (URL of t as text)
  end tell
end run
'''
        raw = run_applescript(script)
        parts = raw.split(self._US)
        if len(parts) != 4:
            raise AppleScriptError(f"Unexpected active_tab output: {raw!r}")
        wi = int(parts[0])
        ti = int(parts[1])
        return Tab(window_index=wi, tab_index=ti, title=parts[2], url=parts[3])

    def activate_tab(self, window_index: int, tab_index: int) -> None:
        script = r'''
on run argv
  set wi to (item 1 of argv) as integer
  set ti to (item 2 of argv) as integer

  tell application "Google Chrome"
    if (count of windows) = 0 then
      make new window
    end if

    set theWindow to window wi
    activate
    set index of theWindow to 1
    set active tab index of theWindow to ti
  end tell
end run
'''
        run_applescript(script, [str(window_index), str(tab_index)])

    def open_url_new_tab(self, url: str) -> None:
        script = r'''
on run argv
  set theURL to item 1 of argv

  tell application "Google Chrome"
    activate
    if (count of windows) = 0 then
      make new window
    end if

    tell front window
      make new tab with properties {URL:theURL}
    end tell
  end tell
end run
'''
        run_applescript(script, [url])

    def eval_js_active_tab(self, javascript: str) -> str:
        """
        Requires Chrome setting: View → Developer → Allow JavaScript from Apple Events.
        Returns the JS result coerced to text (or "" if missing).
        """
        script = r'''
on run argv
  set js to item 1 of argv

  tell application "Google Chrome"
    if (count of windows) = 0 then
      make new window
    end if

    tell active tab of front window
      set r to execute javascript js
      if r is missing value then
        return ""
      else
        return r as text
      end if
    end tell
  end tell
end run
'''
        return run_applescript(script, [javascript])

    def html_active_tab(self) -> str:
        return self.eval_js_active_tab("document.documentElement.outerHTML")


if __name__ == "__main__":
    events = ChromeAppleEvents()
    print("Tabs:")
    for tab in events.list_tabs():
        print(f"  {tab.window_index}:{tab.tab_index} {tab.title} ({tab.url})")

    active = events.active_tab()
    print(f"\nActive tab: {active.window_index}:{active.tab_index} {active.title} ({active.url})")