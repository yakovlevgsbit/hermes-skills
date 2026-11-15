---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: [web-design-check, subagent-library]
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the `browser_exec` tool. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

**Scope:** this finds *functional* bugs — dead buttons, broken forms, JS errors,
wrong navigation. For visual/accessibility mechanics (contrast, tap targets,
overflow) use `web-design-check`, which measures them numerically.

## Prerequisites

- The `browser_exec` tool (a real Chromium driven over CDP). It is the only
  browser tool in this build — there is no `browser_navigate`/`browser_click`
  family, so drive the page with `browser_exec` helpers: `new_tab(url)`,
  `goto_url(url)`, `wait_for_load()`, `page_info()`, `js(expr)`,
  `fill_input(selector, text)`, `click_at_xy(x, y)`, `capture_screenshot()`,
  `cdp('Domain.method', **kw)`.
- A target URL and testing scope from the user.

**Work text-first.** Read the DOM with `js(...)` and `cdp('Accessibility.getFullAXTree')`
rather than screenshotting; screenshots are evidence for the report, not the
primary way to find bugs.

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan, one `browser_exec` call per page that
navigates, waits, reads the DOM and collects console errors together:

```python
# Explore <page> — navigate, read DOM, collect console errors
new_tab("https://example.com/page")
wait_for_load()
info = page_info()

# console errors: CDP Log domain must be enabled before the page loads to catch
# everything; this reads what is buffered plus runtime exceptions.
logs = js("window.__errors__ || []")
exc  = cdp("Runtime.evaluate", expression="1")  # probe: raises if CDP is dead

# full interactive inventory in one call
els = js("""(() => Array.from(document.querySelectorAll('a,button,input,select,textarea'))
  .map((e,i) => ({i, tag:e.tagName, text:(e.textContent||'').trim().slice(0,40),
                  type:e.type||'', name:e.name||'', id:e.id||'',
                  visible: !!(e.offsetWidth||e.offsetHeight)}))
)()""")
print(len(els), "interactive elements")
for e in els:
    print(e)
```

To catch JS errors reliably, install a hook before interacting, then read it:

```python
js("""(() => { window.__errors__ = window.__errors__ || [];
  window.addEventListener('error', e => window.__errors__.push(String(e.message)));
  window.addEventListener('unhandledrejection', e => window.__errors__.push('rejection: '+String(e.reason)));
  return 'hooked'; })()""")
```

Interactive testing is by CSS selector, not by ref:

- Click: `js("document.querySelector('SEL').click()")`
- Fill: `fill_input('SEL', 'test input')`
- Keyboard: `js("document.querySelector('SEL').focus()")` then `cdp('Input.dispatchKeyEvent', type='keyDown', key='Tab')`
- Scroll: `js("window.scrollTo(0, document.body.scrollHeight)")`
- If a selector is not obvious, get click coordinates from the accessibility
  tree: `cdp('Accessibility.getFullAXTree')['nodes']` → filter by role/name in
  Python → `cdp('DOM.getBoxModel', backendNodeId=n)` for the box, then
  `click_at_xy(x, y)`.

After each interaction re-read state with `js(...)` and check `window.__errors__`.

For visual evidence, `capture_screenshot()` and reference the returned path in
the report.

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```python
   path = capture_screenshot()
   ```
   Keep the returned path — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Tools Reference

All through `browser_exec` (Python, helpers pre-imported):

| Helper | Purpose |
|------|---------|
| `new_tab(url)` | Open/navigate (use for the first navigation) |
| `goto_url(url)` | Navigate the current tab |
| `wait_for_load()` | Wait for load after navigation |
| `page_info()` | Summarise current page state |
| `js(expr)` | Evaluate JS; wrap bodies as `(() => {...})()` |
| `fill_input(sel, text)` | Type into an input |
| `click_at_xy(x, y)` | Click viewport coordinates |
| `capture_screenshot()` | Save + return a screenshot path (evidence) |
| `cdp('Domain.method', **kw)` | Raw CDP: accessibility tree, box models, input events |

## Related

Visual/a11y defects (contrast, tap targets, overflow) are measured numerically by
the `web-design-check` skill — use it instead of eyeballing layout issues here.

## Tips

- **Install the error hook before interacting**, then read `window.__errors__` after each step. Silent JS errors are among the most valuable findings.
- **Test with both valid and invalid inputs** — form validation bugs are common.
- **Scroll through long pages** — content below the fold may have rendering issues.
- **Test navigation flows** — click through multi-step processes end-to-end.
- **Check responsive behaviour** by re-running key pages at a narrow viewport (`new_tab` a fresh context width if the helper allows, else note it as untested).
- **Don't forget edge cases**: empty states, very long text, special characters, rapid clicking.
- When reporting screenshots to the user, include `MEDIA:<screenshot_path>` so they can see the evidence inline.
- **One `browser_exec` call per page** — batch navigate + read + interact so progress survives a timeout.
