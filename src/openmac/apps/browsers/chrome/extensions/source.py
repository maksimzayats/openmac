from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from openmac.apps.browsers.chrome.objects.tabs import ChromeTab


@dataclass(slots=True)
class Source:
    tab: ChromeTab

    @property
    def html(self) -> str:
        return cast("str", self.tab.execute("document.documentElement.outerHTML"))

    @property
    def body(self) -> str:
        return cast("str", self.tab.execute("document.body.outerHTML"))

    @property
    def readable_body(self) -> str:
        script = dedent(
            """
            (function () {
              const excludedSelectors = [
                "script",
                "style",
                "noscript",
                "meta",
                "link",
                "iframe",
                "svg",
                "canvas"
              ];

              // Attributes we allow to survive (structural only)
              const allowedAttributes = new Set([
                "id",
                "class",
                "href",
                "src",
                "alt",
                "title",
                "type",
                "name",
                "value",
                "placeholder",
                "role",
                "aria-label"
              ]);

              const clone = document.body.cloneNode(true);

              // Remove unwanted tags completely
              clone.querySelectorAll(excludedSelectors.join(","))
                .forEach(el => el.remove());

              clone.querySelectorAll("*").forEach(el => {
                // Remove ALL attributes except allowed ones
                [...el.attributes].forEach(attr => {
                  const name = attr.name.toLowerCase();

                  if (
                    name.startsWith("on") ||          // onclick, onload, etc.
                    name === "style" ||               // inline styles
                    name.startsWith("data-") ||       // data attrs
                    !allowedAttributes.has(name)      // not in whitelist
                  ) {
                    el.removeAttribute(attr.name);
                  }
                });

                // Remove empty elements (no text and no children)
                if (
                  el.children.length === 0 &&
                  !el.textContent.trim()
                ) {
                  el.remove();
                }
              });

              const result = clone.outerHTML;

              console.log(result);
              return result;
            })();
            """,
        ).strip()

        return cast("str", self.tab.execute(script))
