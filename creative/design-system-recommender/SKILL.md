---
name: design-system-recommender
description: "Use when generating a design system from a project brief."
version: 1.0.0
author: NextLevelBuilder (nextlevelbuilder) — adapted for Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [design, design-system, ui, ux, typography, colors, reasoning, industry]
    related_skills: [landing-page-copy, web-design-check, popular-web-designs]
---

# Design System Recommender

Generate a complete design system from a project brief: pattern, style, color
palette, typography, effects, anti-patterns, and a pre-delivery checklist.
Adapted from UI UX Pro Max by NextLevelBuilder (MIT); the Python engine is
unchanged, the CLI wrapper was removed.

## When to Use

- A client asks for a landing page, dashboard, or web app and you need a
  design direction before writing code.
- The user says "сделай красиво", "нужен дизайн", "какой стиль выбрать".
- You want an industry-informed palette / typography / pattern without
  hand-picking from scratch.
- You are about to start a new project and need a structured brief for the
  designer subagent.

Don't use for: auditing an existing design (use `web-design-check`), writing
copy (use `landing-page-copy`), or producing pixel-perfect mockups (use
`popular-web-designs` + `claude-design`).

## What it contains

| Domain | Rows | What it gives you |
|---|---|---|
| `products.csv` | 192 | Industry → recommended pattern + style + palette focus |
| `ui-reasoning.csv` | 192 | Industry → JSON decision rules (if_booking, if_data_heavy, …) |
| `styles.csv` | 89 | UI styles: colors, effects, a11y risk, CSS keywords |
| `colors.csv` | 193 | Full semantic palettes (Primary, On Primary, Accent, …) |
| `typography.csv` | 75 | Font pairings with Google Fonts URLs + Tailwind config |
| `landing.csv` | 34 | Landing page patterns with section order + CTA placement |
| `charts.csv` | 25 | Chart types per data shape + a11y guidance |
| `motion.csv` | 18 | GSAP snippets with intensity tiers |
| `ux-guidelines.csv` | 119 | Do/Don't with code examples, severity-rated |
| `icons.csv` | — | Icon library mapping (Phosphor, Heroicons, Lucide) |
| `app-interface.csv` | 33 | App-level UI patterns |
| `google-fonts.csv` | — | Google Fonts metadata with licenses |
| `stacks/` | 22 | Per-stack guidance (React, Vue, Svelte, SwiftUI, Flutter, …) |

The engine is stdlib-only Python. No dependencies, no network calls, no API.

## How to Use

The engine lives in `scripts/`. Call it from a terminal:

```python
import sys, json
sys.path.insert(0, "<skill_dir>/scripts")
from design_system import generate_design_system

result = generate_design_system(
    query="beauty salon booking landing page",
    project_name="Serenity Spa",
    output_format="markdown",
    # optional design dials (1-10):
    variance=5,   # 1=minimal, 10=bold
    motion=3,     # 1=subtle, 10=complex
    density=4,    # 1=spacious, 10=dense
)
print(result["text"])
# raw dict also available: result["design_system"]
```

### Query tips

- **Be specific**: "crypto trading dashboard dark" beats "dashboard".
- **Mention the industry**: it drives `products.csv` + `ui-reasoning.csv`.
- **Mention the platform**: "iOS app" vs "web" changes `stacks/` guidance.
- **Mention constraints**: "accessibility-first", "elderly users", "low-end devices".

### Design dials

Three optional 1-10 sliders that bias the search instead of replacing it:

| Dial | 1 | 5 | 10 |
|---|---|---|---|
| `variance` | Minimal / centered / grid | Balanced / modern | Bold / asymmetric / experimental |
| `motion` | Subtle hover only | Standard transitions | Complex GSAP + parallax |
| `density` | Spacious (24px spacing) | Standard (16px) | Dense dashboard (8px) |

### Output formats

- `"markdown"` (default) — structured, readable, good for pasting into a brief.
- `"ascii"` — box-drawn terminal output, good for quick previews.

### Persistence (optional)

```python
result = generate_design_system(
    query="...", project_name="...",
    persist=True, output_dir="/path/to/project", force=True,
)
# writes design-system/<slug>/MASTER.md
# with --force it overwrites; without it, existing files are preserved
```

## Reasoning rules

The most valuable part: `ui-reasoning.csv` maps 192 industries to JSON decision
rules. Examples:

```
SaaS (General)     → if_ux_focused: style:minimalism, if_data_heavy: style:glassmorphism
Beauty/Spa         → if_booking: pattern:booking, if_luxury: style:soft-ui-evolution
Crypto/DeFi        → if_trust_needed: style:trust-blue, anti:bright-neon
Medical Clinic     → if_health: style:clean-trust, anti:dark-mode
```

These rules are applied by `reasoning_contract.py` — a closed grammar that
parses condition→action pairs and rejects malformed rules. You can read the
raw CSV to understand *why* a recommendation was made.

## Procedure

1. **Get the brief.** What is it? Who is it for? What platform? Any constraints?
2. **Generate the design system.** Run `generate_design_system` with the query.
3. **Review the raw dict.** `result["design_system"]` has structured fields —
   use them to build a component spec, not just a color dump.
4. **Cross-check with `web-design-check`** if you are building a real page:
   the recommender gives you the *intent*, the checker verifies the *output*.
5. **Hand off to `landing-page-copy`** if the page needs copy, or to
   `claude-design` / `popular-web-designs` if you need HTML.

## Pitfalls

- **The engine is a recommender, not a designer.** It gives you a structured
  starting point. You still need to exercise taste.
- **Do not blindly apply anti-patterns.** They are heuristics per industry;
  your client's brand may override them.
- **The CSV data has a freshness SLA.** `data-provenance.json` tracks when
  each row was last verified. Fonts and icons move fast — check
  `google-font-licenses.json` if you are using a font commercially.
- **Dark mode resolution is conservative.** It defaults to light unless the
  query explicitly asks for dark or the style is dark-first. Verify with
  `_resolve_color_mode()` if the output looks wrong.
- **No tests for the engine.** `validate_data.py` checks data integrity, but
  `core.py` and `design_system.py` have no unit tests. If you modify the
  engine, test it manually on a known query.
- **The `stacks/` directory has 22 files.** Not all are relevant to your
  project. Filter by what you actually use.

## Native-site asset handoffs

For licensed stock photography, native-block composition, and honest demo/form
states, follow `references/verified-stock-handoff.md`. Keep source verification
separate from visual review and from browser/delivery QA.

## Verification

- [ ] `generate_design_system()` returns a non-empty `design_system` dict.
- [ ] Every color in the palette has a valid hex value.
- [ ] The anti-patterns list is non-empty (a red flag if it is empty for a
      real industry).
- [ ] The typography section includes both a heading and a body font.
- [ ] If you used `persist=True`, the file was written to the expected path.
