from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Final

from bs4 import BeautifulSoup
from bs4.element import Tag

_HIDDEN_STYLE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden",
    re.IGNORECASE,
)
_MAX_NAME_LENGTH: Final[int] = 80
_INTERACTIVE_ROLES: Final[frozenset[str]] = frozenset(
    {
        "button",
        "checkbox",
        "combobox",
        "link",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "option",
        "radio",
        "searchbox",
        "slider",
        "spinbutton",
        "switch",
        "textbox",
    },
)
_CONTENT_REF_ROLES: Final[frozenset[str]] = frozenset(
    {
        "article",
        "cell",
        "columnheader",
        "gridcell",
        "heading",
        "listitem",
        "main",
        "navigation",
        "region",
        "rowheader",
    },
)
_STRUCTURAL_ROLES: Final[frozenset[str]] = frozenset(
    {
        "article",
        "body",
        "div",
        "document",
        "html",
        "list",
        "main",
        "navigation",
        "region",
        "row",
        "section",
        "span",
        "table",
    },
)
_TEXT_FALLBACK_EXCLUDED_ROLES: Final[frozenset[str]] = frozenset(
    {
        "article",
        "body",
        "div",
        "document",
        "html",
        "list",
        "main",
        "navigation",
        "region",
        "row",
        "section",
        "span",
        "table",
    },
)
_ROLE_BY_TAG: Final[dict[str, str]] = {
    "article": "article",
    "body": "document",
    "button": "button",
    "html": "document",
    "img": "image",
    "li": "listitem",
    "main": "main",
    "nav": "navigation",
    "ol": "list",
    "option": "option",
    "select": "combobox",
    "table": "table",
    "td": "cell",
    "textarea": "textbox",
    "tr": "row",
    "ul": "list",
}
_HEADING_TAGS: Final[frozenset[str]] = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_INPUT_ROLE_BY_TYPE: Final[dict[str, str]] = {
    "button": "button",
    "checkbox": "checkbox",
    "email": "textbox",
    "image": "button",
    "number": "spinbutton",
    "password": "textbox",
    "radio": "radio",
    "range": "slider",
    "reset": "button",
    "search": "searchbox",
    "submit": "button",
    "tel": "textbox",
    "text": "textbox",
    "url": "textbox",
}


@dataclass(slots=True, frozen=True)
class SnapshotRef:
    selector: str
    role: str
    name: str | None
    nth: int | None


@dataclass(slots=True, frozen=True)
class Snapshot:
    tree: str = "(empty)"
    refs: dict[str, SnapshotRef] = field(default_factory=dict)

    @classmethod
    def from_source(
        cls,
        html: str,
        *,
        interactive: bool = False,
        max_depth: int | None = None,
        compact: bool = False,
    ) -> Snapshot:
        if not html.strip():
            return cls()

        builder = _SnapshotBuilder(
            html=html,
            interactive=interactive,
            max_depth=max_depth,
            compact=compact,
        )
        return builder.build_snapshot()

    def __str__(self) -> str:
        return self.tree


@dataclass(slots=True)
class _TreeNode:
    role: str
    name: str | None
    selector: str
    interactive: bool
    children: list[_TreeNode] = field(default_factory=list)
    ref: str | None = None
    nth: int | None = None


@dataclass(slots=True)
class _SnapshotBuilder:
    html: str
    interactive: bool
    max_depth: int | None
    compact: bool
    _soup: BeautifulSoup = field(init=False, repr=False)
    _id_map: dict[str, Tag] = field(init=False, repr=False)
    _label_map: dict[str, list[str]] = field(init=False, repr=False)
    _refs: dict[str, SnapshotRef] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._soup = BeautifulSoup(self.html, "html.parser")
        self._id_map: dict[str, Tag] = {}
        self._label_map: dict[str, list[str]] = defaultdict(list)
        self._refs: dict[str, SnapshotRef] = {}
        self._index_document()

    def build_snapshot(self) -> Snapshot:
        root = self._resolve_root()
        if root is None:
            return Snapshot()

        tree = self._build_tree(root, depth=0)
        if tree is None:
            return Snapshot()

        self._assign_refs(tree)
        lines = self._render_tree(tree, depth=0)
        tree_text = "\n".join(lines) or "(empty)"
        refs = self._refs if lines else {}
        return Snapshot(tree=tree_text, refs=refs)

    def _resolve_root(self) -> Tag | None:
        body = self._soup.body
        if isinstance(body, Tag):
            return body

        html = self._soup.html
        if isinstance(html, Tag):
            return html

        for candidate in self._soup.children:
            if isinstance(candidate, Tag):
                return candidate

        return None

    def _index_document(self) -> None:
        for tag in self._soup.find_all(name=True):
            tag_id = _attribute_value(tag, "id")
            if tag_id is not None:
                self._id_map.setdefault(tag_id, tag)

            if tag.name != "label":
                continue

            target_id = _attribute_value(tag, "for")
            if target_id is None or self._is_hidden(tag):
                continue

            label_text = _text_content(tag)
            if label_text is not None:
                self._label_map[target_id].append(label_text)

    def _build_tree(self, tag: Tag, *, depth: int) -> _TreeNode | None:
        if self.max_depth is not None and depth > self.max_depth:
            return None
        if self._is_hidden(tag):
            return None

        role = self._infer_role(tag)
        name = self._infer_name(tag, role)
        interactive = role in _INTERACTIVE_ROLES
        selector = self._build_selector(tag)

        children: list[_TreeNode] = []
        for child in tag.children:
            if not isinstance(child, Tag):
                continue

            child_tree = self._build_tree(child, depth=depth + 1)
            if child_tree is not None:
                children.append(child_tree)

        include_self = (
            interactive
            if self.interactive
            else self._is_meaningful(role, name, is_interactive=interactive)
        )
        if include_self or children:
            return _TreeNode(
                role=role,
                name=name,
                selector=selector,
                interactive=interactive,
                children=children,
            )

        return None

    def _is_hidden(self, tag: Tag) -> bool:
        if tag.has_attr("hidden"):
            return True

        if tag.name == "input" and _attribute_value(tag, "type") == "hidden":
            return True

        aria_hidden = _attribute_value(tag, "aria-hidden")
        if aria_hidden is not None and aria_hidden.casefold() == "true":
            return True

        style = _attribute_value(tag, "style")
        return style is not None and _HIDDEN_STYLE_PATTERN.search(style) is not None

    def _infer_role(self, tag: Tag) -> str:
        explicit_role = _attribute_value(tag, "role")
        if explicit_role:
            return explicit_role.split(maxsplit=1)[0].casefold()

        tag_name = tag.name.casefold()
        if tag_name == "a":
            role = "link" if tag.has_attr("href") else tag_name
        elif tag_name in _HEADING_TAGS:
            role = "heading"
        elif tag_name == "section":
            role = self._section_role(tag)
        elif tag_name == "th":
            role = "rowheader" if _attribute_value(tag, "scope") == "row" else "columnheader"
        elif tag_name == "input":
            role = _INPUT_ROLE_BY_TYPE.get(_attribute_value(tag, "type") or "text", "input")
        else:
            role = _ROLE_BY_TAG.get(tag_name, tag_name)

        return role

    def _infer_name(self, tag: Tag, role: str) -> str | None:
        for name_candidate in (
            self._name_from_aria_label(tag),
            self._name_from_aria_labelled_by(tag),
            self._name_from_associated_label(tag),
            self._name_from_wrapping_label(tag),
            self._name_from_control_attrs(tag),
        ):
            if name_candidate is not None:
                return _truncate_name(name_candidate)

        if role in _TEXT_FALLBACK_EXCLUDED_ROLES:
            return None

        text_fallback = _text_content(tag)
        return _truncate_name(text_fallback) if text_fallback is not None else None

    def _section_role(self, tag: Tag) -> str:
        labelled = _attribute_value(tag, "aria-label")
        labelled_by = _attribute_value(tag, "aria-labelledby")
        return "region" if labelled is not None or labelled_by is not None else "section"

    def _name_from_aria_label(self, tag: Tag) -> str | None:
        return _attribute_value(tag, "aria-label")

    def _name_from_aria_labelled_by(self, tag: Tag) -> str | None:
        labelled_by = _attribute_value(tag, "aria-labelledby")
        if labelled_by is None:
            return None

        label_parts: list[str] = []
        for reference in labelled_by.split():
            referenced_tag = self._id_map.get(reference)
            if referenced_tag is None:
                continue
            text = _text_content(referenced_tag)
            if text is not None:
                label_parts.append(text)

        joined = _normalize_text(" ".join(label_parts))
        return joined or None

    def _name_from_associated_label(self, tag: Tag) -> str | None:
        tag_id = _attribute_value(tag, "id")
        if tag_id is None:
            return None

        mapped_labels = self._label_map.get(tag_id, [])
        if not mapped_labels:
            return None

        joined = _normalize_text(" ".join(mapped_labels))
        return joined or None

    def _name_from_wrapping_label(self, tag: Tag) -> str | None:
        wrapping_label = tag.find_parent("label")
        if not isinstance(wrapping_label, Tag):
            return None
        return _text_content(wrapping_label)

    def _name_from_control_attrs(self, tag: Tag) -> str | None:
        for attr_name in ("placeholder", "alt", "value"):
            attr_value = _attribute_value(tag, attr_name)
            if attr_value is not None:
                return attr_value
        return None

    def _is_meaningful(self, role: str, name: str | None, *, is_interactive: bool) -> bool:
        if is_interactive:
            return True
        if name is None:
            return role in _STRUCTURAL_ROLES
        if role in _CONTENT_REF_ROLES:
            return True
        return role not in {"document", "html", "body"}

    def _assign_refs(self, root: _TreeNode) -> None:
        candidates = list(self._iter_ref_candidates(root))
        duplicate_counts: dict[tuple[str, str], int] = defaultdict(int)
        for candidate in candidates:
            if candidate.name is None:
                continue
            duplicate_counts[candidate.role, candidate.name] += 1

        duplicate_seen: dict[tuple[str, str], int] = defaultdict(int)
        for index, candidate in enumerate(candidates, start=1):
            nth: int | None = None
            if candidate.name is not None:
                key = (candidate.role, candidate.name)
                if duplicate_counts[key] > 1:
                    nth = duplicate_seen[key]
                    duplicate_seen[key] += 1

            ref_key = f"e{index}"
            candidate.ref = ref_key
            candidate.nth = nth
            self._refs[ref_key] = SnapshotRef(
                selector=candidate.selector,
                role=candidate.role,
                name=candidate.name,
                nth=nth,
            )

    def _iter_ref_candidates(self, node: _TreeNode) -> list[_TreeNode]:
        nodes: list[_TreeNode] = []
        if node.interactive or (node.role in _CONTENT_REF_ROLES and node.name is not None):
            nodes.append(node)

        for child in node.children:
            nodes.extend(self._iter_ref_candidates(child))

        return nodes

    def _build_selector(self, tag: Tag) -> str:
        tag_id = _attribute_value(tag, "id")
        if tag_id is not None:
            return f"#{_escape_css_identifier(tag_id)}"

        test_id = _attribute_value(tag, "data-testid")
        if test_id is not None:
            escaped = _escape_css_string(test_id)
            return f'[data-testid="{escaped}"]'

        parts: list[str] = []
        current: Tag | None = tag
        while current is not None and current.name and current.name != "[document]":
            index = 1
            for sibling in current.previous_siblings:
                if isinstance(sibling, Tag) and sibling.name == current.name:
                    index += 1

            parts.append(f"{current.name}:nth-of-type({index})")
            parent = current.parent
            current = parent if isinstance(parent, Tag) else None

        parts.reverse()
        return " > ".join(parts)

    def _render_tree(self, node: _TreeNode, *, depth: int) -> list[str]:
        if self.compact and self._is_compactable(node):
            compact_lines: list[str] = []
            for child in node.children:
                compact_lines.extend(self._render_tree(child, depth=depth))
            return compact_lines

        line = f"{'  ' * depth}- {node.role}"
        if node.name is not None:
            escaped_name = node.name.replace('"', '\\"')
            line = f'{line} "{escaped_name}"'
        if node.ref is not None:
            line = f"{line} [ref={node.ref}]"
        if node.nth is not None and node.nth > 0:
            line = f"{line} [nth={node.nth}]"

        lines = [line]
        for child in node.children:
            lines.extend(self._render_tree(child, depth=depth + 1))
        return lines

    def _is_compactable(self, node: _TreeNode) -> bool:
        if node.ref is not None or node.name is not None:
            return False
        if node.role not in _STRUCTURAL_ROLES:
            return False
        return bool(node.children)


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _truncate_name(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= _MAX_NAME_LENGTH:
        return value

    prefix = value[: _MAX_NAME_LENGTH - 3].rstrip()
    return f"{prefix}..."


def _text_content(tag: Tag) -> str | None:
    text = _normalize_text(tag.get_text(" ", strip=True))
    return text or None


def _attribute_value(tag: Tag, name: str) -> str | None:
    if not tag.has_attr(name):
        return None

    raw = tag.attrs.get(name)
    if isinstance(raw, str):
        normalized = _normalize_text(raw)
        return normalized.casefold() if name in {"type", "scope"} else normalized

    if isinstance(raw, list):
        joined = _normalize_text(" ".join(str(item) for item in raw))
        return joined or None

    return None


def _escape_css_identifier(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    return escaped.replace(" ", "\\ ")


def _escape_css_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    return escaped.replace('"', '\\"')
