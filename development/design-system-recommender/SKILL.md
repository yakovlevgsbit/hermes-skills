---
name: design-system-recommender
description: "Use when a project needs a design system."
version: 1.0.0
author: NextLevelBuilder (ui-ux-pro-max, MIT) — engine; Георгий Яковлев (yakovlevgsbit) — Hermes adaptation
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [design-system, ui, ux, palette, typography, landing-page, accessibility, patterns]
    related_skills: [landing-page-copy, web-design-check, popular-web-designs]
---

# Design System Recommender

Given a project description, produce a complete design system: page pattern,
style, colour palette, typography, effects, anti-patterns and a pre-delivery
checklist. Data-backed, not improvised.

Engine and data adapted from
[ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT,
NextLevelBuilder). Stdlib Python only — no dependencies, no network.

## When to Use

- A client asks for a landing page, panel, or app and needs a look before code.
- You need to pick a palette/style and want it grounded rather than guessed.
- The user says «какой стиль для салона красоты / клиники / SaaS».

Don't use for: auditing an existing page (that is `web-design-check`), or
building the HTML itself (`claude-design`, `popular-web-designs`).

## How to Run

```bash
python3 <skill_dir>/scripts/search.py "<query>" --design-system \
  --format markdown -p "<Project Name>"
```

The flag is `--format` (ascii|markdown) — there is no `--output-format`.
`-p` is shorthand for `--project-name`.

Design dials (1-10, optional):

```bash
  --variance 8   # minimal → brutalist
  --motion 9     # static → animated
  --density 7    # spacious → dashboard
```

Other modes:

```bash
# search a single domain
python3 <skill_dir>/scripts/search.py "<query>" --domain product
# domains: product, style, color, typography, landing, ux, chart, icons, motion, react, web, google-fonts

# stack-specific guidance
python3 <skill_dir>/scripts/search.py "<query>" --stack html-tailwind
# stacks: react, nextjs, vue, svelte, astro, swiftui, react-native, flutter,
#         nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs,
#         angular, laravel, avalonia, javafx, uno, uwp, winui, wpf
# NOTE: stack search matches only the Category/Guideline/Do/Don't columns, NOT
# the query text semantically. "landing" -> 0 results; "tailwind animation" -> 1.
# If you get 0, retry with a concrete keyword from the domain (e.g. "animation",
# "form", "responsive", "dark mode") before falling back to general defaults.

# machine-readable (no truncation)
python3 <skill_dir>/scripts/search.py "<query>" --design-system --json
```

## Data available

| Domain | Rows | What it answers |
|---|---|---|
| `products` | 192 | Which pattern/style/palette for a product type |
| `ui-reasoning` | 192 | Industry rules with JSON conditions (`if_bookings` → booking pattern) |
| `styles` | 88 | 79 searchable styles: keywords, palettes, effects, performance, a11y risk |
| `colors` | 192 | Full palettes as tokens (Primary, On Primary, Card, Muted, Ring…) |
| `typography` | 74 | Font pairings with mood, Google Fonts URL, Tailwind config |
| `landing` | 34 | Page patterns with section order and CTA placement |
| `charts` | 25 | Chart type per data type, with a11y grade and fallback |
| `motion` | 17 | Animation patterns with intensity tier and GSAP snippet |
| `ux-guidelines` | 118 | Do/Don't with code examples and severity |
| `stacks` | 22 files | Per-framework conventions |

## What the output contains

Pattern + conversion focus, style with mode support and performance/a11y notes,
colours as CSS variables, typography, key effects, **anti-patterns to avoid**,
and a pre-delivery checklist (contrast ≥4.5:1, focus states, reduced motion,
responsive at 375/768/1024/1440).

## Procedure

1. **Ask what the user cannot be guessed from.** Industry, platform (web/mobile/
   desktop), dark or light, and whether there is an existing brand palette. A
   wrong industry is a wrong design system — «booking» matches a spa and a hotel
   differently.
2. **Run the engine** with the project description. Pass `--variance/--motion/
   --density` when the user has a preference.
3. **Read the anti-patterns section** and remove anything that contradicts the
   user's brand (the engine's «avoid» list is generic; the client's brand is not).
4. **Hand over as a file**, not chat prose — the client needs something they can
   pass to a developer. Persist with `--persist --output-dir <project-root>`.
5. **Verify the colours** with the `web-design-check` skill once built, because
   the engine recommends, it does not measure.

## Pitfalls

- **The engine recommends; it does not verify.** Its palettes are hand-curated
  from common practice, not measured contrast ratios. Run `web-design-check` on
  the result before shipping.
- **Industry match is the highest-leverage input.** A vague query
  («dashboard») lands on a generic SaaS rule; «medical clinic dashboard» gets a
  materially different palette and pattern. Always ask for the industry.
- **Dark mode needs an explicit request or a dark-first style.** Otherwise the
  engine resolves light mode. Pass «dark mode» in the query when the user wants it.
- **Truncated human output.** Long code samples are cut at 300 chars unless they
  are in `UNTRUNCATED_COLS`. Use `--json` when you need the full snippet.
- **`--persist` never overwrites** an existing `MASTER.md` without `--force`, so
  prior design decisions survive. Pass `--force` deliberately.
- **Client-visible text still needs a human pass.** The output is English; UI
  copy in Russian is your job (see `landing-page-copy`).

## Verification

- [ ] `search.py` ran without error and returned non-empty output.
- [ ] The palette's `Background`/`Foreground` contrast was checked with
      `web-design-check` or the engine's own numbers before handover.
- [ ] Anti-patterns that clash with the user's brand were removed.
- [ ] Output persisted to a file the user can hand to a developer.
- [ ] Any claim about accessibility (WCAG grade) was verified, not copied.

## Attribution

Engine, data and reasoning rules: MIT, NextLevelBuilder.
Adaptation (Hermes SKILL.md, integration with `web-design-check`):
Георгий Яковлев (yakovlevgsbit). Original project: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
