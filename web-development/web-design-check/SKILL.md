---
name: web-design-check
description: "Use when checking a web page's design or a11y."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [design, audit, accessibility, wcag, contrast, layout, playwright, qa, responsive]
    related_skills: [dogfood, landing-page-copy, web-panel-on-existing-vps]
---

# Web Design Check

Measure a live web page's visual and accessibility defects with numbers instead
of opinions. Contrast ratios, tap-target sizes, overflow, clipping, broken
requests — each finding carries the measured value, so it is arguable.

This checks **mechanics, not taste**. It cannot tell you the design is ugly or
the hierarchy is wrong. It tells you where the page breaks its own rules.

## When to Use

- A client page or panel is ready and needs a pre-ship visual/a11y pass.
- A user says "на телефоне всё разъезжается", "контраста не хватает", "кнопку не видно".
- Comparing a before/after design change.

Don't use for: functional QA (broken flows, dead buttons) — that is `dogfood`.
Nor for judging composition or copy — no script does that.

## Prerequisites

Discover the actual Python environment and browser installation before each live audit. Do not hardcode a Hermes generation, venv or Chromium build: upgrades and Playwright installs can replace them. A working browser tool does not prove the terminal's Python imports Playwright.

Check the candidate interpreter first:

```bash
python -c "import sys, importlib.util; print(sys.executable); print(importlib.util.find_spec('playwright'))"
```

If the module is missing, select an existing verified helper environment or prepare an isolated environment only within an authorized setup/live-audit task. Do not modify Hermes's selected environment with raw pip. Confirm the selected Playwright installation has its compatible browser before launching the audit.

## How to Run

Set `AUDIT_PY` to the verified interpreter, `SKILL_DIR` to this skill's actual directory and `TARGET_URL` to the requested page. Use Hermes scratch through `TMPDIR`, not the system temporary directory.

```bash
"$AUDIT_PY" "$SKILL_DIR/scripts/design_audit.py" "$TARGET_URL" --out "$TMPDIR/design-audit"
```

Flags: `--widths 375,768,1440` (default), `--target-min 24` (24 = WCAG AA 2.5.8,
44 = AAA 2.5.5).

Outputs into `--out`: `audit.json` (machine-readable), `report.md` (readable,
Russian), `screenshots/viewport-<W>.png`.

## What it measures

| Check | Method | Bar |
|---|---|---|
| Text contrast | WCAG relative-luminance ratio on each text node | AA: 4.5:1, or 3:1 if ≥24px / ≥18.66px bold |
| Tap-target size | `getBoundingClientRect` of interactive elements | 24×24 AA (2.5.8); 44×44 AAA (2.5.5) |
| Horizontal overflow | `scrollWidth > clientWidth`, elements past the viewport | none |
| Clipped text | hidden overflow with `scrollWidth > clientWidth` and no ellipsis | none |
| Images without `alt` | attribute presence | all labelled |
| Form controls without label | `label[for]`, wrapping `label`, `aria-label`, `aria-labelledby` | all labelled |
| Console errors | `console` event, type `error` | none |
| Failed requests | `requestfailed` + responses ≥ 400 | none |

## Procedure

1. **Run the audit on the deployed URL**, not a local file, whenever the page is
   live — rendering differs from `file://` (fonts, fetch, mixed content).
2. **Read `report.md`**, then open the screenshots to confirm the high-severity
   findings visually before reporting them.
3. **Re-check anything the report calls unmeasurable.** Gradient text and text
   over images are skipped by design (see Pitfalls) — those need your eyes.
4. **Separate mechanical from judgement.** Report contrast/overflow/clipping as
   measured facts; say plainly that composition and copy were not assessed.
5. **Hand fixes as specific values**, not advice: «`a.cta`: 3.16:1 → нужно
   4.5:1, затемнить фон до #4a7ae0» beats «улучшить контраст кнопки».

## Pitfalls

- **Transparent text is not low contrast.** Text using `background-clip: text`
  over a gradient has `color: rgba(0,0,0,0)`; a naive ratio reports ~1:1 and is
  wrong. The script skips these and lists them as unmeasurable.
- **Alpha backgrounds must be composited.** A chip with
  `background: rgba(91,140,255,0.15)` over a dark card needs the whole ancestor
  stack flattened bottom-up; taking only the first non-transparent ancestor
  reports a false 1:1. The script composites the stack.
- **Do not default the tap-target bar to 44px.** 44×44 is AAA (2.5.5). AA
  (2.5.8) is 24×24. Using 44 as the default flags most real sites and buries
  the true findings.
- **Inline links in a text block are exempt from target size** (WCAG 2.5.8).
  The script moves them to a separate `inlineLinksExempt` list; do not report
  them as defects.
- **Exclude intentional screen-reader-only clipping from visible-text defects.** A `legend.sr-only` with a one-pixel box and clip-path is often the form's accessible name, not broken layout. Verify the accessible name remains present; do not remove the legend or unhide it merely to make the audit green.
- **A clean report is not a good design.** Zero findings only means no measured
  rule was broken.
- **`file://` skews results.** Fetch, CORS and font behaviour differ from a real
  origin; use it only for a quick local fixture, never for a client verdict.

## Verification

Before reporting an audit as done:

- [ ] `audit.json`, `report.md` and ≥1 screenshot per viewport exist on disk.
- [ ] Every high-severity finding was visually confirmed in a screenshot.
- [ ] Findings the script listed as unmeasurable were inspected by eye or
      explicitly reported as not assessed.
- [ ] The report states what was **not** checked (taste, hierarchy, copy).
- [ ] Each reported defect carries a measured number, not an adjective.
