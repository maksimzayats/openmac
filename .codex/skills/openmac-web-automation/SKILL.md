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

When automation is multi-step, avoid recreating or reopening the tab in each loop. Resolve once, then re-validate:

```python
def resolve_target_tab(chrome, *, url_fragment: str, title_contains: str | None = None):
    exact = [t for t in chrome.tabs.all if url_fragment in t.url]
    if exact:
        return exact[0]

    if title_contains:
        by_title = [t for t in chrome.tabs.all if title_contains in t.title]
        if by_title:
            return by_title[0]
    return None

tab = resolve_target_tab(
    chrome,
    url_fragment="web.telegram.org/a/#<chat-topic-fragment-or-url-substring>",
    title_contains="<exact topic title or stable substring>",
)
if not tab:
    raise RuntimeError("Target tab not found")
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

### 1a. Must-pass state lock before/after every action

Before and after each non-trivial action, verify all three signals:

1. Tab identity is stable:
- `tab.id` exists and does not unexpectedly change.
2. Route identity is locked:
- `location.href` contains the expected URL fragment.
3. Content container identity is stable:
- target container (`.MessageList` or app-specific equivalent) exists and remains the same object.

If any signal drops:
- stop the current loop immediately,
- re-resolve tab from `tabs.all` using URL fragment + title,
- re-open target via topic/topic-anchor click if needed,
- re-run baseline snapshot before continuing.

Avoid `tabs.get_or_open`/`tabs.open` for already-existing tabs; repeated focus switches can induce state churn.

## Workflow

### 1. Resolve The Target Context

1. Resolve the target tab by URL fragment first.
2. Fall back to title contains when URL is unstable.
3. Record baseline state (`url`, `title`, optional page marker text) before acting.
4. Confirm manager/object API shape before scripting loops (for example property vs method calls on managers).
5. If `tabs.get(url__contains=...)` fails or returns unexpected chat:
- rebuild candidates from `tabs.all`,
- match by both URL fragment and title text,
- and only proceed after container verification.

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
5. Use bounded retries (3–6 attempts); on repeated failure, stop with explicit failure evidence and request escalation.

### 6. Dynamic Timeline/Feed Protocol

Use this when the target is a live list, timeline, or chat-like surface with virtualized rendering.

1. Find the active scroll container first (do not assume `window` scroll):
- select the largest visible element with `overflow-y: auto|scroll` and `scrollHeight > clientHeight`
- scope this search to the active content column/panel
2. If there is a jump control (for example unread/latest/bottom), trigger it by accessible label and verify.
3. Verify anchor-to-latest with at least three signals:
- same scroll container is still selected after action
- `scrollTop` is near `maxTop` (`abs(maxTop - scrollTop) <= 3`)
- latest visible items/time markers move forward as expected
4. If verification fails, retry with bounded attempts (3-6), then fallback to `container.scrollTop = container.scrollHeight`.
5. Re-discover the scroll container after each major jump; virtualized UIs may remount and change dimensions.
6. Do not treat any step as `latest` if visible message count is 0.

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

### Find Active Scroll Container

```python
scroll_state = tab.execute(
    """
    (() => {
      const root = document.querySelector("main, #app, body") || document.body;
      const items = Array.from(root.querySelectorAll("*"))
        .filter((el) => {
          const cs = getComputedStyle(el);
          const oy = cs.overflowY;
          return (oy === "auto" || oy === "scroll" || oy === "overlay")
            && el.scrollHeight - el.clientHeight > 20;
        })
        .map((el) => {
          const r = el.getBoundingClientRect();
          return {
            class_name: String(el.className || ""),
            id: String(el.id || ""),
            area: Math.round(r.width * r.height),
            top: Number(el.scrollTop || 0),
            max_top: Number((el.scrollHeight || 0) - (el.clientHeight || 0)),
            client_height: Number(el.clientHeight || 0),
          };
        })
        .sort((a, b) => b.area - a.area);

      return {containers: items.slice(0, 5)};
    })();
    """
)
```

### Click By Accessible Label (Not Fragile CSS)

```python
click = tab.execute(
    """
    ((targetLabel) => {
      const normalize = (s) => (s || "").trim().toLowerCase();
      const btn = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((el) => {
          const label = normalize(
            el.getAttribute("aria-label") || el.innerText || el.getAttribute("title") || ""
          );
          return label === normalize(targetLabel);
        });
      if (!btn) return {ok: false, reason: "not_found", targetLabel};

      const r = btn.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const fire = (type) => btn.dispatchEvent(new MouseEvent(type, {
        bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, button: 0,
      }));
      fire("pointerdown");
      fire("mousedown");
      fire("pointerup");
      fire("mouseup");
      fire("click");
      return {ok: true, targetLabel};
    })("Go to bottom");
    """
)
```

### Real Click Helper (When It Helps)

Your helper is useful as a baseline because it sends real mouse events instead of only `el.click()`:

```javascript
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
```

For flaky SPAs, prefer a hardened variant:
1. `scrollIntoView({block: "center"})` before click.
2. Resolve `top = document.elementFromPoint(x, y) || el`.
3. Dispatch on `top` (not only `el`), and include `pointerup`.

```javascript
function realClickRobust(el) {
  el.scrollIntoView({ block: "center" });
  const rect = el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  const top = document.elementFromPoint(x, y) || el;
  const events = ["pointerdown", "mousedown", "pointerup", "mouseup", "click"];

  for (const type of events) {
    top.dispatchEvent(new MouseEvent(type, {
      view: window,
      bubbles: true,
      cancelable: true,
      clientX: x,
      clientY: y,
      button: 0,
    }));
  }
}
```

## Telegram/Forum Protocol (Learned From Failures)

Use this when automating Telegram Web forum topics.

1. Prefer clicking UI anchors over forcing URL hash:
- Open group via sidebar anchor `a[href="#-100..."]`.
- Open topic via forum topic anchor `a[href="#-100..._<topic_id>"]`.
- Avoid `location.hash = ...` as a primary action; it can land in partial UI state (`title="Telegram"`, no messages rendered).

2. Scope candidate selection to the correct panel:
- Sidebar targets: only from `.chat-list a[href]`.
- Message/thread targets: only from topic list area.
- Reject header/title duplicates outside the intended panel.

3. Scroll container selection:
- Prefer explicit container first (`.MessageList` for Telegram).
- Fallback to largest visible scroll container only if explicit selector is missing.
- Do not hardcode geometry thresholds like `left >= 250`; layouts vary (right panel, narrow mode, remounts).

4. Bottom-anchor verification (must pass before calling a window “latest”):
- Same `.MessageList` instance still present after jump.
- `abs(maxTop - scrollTop) <= 3` on that container.
- Visible messages exist (`.Message` count in viewport > 0).

5. Capture windows protocol:
- Capture `step=0` immediately after verified bottom anchor.
- For each upward step: `scrollBy(-0.8 to -0.9 * clientHeight)` then wait `0.6-1.0s`.
- Store provenance per capture: `step`, `scrollTop`, `maxTop`, `clientHeight`, `hash`, `title`, message ids.
- Deduplicate by stable message id across windows.

6. Unanswered-question detection:
- Start with messages containing `?`.
- Exclude questions that have an obvious direct reply in next messages (quoted/reply context + answer-like body).
- Mark uncertain cases as “likely unanswered” rather than definitive.

## Telegram forum hardening for repeated reliability

1. Always open the topic explicitly by sidebar/topic anchor click when not already on target.
2. Avoid direct `location.hash = ...` as a primary path.
3. Validate all three anchors before window capture:
- URL fragment + topic title,
- `.MessageList` instance continuity,
- bottom state (`abs(maxTop - scrollTop) <= 3`) after “Go to bottom”.
4. Capture provenance on every window:
- `step`, `scrollTop`, `maxTop`, `clientHeight`, `hash`, `title`, `message_ids`.
5. Deduplicate by stable message IDs across windows (`data-message-id`, `message-*`).
6. If any window capture target mismatch is detected, abort and re-lock target before continuing.

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

### Symptom: Wrong topic/chat selected after re-resolution

1. Rebuild candidates from `chrome.tabs.all` and log `(tab.id, url, title)` to find the expected target.
2. Match on both URL fragment and title text before continuing.
3. Re-open target topic via anchor click (not hash rewrite), then re-run state-lock checks.
4. Continue only when:
- correct container is active,
- bottom-anchor verification passes,
- target window capture has visible messages.

### Symptom: openmac loses tab control after `get_or_open`/open

1. On macOS, these flows can fail with System Events permission errors and change app focus unexpectedly.
2. Prefer existing tabs (`chrome.tabs.all` + strict matching) over `get_or_open` for stateful automation.
3. If this occurs, close the attempted operation path, re-acquire with safe scans, and continue with anchor-click navigation.

### Symptom: Jump-To-Latest Clicked But Position Is Still Wrong

1. Verify you clicked the exact control by accessible label (not overlapping icon child).
2. Re-discover the scroll container; virtualized views may swap container instances.
3. Compare `scrollTop` to `maxTop` on the same element after each attempt.
4. Retry bounded times, then force `scrollTop = scrollHeight` and verify again.
5. If metrics changed drastically (`maxTop` shrinks/grows), wait and re-snapshot before extraction.

### Symptom: Extracted “Latest” Items Are Actually Older Context

1. Ensure anchor-to-latest was verified immediately before capture.
2. Record capture provenance: `step`, `scrollTop`, `maxTop`, and whether jump control remained visible.
3. Deduplicate by stable message/item id across scroll steps.
4. Only call items “latest window” when `step=0` was captured from verified bottom state.

### Symptom: Selector Is Too Fragile

1. Prefer stable anchors in this order:
- `id`
- semantic attributes (`role`, `aria-label`, `name`, `type`)
- URL fragment (`href`)
- constrained text plus parent role
2. Avoid deep CSS chains with generated class names.

### Symptom: JS Extraction Returns `None`/Missing Value

1. Ensure the JS snippet returns an explicit object (`return {...}`), not `undefined`.
2. If building JS with Python `f"""..."""`, escape literal braces (`{{`/`}}`) or avoid f-strings.
3. Watch for regex quantifiers inside f-strings (for example `{1,2}`) which can be mangled by Python formatting.
4. Prefer a plain triple-quoted string + placeholder replacement for small params.

### Symptom: JSON Serialization Fails With `Keyword`/Non-JSON Types

1. Normalize `tab.execute(...)` output at the Python boundary.
2. Convert unknown/non-primitive values via `str(...)` before `json.dumps`.
3. Persist normalized snapshots only; keep raw objects out of result files.

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
