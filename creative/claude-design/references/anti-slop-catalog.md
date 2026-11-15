# Anti-Slop Catalog — patterns, reasons, replacements

Condensed from [AkyRayy/Frontend-Design-SKILLS-for-AI](https://github.com/AkyRayy/Frontend-Design-SKILLS-for-AI)
(MIT, commit `85d8633`), files `anti-patterns.md` and `code-style.md`. Rewritten and
shortened; concrete values kept as published. Not affiliated with the upstream author.

Use when an artifact feels generic and the 10-tell diagnostic in SKILL.md says which
register is wrong, but you need the specific replacement. Every row is
**pattern → why it reads as generated → what to do instead**.

## Visual

| Pattern | Why it reads as slop | Replace with |
|---|---|---|
| `linear-gradient(135deg,#667eea,#764ba2)` hero | the 2022 AI-image default; carries zero information | off-white surface with ink headline set tight and large; or one full-bleed photo with no gradient; or a deliberately designed gradient (single hue, low opacity) |
| Glassmorphism everywhere (`backdrop-filter: blur(20px)`) | signals «AI template», hurts legibility and paint cost | solid surfaces separated by hairlines; one focal glass element at most |
| Emoji as icons (🚀 ✨ ⚡) | render differently per OS, not part of any system | one real icon set (Lucide/Phosphor/Tabler) used with intent, or no icon — type alone can structure a section |
| `border-radius: 9999px` on everything | default rounding applied everywhere = no decisions | radius scale: buttons 6–8px (or 0 Swiss, or pill only for tags), cards 8–12px, inputs 6–8px; define `--radius-sm/md/lg` |
| Gummy shadow stack (3+ soft layers) | everything floats at the same depth = no hierarchy | one precise shadow `0 1px 2px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.04)`, or hairlines; elevated shadow for modals only |
| Centred hero + 2 CTAs + logo bar | the universal default, no composition was chosen | left headline with a product surface or image on the right; deliberate asymmetric split; or an oversized poster-style centred headline that is clearly a decision |
| Aurora / mesh gradient blobs | decorative noise competing with content | nothing — whitespace as background; or one restrained geometric element |
| 3D blob illustrations | generative default, means nothing | real product UI screenshot, real photo, a diagram, or type alone |
| Text shadow on headlines | 2008 Photoshop residue | none; legibility comes from contrast and size |
| Stock «smiling person at laptop» hero | says nothing about this product | its own UI as the hero (strongest for B2B), real team/space photo, or pure typography |

## Structural

| Pattern | Why | Replace with |
|---|---|---|
| SaaS sandwich: hero → logo bar → 3 features → 3 steps → 3 more cards → carousel → 3 pricing columns | the template that every generated landing page reproduces | vary section rhythm: one dominant proof, asymmetric splits (5/7, 3/9), no two consecutive sections with the same structure |
| Identical 3-column feature row repeated down the page | nothing is prioritised, so nothing is read | one primary capability told long, the rest as a compact list or table |
| Middle pricing card highlighted with a glow | decoration standing in for a recommendation | state the recommendation in words («best for teams of 5–20»), keep cards visually equal |
| FAQ of 8 questions all starting «What is…» | generated filler | 3–5 real objections in the customer's phrasing, answered in one or two sentences |
| «Trusted by 10,000+» with invented logos | unverifiable claim, instantly suspicious | name two or three real clients, or drop the band |
| Testimonial carousel with stock headshots | nobody scrolls it; faces are not evidence | one named quote with a role and a specific outcome, inline where it supports a claim |

## Copy

- Verb stacks («empowering, enabling, unlocking, supercharging») and three-adjective taglines («Fast. Simple. Beautiful.») → one concrete claim with a number or a named outcome.
- «Built for the modern [audience]», «Welcome to [Brand] — your one-stop solution», «The future of work is here» → the single job of the page, stated plainly.
- Nouns without a referent («Insights», «Growth», «Platform») → the thing itself.
- Lorem ipsum in disguise (plausible but empty sentences) → real content or an explicit placeholder marker.

## Code

| Pattern | Why | Replace with |
|---|---|---|
| Tailwind utility soup, 14 classes per element, no extraction | unmaintainable, resists design change | tokens + component classes for anything repeated; utilities only as exception |
| Inline `style={{…}}` for values that should be tokens | palette drifts silently | CSS custom properties |
| Raw hex in components | no single source of truth | tokens only; hex lives in `:root` |
| `transition: all` | animates layout you never meant to animate | name the property: `transition: background-color .15s, border-color .15s` |
| Default browser focus rings, or `outline: none` with nothing in its place | keyboard users lose the page | `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }` on every interactive element |
| `<div>` soup where semantics exist | screen readers get no structure | `<article> <section> <nav> <aside> <button>` |
| `font-weight: 700` on every heading | flattens hierarchy and ignores the family | 2–3 weights per page; hierarchy via size and spacing first |
| `transform: scale(1.05)` on every hover | motion without a system | one hover treatment applied consistently |
| Boolean flags that change behaviour: `doThing(x, true, false)` | call site becomes unreadable | separate named functions, or an options object |
| Comments that restate the code («this function does X») | noise | comments explain *why* and the non-obvious constraint |
| Empty `catch {}` and swallowed errors | failures become invisible | catch what you can handle, rethrow or surface the rest; name the failure |
| `any`, `as any`, `@ts-ignore` without justification | the type system is switched off | `unknown` + narrowing; fix the type |
| Magic numbers (`3600`, `0.5`, `100`) | meaning is lost | named constants with units (`timeoutMs`, `pageSize`) |
| Names like `data`, `result`, `item`, `temp`, `processData`, `handleStuff` | nothing is conveyed | what it is in context: `normalizeInvoice`, `activeUsers`, `createdAt` |
| Functions >50 lines, >5 parameters, god files >500 lines | no seam for change or test | split by responsibility; group parameters into an object |
| Dependencies for one function, or a UI library for two components | permanent maintenance cost | write the function; write the components |
| Tests that only assert «does not throw», or mock everything | green suite that proves nothing | test behaviour and boundaries with real inputs |

## The single rule behind all of it

Remove one element. Then another. If the page is better without them, they were slop.
The upstream mantra: «If the design is good, you won't notice the design. If it's bad,
you notice immediately.»
