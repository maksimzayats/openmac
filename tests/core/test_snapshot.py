from __future__ import annotations

from typing import cast

from bs4 import BeautifulSoup

from achrome.core.source import Snapshot, _attribute_value, _truncate_name


def test_snapshot_from_empty_and_text_only_source_returns_empty() -> None:
    empty_snapshot = Snapshot.from_source("")
    text_only_snapshot = Snapshot.from_source("plain text")

    assert empty_snapshot.tree == "(empty)"
    assert empty_snapshot.refs == {}
    assert text_only_snapshot.tree == "(empty)"
    assert text_only_snapshot.refs == {}


def test_snapshot_builds_role_first_tree_and_stable_refs() -> None:
    html = """
    <html>
      <body>
        <main>
          <h1>Welcome</h1>
          <a href="/docs">Docs</a>
          <button>Continue</button>
          <input type="text" placeholder="Search" />
        </main>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert str(snapshot) == snapshot.tree
    assert '- heading "Welcome" [ref=e1]' in snapshot.tree
    assert '- link "Docs" [ref=e2]' in snapshot.tree
    assert '- button "Continue" [ref=e3]' in snapshot.tree
    assert '- textbox "Search" [ref=e4]' in snapshot.tree
    assert list(snapshot.refs) == ["e1", "e2", "e3", "e4"]


def test_snapshot_name_inference_precedence_is_stable() -> None:
    html = """
    <html>
      <body>
        <span id="external">External Label</span>
        <label for="with-for">For Label</label>
        <input id="with-aria-label" aria-label="Aria Label" aria-labelledby="external" />
        <input id="with-aria-labelledby" aria-labelledby="external" />
        <input id="with-for" placeholder="Placeholder Value" />
        <input id="with-placeholder" placeholder="Placeholder Wins" value="Ignore Me" />
        <button>Text Fallback</button>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)
    refs_by_selector = {ref.selector: ref for ref in snapshot.refs.values()}

    assert refs_by_selector["#with-aria-label"].name == "Aria Label"
    assert refs_by_selector["#with-aria-labelledby"].name == "External Label"
    assert refs_by_selector["#with-for"].name == "For Label"
    assert refs_by_selector["#with-placeholder"].name == "Placeholder Wins"
    assert any(
        ref.role == "button" and ref.name == "Text Fallback" for ref in snapshot.refs.values()
    )


def test_snapshot_prefers_id_then_test_id_then_css_path() -> None:
    html = """
    <html>
      <body>
        <button id="with-id" data-testid="ignored">With Id</button>
        <button data-testid="with-test-id">With Test Id</button>
        <div>
          <button>Path Selector</button>
        </div>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert snapshot.refs["e1"].selector == "#with-id"
    assert snapshot.refs["e2"].selector == '[data-testid="with-test-id"]'
    assert (
        snapshot.refs["e3"].selector
        == "html:nth-of-type(1) > body:nth-of-type(1) > div:nth-of-type(1) > button:nth-of-type(1)"
    )


def test_snapshot_duplicate_role_name_tracks_nth_for_duplicates_only() -> None:
    html = """
    <html>
      <body>
        <button>Save</button>
        <button>Save</button>
        <button>Cancel</button>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert snapshot.refs["e1"].name == "Save"
    assert snapshot.refs["e2"].name == "Save"
    assert snapshot.refs["e1"].nth == 0
    assert snapshot.refs["e2"].nth == 1
    assert snapshot.refs["e3"].nth is None
    assert "[nth=0]" not in snapshot.tree
    assert snapshot.tree.count("[nth=1]") == 1


def test_snapshot_excludes_hidden_nodes_from_source_hints() -> None:
    html = """
    <html>
      <body>
        <button>Visible</button>
        <button hidden>Hidden Attribute</button>
        <button aria-hidden="true">Aria Hidden</button>
        <button style="display: none">Display None</button>
        <button style="visibility:hidden">Visibility Hidden</button>
        <input type="hidden" value="secret" />
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert list(snapshot.refs) == ["e1"]
    assert snapshot.refs["e1"].name == "Visible"
    assert "Hidden Attribute" not in snapshot.tree
    assert "Aria Hidden" not in snapshot.tree
    assert "Display None" not in snapshot.tree
    assert "Visibility Hidden" not in snapshot.tree


def test_snapshot_interactive_mode_keeps_only_interactive_nodes() -> None:
    html = """
    <html>
      <body>
        <h1>Heading</h1>
        <p>Body text</p>
        <button>Click</button>
        <a href="/go">Go</a>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html, interactive=True)

    assert "Heading" not in snapshot.tree
    assert "Body text" not in snapshot.tree
    assert '- button "Click" [ref=e1]' in snapshot.tree
    assert '- link "Go" [ref=e2]' in snapshot.tree
    assert all(ref.role in {"button", "link"} for ref in snapshot.refs.values())


def test_snapshot_respects_max_depth() -> None:
    html = """
    <html>
      <body>
        <div>
          <section>
            <button>Too Deep</button>
          </section>
        </div>
      </body>
    </html>
    """

    truncated = Snapshot.from_source(html, max_depth=2)
    full = Snapshot.from_source(html)

    assert "Too Deep" not in truncated.tree
    assert truncated.refs == {}
    assert "Too Deep" in full.tree
    assert full.refs["e1"].name == "Too Deep"


def test_snapshot_compact_mode_removes_empty_structural_branches() -> None:
    html = """
    <html>
      <body>
        <div>
          <div>
            <span>
              <button>Run</button>
            </span>
          </div>
        </div>
      </body>
    </html>
    """

    expanded = Snapshot.from_source(html, compact=False)
    compact = Snapshot.from_source(html, compact=True)

    assert '- button "Run" [ref=e1]' in expanded.tree
    assert '- button "Run" [ref=e1]' in compact.tree
    assert len(compact.tree.splitlines()) < len(expanded.tree.splitlines())
    assert "- div" not in compact.tree


def test_snapshot_handles_root_fallbacks_and_hidden_root() -> None:
    html_root_snapshot = Snapshot.from_source("<html><h1>Html Root</h1></html>")
    candidate_root_snapshot = Snapshot.from_source("<svg><title>Vector Title</title></svg>")
    hidden_root_snapshot = Snapshot.from_source("<body hidden><button>Never</button></body>")

    assert "Html Root" in html_root_snapshot.tree
    assert "Vector Title" in candidate_root_snapshot.tree
    assert hidden_root_snapshot.tree == "(empty)"
    assert hidden_root_snapshot.refs == {}


def test_snapshot_ignores_hidden_or_empty_labels_during_name_resolution() -> None:
    html = """
    <html>
      <body>
        <label for="target" hidden>Hidden Label</label>
        <label for="target"></label>
        <input id="target" placeholder="Placeholder Name" />
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert snapshot.refs["e1"].name == "Placeholder Name"


def test_snapshot_resolves_explicit_role_scope_and_wrapped_label_names() -> None:
    html = """
    <html>
      <body>
        <div role="menuitem">Menu Item</div>
        <table>
          <tr>
            <th scope="row">Row Header</th>
          </tr>
        </table>
        <label>Wrapped Label <input id="wrapped" /></label>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)
    refs_by_selector = {ref.selector: ref for ref in snapshot.refs.values()}

    assert any(ref.role == "menuitem" and ref.name == "Menu Item" for ref in snapshot.refs.values())
    assert any(
        ref.role == "rowheader" and ref.name == "Row Header" for ref in snapshot.refs.values()
    )
    assert refs_by_selector["#wrapped"].name == "Wrapped Label"


def test_snapshot_handles_missing_and_empty_aria_labelledby_targets() -> None:
    html = """
    <html>
      <body>
        <span id="empty"></span>
        <input id="with-labels" aria-labelledby="missing empty" placeholder="Fallback Label" />
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert snapshot.refs["e1"].name == "Fallback Label"


def test_snapshot_assigns_refs_to_nameless_interactive_nodes() -> None:
    html = """
    <html>
      <body>
        <button></button>
        <button>Named</button>
      </body>
    </html>
    """

    snapshot = Snapshot.from_source(html)

    assert snapshot.refs["e1"].name is None
    assert snapshot.refs["e1"].nth is None
    assert snapshot.refs["e2"].name == "Named"


def test_snapshot_compact_mode_keeps_non_structural_nodes() -> None:
    html = """
    <html>
      <body>
        <custom>
          <input type="text" />
        </custom>
      </body>
    </html>
    """

    compact = Snapshot.from_source(html, compact=True)

    assert "- custom" in compact.tree
    assert "- textbox [ref=e1]" in compact.tree


def test_snapshot_private_helpers_cover_edge_cases() -> None:
    soup = BeautifulSoup('<div class="a b" data-testid="x"></div>', "html.parser")
    tag = soup.find("div")
    assert tag is not None
    cast("dict[str, object]", tag.attrs)["data-custom"] = 123

    assert _truncate_name(None) is None
    assert _truncate_name("short") == "short"
    assert _truncate_name("x" * 81) == ("x" * 77) + "..."
    assert _attribute_value(tag, "class") == "a b"
    assert _attribute_value(tag, "data-custom") is None
    assert _attribute_value(tag, "unknown") is None
