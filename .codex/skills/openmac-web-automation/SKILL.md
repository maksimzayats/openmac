---
name: openmac-web-automation
description: Automate browser workflows with openmac (Chrome tabs plus JavaScript execute) using robust inspect-plan-act-verify loops. Use when Codex must analyze a live web page, create LLM-ready snapshots, perform multi-step actions (click/type/scroll/navigate), extract structured data (for example GitHub pull requests), or debug flaky web automation on SPA pages.
---

# Openmac Web Automation

## Overview

Use this skill to drive Chrome tabs through `openmac` with deterministic action execution and strict verification. Prefer compact semantic snapshots plus actionable element metadata instead of raw full-page HTML.

## Quick Start

1. Get the right tab:
```python
from openmac import Chrome

chrome = Chrome()
tab = chrome.tabs.get(url__contains="github.com")
```

2. Capture compact state:
```python
snapshot = tab.execute(
    """
    (() => {
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.display !== "none" && s.visibility !== "hidden";
      };
      const actions = Array.from(
        document.querySelectorAll('button, a[href], input, textarea, select, [role="button"], [tabindex]')
      )
        .filter(visible)
        .slice(0, 150)
        .map((el, i) => {
          const r = el.getBoundingClientRect();
          return {
            action_id: `a${i + 1}`,
            tag: el.tagName.toLowerCase(),
            role: el.getAttribute("role"),
            type: el.getAttribute("type"),
            text: (el.innerText || el.getAttribute("aria-label") || el.getAttribute("title") || "").trim().slice(0, 160),
            href: el.getAttribute("href"),
            id: el.id || null,
            classes: typeof el.className === "string" ? el.className : null,
            selector: el.id ? `#${el.id}` : null,
            rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
          };
        });
      return {
        url: location.href,
        title: document.title,
        inner_text: (document.body?.innerText || "").slice(0, 40000),
        actions,
      };
    })();
    """
)
```

3. Select the action using both semantics (`inner_text`) and grounding (`actions`).

4. Execute with actionability checks and pointer/mouse events (not only `el.click()`).

5. Verify outcome with at least two independent signals (URL/hash, title/header, target content presence).

## Workflow

### 1. Resolve The Target Context

1. Resolve the target tab by URL fragment first.
2. Fall back to title contains when URL is unstable.
3. Record baseline state (`url`, `title`, optional page marker text) before acting.

### 2. Build An LLM-Ready Snapshot

1. Prefer `document.body.innerText` for semantic understanding.
2. Add a compact actionable element list for execution grounding.
3. Keep payload size bounded:
- Cap `inner_text` length.
- Cap action count (for example 100-200 visible actions).
- Trim action text to short snippets.
4. Exclude non-actionable noise:
- Avoid full raw HTML by default.
- Avoid scripts/styles/meta unless troubleshooting rendering bugs.

### 3. Choose The Target Element Robustly

1. Match by intent first:
- text/name/aria-label
- semantic role (`button`, link, input)
- nearby context (section name, panel title)
2. Disambiguate duplicates with geometry:
- prefer visible
- prefer in viewport
- prefer larger clickable parent anchors/buttons over nested labels
3. Reject unsafe candidates:
- zero-size nodes
- hidden nodes
- disabled controls
- nodes outside active scroll container viewport

### 4. Execute Action Using Realistic Event Path

1. Scroll candidate into view before interaction.
2. Compute center point and resolve `document.elementFromPoint`.
3. Dispatch event sequence on top element:
- `pointerdown`
- `mousedown`
- `pointerup`
- `mouseup`
- `click`
4. Use direct `el.click()` only as a fallback.
5. Prefer container-aware scrolling (`list.scrollBy`) over `window.scrollBy` on virtualized lists.

### 5. Verify, Retry, Diagnose

1. Verify expected state change immediately after action.
2. Sleep briefly (`0.5-1.5s`) for SPA route transitions, then re-check.
3. Retry with improved targeting if verification fails.
4. Emit diagnostics before retry:
- chosen selector/text
- visibility and bounding rect
- top hit-test element at click point
- resulting URL/title/hash

## Snapshot Contract

Use this JSON shape when preparing context for an LLM planner:

```json
{
  "snapshot_version": "1.0",
  "page": {
    "url": "https://example.com/path",
    "title": "Page Title",
    "captured_at": "2026-03-02T20:15:00+03:00",
    "viewport": {"width": 1512, "height": 982}
  },
  "inner_text": "Human-visible text only...",
  "actions": [
    {
      "action_id": "a1",
      "kind": "click",
      "tag": "button",
      "role": null,
      "name": "Open menu",
      "selector": "#menu-button",
      "href": null,
      "rect": {"x": 13, "y": 7, "w": 40, "h": 40},
      "visible": true
    }
  ]
}
```

Use this command contract for the planner output:

```json
{
  "do": "click",
  "action_id": "a1",
  "reason": "Open navigation menu before selecting Pull requests"
}
```

## Reusable Execution Snippets

### Safe Click By Selector

```python
result = tab.execute(
    """
    ((selector) => {
      const el = document.querySelector(selector);
      if (!el) return {ok: false, reason: "not_found", selector};

      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      if (!r.width || !r.height || s.display === "none" || s.visibility === "hidden") {
        return {ok: false, reason: "not_actionable", selector};
      }

      el.scrollIntoView({block: "center"});
      const rr = el.getBoundingClientRect();
      const cx = rr.left + rr.width / 2;
      const cy = rr.top + rr.height / 2;
      const top = document.elementFromPoint(cx, cy) || el;

      const fire = (node, type) =>
        node.dispatchEvent(new MouseEvent(type, {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: cx,
          clientY: cy,
          button: 0
        }));

      fire(top, "pointerdown");
      fire(top, "mousedown");
      fire(top, "pointerup");
      fire(top, "mouseup");
      fire(top, "click");

      return {
        ok: true,
        selector,
        clicked_tag: top.tagName.toLowerCase(),
        clicked_class: top.className || ""
      };
    })("#menu-button");
    """
)
```

### Verify Navigation

```python
verify = tab.execute(
    """
    (() => ({
      href: location.href,
      hash: location.hash,
      title: document.title,
      h1: document.querySelector("h1")?.innerText || ""
    }))();
    """
)
```

Require expected checks such as:
1. URL path/hash changed as intended.
2. Title or header contains target entity.
3. Target panel/list element exists.

## Troubleshooting Playbook

### Symptom: Click Returns Success But Nothing Changes

1. Check if only `el.click()` was used.
2. Re-run with pointer/mouse dispatch sequence.
3. Check if hit-test top element is overlay/ripple wrapper.
4. Click the top hit-test element instead of raw anchor node.

### Symptom: Correct Text Matched But Wrong Element Clicked

1. Check for virtualized duplicates in DOM.
2. Filter to visible + in-viewport candidates.
3. Scroll candidate into center and re-resolve hit-test target.
4. Select nearest clickable ancestor (`a`, `button`, `[role="button"]`).

### Symptom: SPA Route Did Not Update

1. Check route state (`location.href`, `location.hash`) before and after.
2. Trigger action from active list context (for example set the right tab/filter first).
3. Add small wait and poll for transition completion.

### Symptom: Selector Is Too Fragile

1. Prefer stable anchors in this order:
- `id`
- semantic attributes (`role`, `aria-label`, `name`, `type`)
- URL fragment (`href`)
- constrained text plus parent role
2. Avoid deep CSS chains with generated class names.

## Example Workflow: Open GitHub Pull Requests

Goal: open pull requests tab and extract open PR titles for a repository.

1. Resolve repo tab:
```python
tab = chrome.tabs.get(url__contains="github.com/OWNER/REPO")
```

2. Build snapshot and locate "Pull requests" action.

3. Execute click on the actionable element matching:
- text contains `Pull requests`
- tag is `a` or role button

4. Verify:
- URL contains `/pulls`
- page title contains `Pull requests`

5. Extract rows:
```python
prs = tab.execute(
    """
    (() => {
      return Array.from(document.querySelectorAll('[data-testid="issue-row"], .js-issue-row'))
        .map((row) => {
          const a = row.querySelector('a[id^="issue_"], a.Link--primary');
          return {
            title: a?.innerText?.trim() || "",
            href: a?.href || "",
            number: row.querySelector('[id^="issue_"]')?.id?.replace("issue_", "") || ""
          };
        })
        .filter((x) => x.title);
    })();
    """
)
```

6. Report a concise result plus verification evidence.

## Reporting Template

Use this user-facing report structure after multi-step automation:

1. Baseline:
- starting URL/title
2. Action:
- what was clicked/typed/scrolled
- candidate metadata (`selector`, `text`, `rect`)
3. Verification:
- resulting URL/title/hash
- target marker found or not
4. Output:
- extracted data, if requested
5. Recovery:
- retries performed and why

## Guardrails

1. Never claim success without verification.
2. Never use a single signal for verification on critical actions.
3. Never rely only on raw HTML for planning.
4. Prefer deterministic extraction and explicit result objects from JS.
5. Persist intermediate evidence when debugging flaky pages (snapshot JSON, body HTML, action logs).

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources (optional)

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**
