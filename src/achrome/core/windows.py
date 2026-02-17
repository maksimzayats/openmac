from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core.tabs import TabsManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, Unpack


@dataclass(slots=True)
class Window:
    id: int
    name: str
    tabs: TabsManager = field(init=False)


class WindowsFilterCriteria(TypedDict):
    id: NotRequired[int]
    id__in: NotRequired[list[int]]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]


class WindowsManager(BaseManager[Window]):
    def _load_items(self) -> list[Window]:
        script = """
        use AppleScript version "2.8"
        use framework "Foundation"
        use scripting additions

        on nsBool(v)
            return current application's NSNumber's numberWithBool:(v = true)
        end nsBool

        on safeText(v)
            if v is missing value then
                return current application's NSNull's null()
            end if
            return v as text
        end safeText

        set windowData to current application's NSMutableArray's array()

        tell application "Google Chrome"
            repeat with w in windows
                set windowRec to current application's NSMutableDictionary's dictionary()

                windowRec's setObject:((id of w) as integer) forKey:"id"
                windowRec's setObject:((name of w) as string) forKey:"name"

                windowData's addObject:windowRec
            end repeat
        end tell

        set {jsonData, jsonError} to current application's NSJSONSerialization's ¬
            dataWithJSONObject:windowData options:0 |error|:(reference)

        if jsonData is missing value then
            return "JSON serialization failed: " & ((jsonError's localizedDescription()) as text)
        end if

        set jsonString to (current application's NSString's alloc()'s ¬
            initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)) as text

        return jsonString

        """

        result = self._context.runner.run(script)
        adapter = TypeAdapter(list[Window])
        windows = adapter.validate_json(result)
        for window in windows:
            window.tabs = TabsManager(_context=self._context, _window_id=window.id)

        return windows

    if TYPE_CHECKING:

        def filter(self, **criteria: Unpack[WindowsFilterCriteria]) -> Self: ...  # type: ignore[override]
        def get(self, **criteria: Unpack[WindowsFilterCriteria]) -> Window: ...  # type: ignore[override]
