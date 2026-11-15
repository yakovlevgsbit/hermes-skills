# Style Families — Swiss, Editorial, Brutalist

Condensed from [AkyRayy/Frontend-Design-SKILLS-for-AI](https://github.com/AkyRayy/Frontend-Design-SKILLS-for-AI)
(MIT, commit `85d8633`), files `aesthetics.md` §3–4, `editorial-patterns.md`,
`brutalist-patterns.md`. Text rewritten and shortened; original wording, numbers and
references preserved where they were specific. Not affiliated with the upstream author.

Read this when the brief is not SaaS/product chrome. For Linear/Stripe/Vercel
minimal, use `popular-web-designs` templates instead — that vocabulary already
exists locally and this file would only duplicate it.

## How to use

1. Name one family out loud before writing code. Two families on one page is the failure mode.
2. Take its palette, type pair and layout rules as a system, not as decoration.
3. If a section argues with the family (a centred CTA row inside a Swiss grid), delete the section, do not soften the family.

| Family | Fits | Default pick |
|---|---|---|
| Swiss / International Typographic | galleries, museums, archives, studios, manifestos, annual reports | when information is the design |
| Editorial / Magazine | publishing, journalism, premium brands, agency sites | Pentagram archive when unsure |
| Brutalist / Raw | music, fashion, streetwear, art, counterculture, edgy tech | Working Format when unsure |

---

## Swiss / International Typographic

Reference: Müller-Brockmann, Vignelli, Pentagram archive, Bureau Mirko Borsche,
Studio Dumbar, Werkplaats Typografie, MoMA catalogues.

**Vibe:** the grid is the design. Information architecture is visual architecture.

**Type**

- One neutral grotesque used ruthlessly: Helvetica Now, Söhne, Neue Haas Grotesk, GT America, Inter, ABC Diatype.
- Mono only for tabular data, captions, indices — IBM Plex Mono or the same family's mono.
- Hero is **smaller than an agent wants it to be**: `clamp(2.5rem, 5vw, 4.5rem)`. Big headline here reads as shouting, not confidence.
- Numerals, dates and indices set large as visual anchors.

**Color**

```
--surface: #FFFFFF   /* or #000000 — nothing in between */
--ink:     #000000   /* pure, not a grey */
--accent:  red / fluorescent / electric blue, ONE punctuation mark
           /* no accent at all is a valid Swiss choice */
```

**Layout**

- Strict modular grid: 12 or 6 columns, visible or not.
- Left-aligned everything. Centring is a decision that Swiss does not make.
- Numbered sections, folio numbers, indices; metadata shown (dates, places, dimensions, edition).
- Tables and diagrams treated as typography, never as decoration.

**Signatures:** captions and labels are part of the design (small, often mono);
density high, whitespace as separator rather than filler; manifesto text set large;
photography documentary and full-bleed.

**Kills:** decorative elements, a second typeface, centred headlines, friendly rounded corners.

---

## Editorial / Magazine

### Pentagram archive (default)

Reference: pentagram.com archive work. Serif display + sans body, asymmetric grids,
real photography, restrained colour.

```
--surface:         #FFFFFF
--surface-1:       #FAFAFA
--ink:             #1A1A1A
--ink-muted:       #6B6B6B
--ink-subtle:      #A0A0A0
--hairline:        #E5E5E5
--hairline-strong: #C7C7C7
--accent:          often red #C8281C, often nothing
```

- Type: GT Super / Tiempos / Instrument Serif for display, Söhne / Inter for body.
- Hero: `clamp(4rem, 9vw, 9rem)`, tracking −0.03…−0.05em, line-height 1.0–1.1; body 1.55–1.65.
- Layout: strong vertical rhythm, generous gutters, asymmetric splits, image bleeding off one edge, text column offset; hairlines only where they organise information.
- Signatures: section markers as design («§ 01 — On the work»), captions in italic with credit, a colophon page, long considered scroll.
- Kills: 3-card rows, gradient backgrounds, stock photography, centred hero with two CTAs, «trusted by» logo bar, rainbow palettes.

### Bloomberg Businessweek

Dense, opinionated, graphic. Mixed sans/serif, flat saturated blocks, bright accent as
punctuation, magazine spreads, no fear of density. Use when the brief wants loud and
editorial at once; the early-2010s covers are the closest thing to editorial-brutalist.

Other directions worth naming before you build: NYT Magazine (serif throughout, calm,
black and white), It's Nice That (contemporary, bright, mixed sans), Apartamento (warm,
intimate, sans display + serif body), The Gentlewoman (portrait-led, near monochrome).

---

## Brutalist / Raw

Reference: Bandcamp, Working Format, early Bloomberg BW covers, Slam Jam, SSENSE
editorial, Brutalist Websites gallery.

> **Brutalism is a choice, not a lack of effort.**

True brutalism has strong type decisions (louder, not quieter), considered asymmetry
(deliberately off, not careless), one or two moments of polish inside the rawness,
loud-and-quiet alternation, and is self-aware. False brutalism is default system fonts,
random colours, sloppiness where sloppiness is not the point, noise throughout, and
inaccessibility by design.

**Pick the cousin**

| Sub-style | Mood | Type | Colour | Audience |
|---|---|---|---|---|
| Bandcamp | functional raw, archive-first | sans + mono | monochrome + album art | music, indie labels |
| Working Format | considered raw, editorial-influenced | sans display, restrained | B/W + bold accent | music industry, fashion editorial |
| Bloomberg BW covers 2010–2015 | loud, dense, graphic | mixed sans/serif/mono | flat saturated blocks | news, design-literate |
| Brutalist Websites gallery | pure HTML aesthetic, geometric | often default system | often none | design history, art students |
| Slam Jam | loud typography, mixed media | condensed display | black + one accent | streetwear, art |

**Bandcamp as a concrete baseline**

```
--surface: #FFFFFF (or #1A1A1A)
--ink: #1A1A1A
--hairline: #E5E5E5 / --hairline-strong: #C7C7C7
--accent: #629AA9 (used on tags, links, active states only)
```

- Type: Avant Garde / Inter / Söhne for headings; Verdana-class or Source Sans for body; IBM Plex Mono for metadata. Hero `clamp(2rem, 4vw, 3rem)` — calm, not dramatic. Tracking 0 or −0.01em, body line-height 1.4.
- Layout: dense archive-first lists, hairlines separating rows, metadata fully visible (track count, runtime, date, label, tags), album art as the anchor of each item.
- Signatures: persistent player as a design element, semantic tag colours, hierarchy through size rather than weight.
- Kills: gradients, heavy drop shadows, decorative illustration, 3-card feature rows, centring everything.

---

## Cross-family check before shipping

- One accent, used on ≤10% of pixels (≤5% for editorial).
- Headline size is a decision, not a browser default: 36–48px hero means the template won, push it.
- Two typefaces maximum, three weights maximum.
- Every section has states: hover, focus-visible, active, disabled, empty, error.
- 390 / 768 / 1440 px checked with no horizontal scroll.
