from __future__ import annotations

import json
from typing import Final

INTERACTIVE_ROLES: Final[tuple[str, ...]] = (
    "button",
    "link",
    "textbox",
    "checkbox",
    "radio",
    "combobox",
    "listbox",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "option",
    "searchbox",
    "slider",
    "spinbutton",
    "switch",
    "tab",
    "treeitem",
)

CONTENT_ROLES: Final[tuple[str, ...]] = (
    "heading",
    "cell",
    "gridcell",
    "columnheader",
    "rowheader",
    "listitem",
    "article",
    "region",
    "main",
    "navigation",
)

STRUCTURAL_ROLES: Final[tuple[str, ...]] = (
    "generic",
    "group",
    "list",
    "table",
    "row",
    "rowgroup",
    "grid",
    "treegrid",
    "menu",
    "menubar",
    "toolbar",
    "tablist",
    "tree",
    "directory",
    "document",
    "application",
    "presentation",
    "none",
)


def build_snapshot_javascript(
    *,
    interactive: bool,
    cursor: bool,
    max_depth: int | None,
    compact: bool,
    selector: str | None,
) -> str:
    """Build JavaScript expression for DOM snapshot generation."""
    options_json = json.dumps(
        {
            "interactive": interactive,
            "cursor": cursor,
            "maxDepth": max_depth,
            "compact": compact,
            "selector": selector,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )
    interactive_roles_json = json.dumps(list(INTERACTIVE_ROLES), separators=(",", ":"))
    content_roles_json = json.dumps(list(CONTENT_ROLES), separators=(",", ":"))
    structural_roles_json = json.dumps(list(STRUCTURAL_ROLES), separators=(",", ":"))

    script = """
(function () {
  const options = __OPTIONS__;
  const INTERACTIVE_ROLES = new Set(__INTERACTIVE_ROLES__);
  const CONTENT_ROLES = new Set(__CONTENT_ROLES__);
  const STRUCTURAL_ROLES = new Set(__STRUCTURAL_ROLES__);
  const interactiveTags = new Set(["a", "button", "input", "select", "textarea", "summary"]);
  let refCounter = 0;
  const refs = {};
  const rows = [];
  const duplicateCounts = new Map();

  const nextRef = () => "e" + String(++refCounter);
  const normalizeText = (value) => value.replace(/\\s+/g, " ").trim();
  const escapeQuoted = (value) => value.replace(/\\\\/g, "\\\\\\\\").replace(/"/g, "\\\\\\"");

  const byIdText = (id) => {
    const target = document.getElementById(id);
    if (!target) {
      return "";
    }
    return normalizeText(target.textContent || "");
  };

  const isHidden = (el) => {
    if (el.hidden) {
      return true;
    }
    if ((el.getAttribute("aria-hidden") || "").toLowerCase() === "true") {
      return true;
    }
    const style = getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") {
      return true;
    }
    const rect = el.getBoundingClientRect();
    return rect.width <= 0 || rect.height <= 0;
  };

  const inferRole = (el) => {
    const explicit = normalizeText(el.getAttribute("role") || "").toLowerCase();
    if (explicit) {
      return explicit;
    }

    const tag = el.tagName.toLowerCase();
    if (tag === "a" && el.hasAttribute("href")) {
      return "link";
    }
    if (tag === "button" || tag === "summary") {
      return "button";
    }
    if (tag === "textarea") {
      return "textbox";
    }
    if (tag === "select") {
      return "combobox";
    }
    if (tag === "option") {
      return "option";
    }
    if (tag === "li") {
      return "listitem";
    }
    if (tag === "main") {
      return "main";
    }
    if (tag === "nav") {
      return "navigation";
    }
    if (tag === "article") {
      return "article";
    }
    if (tag === "section") {
      return "region";
    }
    if (/^h[1-6]$/.test(tag)) {
      return "heading";
    }
    if (tag === "th") {
      return "columnheader";
    }
    if (tag === "td") {
      return "cell";
    }
    if (tag === "input") {
      const inputType = (el.getAttribute("type") || "text").toLowerCase();
      if (inputType === "checkbox") {
        return "checkbox";
      }
      if (inputType === "radio") {
        return "radio";
      }
      if (inputType === "range") {
        return "slider";
      }
      if (inputType === "search") {
        return "searchbox";
      }
      if (["button", "submit", "reset", "image"].includes(inputType)) {
        return "button";
      }
      return "textbox";
    }
    return "generic";
  };

  const inferName = (el, role) => {
    const ariaLabel = normalizeText(el.getAttribute("aria-label") || "");
    if (ariaLabel) {
      return ariaLabel;
    }

    const labelledBy = normalizeText(el.getAttribute("aria-labelledby") || "");
    if (labelledBy) {
      const labels = labelledBy.split(/\\s+/).map(byIdText).filter(Boolean);
      if (labels.length > 0) {
        return normalizeText(labels.join(" "));
      }
    }

    const alt = normalizeText(el.getAttribute("alt") || "");
    if (alt) {
      return alt;
    }
    const title = normalizeText(el.getAttribute("title") || "");
    if (title) {
      return title;
    }

    if (el.tagName.toLowerCase() === "input") {
      const inputType = (el.getAttribute("type") || "text").toLowerCase();
      if (["button", "submit", "reset"].includes(inputType)) {
        return normalizeText(el.getAttribute("value") || "");
      }
      const placeholder = normalizeText(el.getAttribute("placeholder") || "");
      if (placeholder) {
        return placeholder;
      }
    }

    if (role === "combobox") {
      const selected = el.querySelector("option:checked");
      if (selected) {
        return normalizeText(selected.textContent || "");
      }
    }

    const textValue = normalizeText(el.textContent || "");
    if (textValue) {
      return textValue.slice(0, 200);
    }

    return "";
  };

  const buildRoleSelector = (role, name) => {
    if (name) {
      return "getByRole('" + role + "', { name: \\"" + escapeQuoted(name) + "\\", exact: true })";
    }
    return "getByRole('" + role + "')";
  };

  const buildCssSelector = (el) => {
    const testId = el.getAttribute("data-testid");
    if (testId) {
      return "[data-testid=\\"" + escapeQuoted(testId) + "\\"]";
    }
    if (el.id) {
      return "#" + CSS.escape(el.id);
    }

    const path = [];
    let current = el;
    while (current && current !== document.body && path.length < 10) {
      let selector = current.tagName.toLowerCase();
      const classNames = Array.from(current.classList).filter((name) => normalizeText(name));
      if (classNames.length > 0) {
        selector += "." + CSS.escape(classNames[0]);
      }
      const parent = current.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter((candidate) => {
          if (candidate.tagName !== current.tagName) {
            return false;
          }
          if (classNames.length === 0) {
            return true;
          }
          return candidate.classList.contains(classNames[0]);
        });
        if (siblings.length > 1) {
          selector += ":nth-of-type(" + String(siblings.indexOf(current) + 1) + ")";
        }
      }
      path.unshift(selector);
      const candidatePath = path.join(" > ");
      try {
        if (document.querySelectorAll(candidatePath).length === 1) {
          return candidatePath;
        }
      } catch (_error) {
        // Keep building if CSS selector parsing fails.
      }
      current = parent;
    }
    return path.join(" > ");
  };

  const addRef = (role, name, linePrefix) => {
    const ref = nextRef();
    const key = role + ":" + (name || "");
    const nth = duplicateCounts.get(key) || 0;
    duplicateCounts.set(key, nth + 1);

    const refData = { selector: buildRoleSelector(role, name), role: role };
    if (name) {
      refData.name = name;
    }
    refs[ref] = refData;

    rows.push({
      text: linePrefix + " [ref=" + ref + "]",
      key: key,
      nth: nth,
      ref: ref,
      isCursor: false,
    });
  };

  const addLine = (line) => {
    rows.push({ text: line, key: "", nth: 0, ref: null, isCursor: false });
  };

  const shouldAddRef = (role, name) => {
    return INTERACTIVE_ROLES.has(role) || (CONTENT_ROLES.has(role) && Boolean(name));
  };

  const visit = (el, depth, outputDepth) => {
    if (!(el instanceof Element) || isHidden(el)) {
      return;
    }
    if (options.maxDepth !== null && options.maxDepth !== undefined && depth > options.maxDepth) {
      return;
    }

    const role = inferRole(el);
    const name = inferName(el, role);
    const isInteractive = INTERACTIVE_ROLES.has(role);
    const isStructural = STRUCTURAL_ROLES.has(role);
    const keepInInteractiveMode = !options.interactive || isInteractive;
    const keepInCompactMode = !(options.compact && isStructural && !name);
    const shouldOutput = keepInInteractiveMode && keepInCompactMode;

    const nextOutputDepth = shouldOutput ? outputDepth + 1 : outputDepth;

    if (shouldOutput) {
      let line = "  ".repeat(outputDepth) + "- " + role;
      if (name) {
        line += " \\"" + escapeQuoted(name) + "\\"";
      }
      if (shouldAddRef(role, name)) {
        addRef(role, name, line);
      } else {
        addLine(line);
      }
    }

    for (const child of Array.from(el.children)) {
      visit(child, depth + 1, nextOutputDepth);
    }
  };

  const root = options.selector
    ? document.querySelector(options.selector)
    : document.body || document.documentElement;
  if (!root) {
    return { tree: "(empty)", refs: {} };
  }

  if (options.selector) {
    visit(root, 0, 0);
  } else {
    for (const child of Array.from(root.children)) {
      visit(child, 0, 0);
    }
  }

  const duplicateKeys = new Set(
    Array.from(duplicateCounts.entries())
      .filter((entry) => entry[1] > 1)
      .map((entry) => entry[0]),
  );

  const initialLines = [];
  for (const row of rows) {
    if (!row.ref) {
      initialLines.push(row.text);
      continue;
    }
    if (duplicateKeys.has(row.key)) {
      refs[row.ref].nth = row.nth;
      if (row.nth > 0) {
        initialLines.push(row.text + " [nth=" + String(row.nth) + "]");
      } else {
        initialLines.push(row.text);
      }
      continue;
    }
    initialLines.push(row.text);
  }

  let tree = initialLines.join("\\n");
  if (options.interactive && !tree) {
    tree = "(no interactive elements)";
  } else if (!tree) {
    tree = "(empty)";
  }

  if (options.cursor) {
    const existingTexts = new Set(
      Object.values(refs)
        .map((value) => (typeof value.name === "string" ? value.name.toLowerCase() : ""))
        .filter(Boolean),
    );
    const cursorLines = [];
    const cursorRoot = options.selector
      ? document.querySelector(options.selector) || document.body
      : document.body || document.documentElement;
    const candidates = cursorRoot ? Array.from(cursorRoot.querySelectorAll("*")) : [];

    for (const candidate of candidates) {
      if (!(candidate instanceof Element) || isHidden(candidate)) {
        continue;
      }
      const tagName = candidate.tagName.toLowerCase();
      const role = normalizeText(candidate.getAttribute("role") || "").toLowerCase();
      if (interactiveTags.has(tagName) || (role && INTERACTIVE_ROLES.has(role))) {
        continue;
      }

      const style = getComputedStyle(candidate);
      const hasCursorPointer = style.cursor === "pointer";
      const hasOnClick =
        candidate.hasAttribute("onclick") || typeof candidate.onclick === "function";
      const tabIndexValue = candidate.getAttribute("tabindex");
      const hasTabIndex = tabIndexValue !== null && tabIndexValue !== "-1";
      if (!hasCursorPointer && !hasOnClick && !hasTabIndex) {
        continue;
      }

      const text = normalizeText(candidate.textContent || "").slice(0, 200);
      if (!text || existingTexts.has(text.toLowerCase())) {
        continue;
      }

      const cursorRole = hasCursorPointer || hasOnClick ? "clickable" : "focusable";
      const ref = nextRef();
      refs[ref] = {
        selector: buildCssSelector(candidate),
        role: cursorRole,
        name: text,
      };

      const hints = [];
      if (hasCursorPointer) {
        hints.push("cursor:pointer");
      }
      if (hasOnClick) {
        hints.push("onclick");
      }
      if (hasTabIndex) {
        hints.push("tabindex");
      }

      cursorLines.push(
        "- " +
          cursorRole +
          " \\"" +
          escapeQuoted(text) +
          "\\" [ref=" +
          ref +
          "] [" +
          hints.join(", ") +
          "]",
      );
      existingTexts.add(text.toLowerCase());
    }

    if (cursorLines.length > 0) {
      if (tree === "(no interactive elements)") {
        tree = cursorLines.join("\\n");
      } else {
        tree = tree + "\\n# Cursor-interactive elements:\\n" + cursorLines.join("\\n");
      }
    }
  }

  return { tree: tree, refs: refs };
})()
""".strip()

    return (
        script.replace("__OPTIONS__", options_json)
        .replace("__INTERACTIVE_ROLES__", interactive_roles_json)
        .replace("__CONTENT_ROLES__", content_roles_json)
        .replace("__STRUCTURAL_ROLES__", structural_roles_json)
    )
