# Design Calibration — what "generated" looks like right now

Source: Anthropic, `skills/frontend-design/SKILL.md`
(https://github.com/anthropics/skills, Apache-2.0, commit `2c5958e`). Text adapted:
condensed, restructured for this skill, examples kept. Not affiliated with Anthropic.

Read this **before** committing to a visual direction, not after. The anti-slop
catalog tells you what to avoid in the abstract; this file tells you what the
current default output actually converges to, so you can notice when your "choice"
is just the model's habit wearing a colour.

## Current clusters

AI-generated design right now clusters around five looks. Each is legitimate for
some briefs — the problem is that they appear regardless of subject.

1. **Warm cream + serif + terracotta.** Background near `#F4F1EA`, high-contrast
   serif display, accent in warm clay near `#D97757`. That accent is close to
   Claude's own interface colour, so on a client brief it reads as a tell.
2. **Near-black + one acid accent.** Dark surface, single bright acid-green or
   vermilion accent, everything else mute.
3. **Broadsheet.** Hairline rules, zero border-radius, dense newspaper columns,
   small caps labels.
4. **The SaaS card kit.** Content chopped into identical rounded cards, one radius
   on everything regardless of hierarchy, the same soft grey shadow
   `rgba(0,0,0,.1)` under each, gradient washes as decoration.
5. **Template chrome that appears whatever the subject.** A tracked-out ALL-CAPS
   eyebrow label above every heading; meta strings joined with middle dots
   («A · B · C»); labels built as «WORD — fragment» with a spaced em dash; tinted
   near-black (`#0B0B0B`, `#111`) standing in for black; monospace for small data
   labels; a «→» appended to link and button text.

Where the brief pins a direction, follow the brief exactly — including when it asks
for one of these five. Where the brief leaves an axis free, do not spend that
freedom on a default.

## Typographic tells

Three treatments read as generated more than any colour choice:

- accenting a single word of a headline (one italic word, one coloured word);
- all-caps used for labels;
- decorative labels stacked above content that does not need a category name.

Also: one family or two — and if two, clearly distinct. Set a type scale from
*The Elements of Typographic Style* with intentional weights and widths. Line
length under 80 characters; serif body gets slightly more line-height than sans.

## Structure is information

Outlines, borders, numbering, eyebrows, dividers and labels must encode something
true about the content, not decorate it. Numbered markers (`01 / 02 / 03`) are
only correct when the content really is a sequence — a process, a timeline, a
ranked list. Check before numbering.

## Motion

Non-user-triggered motion: one orchestrated moment (a load sequence, a single
reveal), not scattered effects. Fade-and-slide-up on every section and hover
scale on every card is the generic default. Motion answering a user action
(opening, expanding, confirming) is welcome when it shows what changed.

## Two passes, and a critique

1. **Plan first, in writing:** 4–6 named hex values for the base palette; the
   typefaces and their roles; a layout concept as one-sentence prose plus ASCII
   wireframes, including alignment; and the principles that make this page
   particular. Compare two or three layout ideas before choosing.
2. **Review the plan against the brief before writing code.** If part of it is
   the default you would produce for any similar page, change that part and say
   what you changed. Only then build.

While building, watch CSS specificity: a type selector (`.section`) and an element
selector (`.cta`) that fight over padding between sections is the usual source of
mystery gaps.

Then critique: screenshot if the environment allows («a picture is worth 1000
tokens»), and apply the mirror rule — before leaving the house, remove one
accessory.

## Restraint

Spend boldness in one place. One element is the memorable thing; everything around
it stays quiet and disciplined. Cut decoration that does not serve the brief. Build
to a quality floor without announcing it: responsive to mobile, visible keyboard
focus, `prefers-reduced-motion` respected, accessible contrast.

## Copy inside the design

Words exist to make the interface easier to use — they are design content, not
decoration.

- Write from the user's side: «Управление уведомлениями», not «Конфигурация webhook».
- Active voice; a CTA names what happens: «Сохранить изменения», not «Отправить».
  The action keeps its name through the flow — a «Publish» button produces a
  «Published» toast.
- Errors say what happened and how to fix it, in the interface's voice, without
  apologising and without vagueness. An empty screen is an invitation to act.
- Conversational tone: plain verbs, sentence case, no filler. Each written element
  does exactly one job.
