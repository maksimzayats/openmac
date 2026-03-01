from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class GenericPage(BaseModel):
    root: GenericPageElement


class GenericPageElement(BaseModel):
    text: str
    js_path: str = Field(
        description=(
            "The JavaScript path to locate this element in the DOM. This can be used to"
            "interact with the element programmatically, e.g., to click a button or extract more information."
            "Example: '#main > div:nth-child(2) > p'"
        ),
    )
    element_type: str = Field(
        description=(
            "The type of the HTML element (e.g., 'div', 'p', 'span'). This can provide context about the role of the element in the page structure."
        ),
    )
    scrollable: bool = Field(
        description=(
            "Indicates whether the element is scrollable. "
            "This can be useful for determining if the element contains overflow content that may not be immediately visible."
        ),
    )
    elements: list[GenericPageElement] = Field(description="Child elements of this HTML element.")

    _execute_javascript: Callable[[str], Any]

    def populate_javascript_executor(self, executor: Callable[[str], Any]) -> None:
        self._execute_javascript = executor
        for child in self.elements:
            child.populate_javascript_executor(executor)

    def click(self) -> None:
        function = """
            function realClick(el) {
              const rect = el.getBoundingClientRect();
              const x = rect.left + rect.width / 2;
              const y = rect.top + rect.height / 2;

              ["pointerdown", "mousedown", "mouseup", "click"].forEach(type => {
                el.dispatchEvent(new MouseEvent(type, {
                  view: window,
                  bubbles: true,
                  cancelable: true,
                  clientX: x,
                  clientY: y,
                  button: 0
                }));
              });
            }
        """

        script = f"""
            (function() {{
                {function}
                const el = document.querySelector("{self.js_path}");
                if (el) {{
                    realClick(el);
                    return true;
                }} else {{
                    return false;
                }}
            }})()
         """

        result = self._execute_javascript(script)
        if not result:
            raise ValueError(f"Element with js_path '{self.js_path}' not found for clicking.")
