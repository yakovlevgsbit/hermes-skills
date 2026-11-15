---
name: web-app-change-verification
description: "Use when verifying a web app change shipped correctly."
version: 1.0.0
author: Георгий
license: MIT
metadata:
  hermes:
    tags: [verification, deployment, browser, web-app, qa]
---

# Live Verification of Web App Changes

## When to Use
A change to a live web app (frontend or backend) must be proven working before
reporting success. Distinct from exploratory QA (see `dogfood`): the goal here is
one tight loop — deploy, confirm delivery, exercise the changed path, assert the
result — not a broad hunt for defects.

## The Loop (in order)

1. **Deploy and confirm readiness in a SEPARATE call.** Restart the service, then
   poll `systemctl is-active <svc>` or hit a health endpoint. Never blind-sleep to
   cover a restart, and never report the deploy before the readiness check returns.
2. **Confirm what the SERVER actually delivers.** Fetch the page over HTTP and
   assert your new marker string is in the body:
   ```python
   html = urllib.request.urlopen(url + '?cachebust=1', timeout=20).read().decode()
   assert '<your new marker>' in html
   ```
   If the marker is absent the fix never shipped — stop and fix the deploy. If
   present, the server is ground truth and any remaining disagreement is downstream.
   Also confirm `Cache-Control: no-store` is really being sent on the document.
3. **Build the fixture data the UI needs, through the API.** An empty-state screen
   hides the state under test. Create the prerequisite records first (e.g. arrival
   → issue → return), keep the ids, then exercise the UI. When done, **delete the
   fixture back out** (children before parents) so live data stays clean.
4. **Navigate in a fresh tab with a cache-busting query** (`?v=<anything>`) and
   treat it as a new client. A tab opened before the deploy is not evidence.
5. **Assert on DOM state, not screenshots.** Read the concrete result of the
   interaction:
   ```python
   js("document.querySelector('SEL.selected') !== null")
   js("document.querySelectorAll('.cut-item').length")
   ```
   A screenshot cannot tell you a list rendered 10 items; a count can. Screenshots
   are the user's evidence; `js()` results are yours.
6. **Report only what was verified.** Name each assertion and its real result.
   Separate what you proved from what you left untested.

## Proving a Global (CSS / Design) Change Across All Screens

A single-page app with several `.page` sections applies one stylesheet to every
screen — if the server delivers the new CSS, every screen has it. When the user
reports "page A changed, the rest didn't", prove coverage screen by screen
before accepting browser cache as the cause:

```python
# computed style of a shared element, per screen (showPage first, then read)
getComputedStyle(document.querySelector('.card')).borderRadius   # expect the new value
# and sample the body background pixel instead of trusting a screenshot:
Image.open(shot).convert('RGB').getpixel((5, height // 2))
```

- New computed values on every screen = the CSS shipped; the remaining
  disagreement is cache or per-screen leftovers.
- Then hunt for leftovers that keep the OLD visual language alive even with new
  CSS: emoji inside buttons/labels and inline `style="color:#..."` attributes.
  Emoji render differently per platform and are what make a redesigned screen
  still read as "old" to the user.
- If `capture_screenshot` times out, drive Playwright directly from a scratch
  script instead of retrying the harness — the screenshot path is evidence, not
  a blocker.

## Making a Dark Theme the Only Theme

When the user says "убери переключение тем, пусть всегда будет тёмный" — remove the toggle AND fix
the theme so it does not break the next element that uses a token.

1. **Remove the toggle and its code paths.** HTML button block (search by its class/id, e.g.
   `theme-toggle`), the JS function plus its click handler, the SVG/icon constant, and any
   loader that applies a saved theme (`localStorage` get/set for the theme key). Grep for every
   theme identifier and assert each count is 0 — the check string must cover all storage places
   (a filter that missed `localStorage` reported success on a half-removed feature).
2. **Collapse the `body.dark X { … }` rules into base rules.** Strip the prefix so the dark values
   become the defaults. Do NOT leave the light values above them "winning by cascade" and rely
   on source order — that is a latent bug when someone reorders the stylesheet.
3. **Set the tokens, not the selectors.** Overriding the dark theme selector-by-selector
   (`color: #ffffff` on each rule) does not reach anything that reads a CSS variable. Re-declare
   the variables themselves after the base block:
   ```css
   :root { --bg: #0b0b0b; --text-primary: #ffffff; --text-secondary: #b9b9b9; }
   ```
   A second `:root` wins (same specificity, later source). It must come before first use in
   source order, or the base declaration still wins.
4. **Hunt hardcoded colors that bypass the tokens.** Any rule that still carries a literal color
   stays broken on the dark background even after the tokens are right. Grep the markup/JS for
   `color:#666`, `color:#888`, `background:#fff`, and for `<a>` links relying on the UA default
   (`color: rgb(0,0,238)` reads ~1.7:1 on `#212121`). Inline `style="color:#666"` inside
   JS-built markup is the usual offender — replace with a utility class that references a token.
5. **Audit contrast across every `.page`** — computed styles prove one element; the audit proves
   the whole page. `scripts/contrast_audit.py <url> <page-id>...` walks every text node, composites
   transparent backgrounds against their ancestor stack, and prints anything under 3.0:1. A zero
   result is the gate for "the dark theme did not break anything".

## Driving a Multi-Step Flow in the Browser

Many UI bugs live in the *sequence* (select recipient → select type → select record),
not in any single screen. Grep cannot see a handler that overwrites state mid-flow.
Drive the whole chain and read the state after each step:

- **Prefer the app's own functions over synthetic clicks.** Where the flow is driven by
  named handlers, call them directly (`js("selectRecipientType(el)")`,
  `js("showPage('output')")`) instead of clicking the first text match — a
  `text=` locator silently resolves to a hidden duplicate (2+ elements) and clicks
  the wrong one, which looks like "the list is empty" and is a bug in your harness.
  Grep the source for the handler names and their real selectors first.
- **One step per assertion.** Snapshot the computed state after each step
  (`selectedRecipientType`, `document.querySelector('.x.selected').dataset.value`,
  `document.querySelectorAll('.item').length`). A regression at step 3 is invisible if
  you only read the final screen.
- **Fixture records created through the API: write, verify, then DELETE.** If you
  create a row to exercise a screen, delete it and re-read the count afterwards —
  confirm the record is actually gone, because a DELETE that returns an empty body
  (no JSON) still may or may not have applied. Live data must be left as you found it;
  a leftover fixture silently changes every later reading of that screen.

## Reverting a Visual Design ("верни к первому варианту")

When the user asks to revert a theme/visual to an earlier version:

1. **Back up current first** — `cp index.html index.html.bak-<label>` before any
   edit. Reverts are reversible only if the current state is preserved.
2. **Mass color-map swap, not per-block patching.** Extract the target palette
   from a known-good backup, build a `{old_hex: new_hex}` dictionary, and run one
   `str.replace` pass over the whole file. Patching each CSS block individually
   misses scattered rgba values and gradient stops.
3. **Map ALL color roles:** accent, background, surface, text (primary/secondary/
   muted), borders, dark-theme overrides, rgba shadow/glow values. A leftover
   hex in one gradient stop keeps the old theme alive.
4. **Grep for leftover old-theme hexes after the swap** — a gradient like
   `linear-gradient(135deg, #NEW, #OLD_TAIL, #NEW)` may keep an old middle stop
   if that hex wasn't in the map. Zero leftover occurrences before deploying.
5. **Verify with `getComputedStyle`, not source grep.** Tokens can be declared
   and unused; read concrete element values (`backgroundColor`, `fontFamily`,
   `textTransform`) to prove the theme actually renders.
6. **A visual revert changes CSS only.** Assert real data still renders after the
   swap to confirm the feature set is untouched.
7. **The user may want a DIFFERENT start screen than the current one.** When
   reverting visuals, check which screen is the start screen and whether the user
   referred to that one; "первый вариант" can mean the first DESIGN, not the
   first SCREEN, and features added later (a dashboard) may need removing too
   (see below).

## Removing an Entire Feature/Screen Cleanly

When deleting a screen/feature (e.g. "убери дашборд совсем"), remove in reverse
dependency order and verify zero references remain:

1. **HTML block** — find `<!-- comment -->` markers or `id=` boundaries, delete
   the section. If the removed screen was the start screen, restore the previous
   start screen by removing its `hidden` class.
2. **CSS** — delete the `:root`/rules block scoped to the feature (check for a
   second `:root` that must NOT be deleted).
3. **JS** — delete the module, its functions, and all call sites (`setTimeout`,
   `showPage` branches).
4. **Verify zero references:** `grep -c` for the feature's key identifiers
   (`id=`, CSS class prefix, function names). All must return 0.
5. **Confirm integrity** of surviving code — the enclosing function
   (e.g. `DOMContentLoaded`) must still be valid after the deletions.

## Pitfalls

- **A CSS variable that is never re-declared is the classic "dark on dark" bug.** The base
  `:root` sets `--text-primary` to a near-black value; a dark theme that recolors each selector
  leaves every `var(--text-primary)` consumer dark on dark, and nothing in the console or in a
  source grep flags it. List which selectors read tokens vs which carry literals and count the
  ones with no dark override — that gap IS the bug list.
- **Never conclude from your own passing browser run that the user's browser will
  agree.** When the server is confirmed correct (step 2) but the user still sees
  the old behaviour, say that plainly and give the hard-reload steps
  (Ctrl+Shift+R, or close and reopen the tab). Do not invent a deeper cause you
  have not reproduced, and do not keep shipping speculative patches at a
  verified-correct backend — each unfounded change adds a new untested variable.
- **When a user says only the first screen changed, verify all screens yourself.**
  A shared stylesheet either shipped everywhere or nowhere: confirm computed
  styles per screen and background pixels before repeating "hard reload". If the
  CSS really is live everywhere, the fix is the per-screen leftovers (emoji,
  inline styles), not the stylesheet.
- **Re-assert after EVERY interaction.** Several "fixes" turn out to be regressions
  in a different function. A handler that sets a variable only under
  `if (!x)` silently stops working once `x` is already set from a previous
  selection — a second DOM read right after the interaction catches it instantly.
- **Reproduce the EXACT path the user names — a sibling path is not evidence.**
  When the report is "path A → B → C resets the selection", drive that precise
  sequence in the browser and read the state at the end. Testing a neighbouring
  branch (clicking «отдел» when they said «цех») proves nothing about their path,
  and grepping the code for a *filter* proves nothing when the bug is an
  *override in a handler*. Both produce a false "it works" that the user refutes
  immediately — and a false negative is worse than no answer, because it sends the
  user looking for a problem that does not exist.
- **A silent fallback to the default branch hides an identifier mismatch.** When a
  lookup drives a summary/computed field and the value disagrees between your unit
  test and live data, the mismatch is in the literal, not the logic: compare the
  stored values in the DB against the code's expected string, character by
  character. A wrong identifier fails *closed* (falls into the default/`else`
  branch) and no error is raised — the code looks correct, the feature quietly does
  nothing. This is why "test passes on synthetic data, live data disagrees" is
  always a data-vs-code comparison, never a logic bug.
- **Distinguish a data problem from a UI bug before editing code.** Duplicate
  records (same number, different ids) are a data problem; deleting the later
  duplicate is the fix, not a code change. Query the database and count before
  deciding.
- **Never assert an empty container is a rendering bug without checking the query
  behind it.** Log the request the UI actually issues, replay it, and read the
  response status and body. A silently-ignored query parameter is invisible in
  the DOM.
- **Keep strict CSP when a browser test fails on `unsafe-eval`.** Some Playwright `wait_for_function` polling paths evaluate a string in the page world and trip the site's policy. Use locator assertions/waits for visible DOM state instead; do not weaken the production CSP to accommodate the test harness. Re-run from a clean context so the test-induced CSP error is not counted as a page error.
- **Open native details before checking lazy image decoding.** Images inside closed `<details>` can retain layout bounds yet never fetch, so an unbounded `img.decode()` can hang the entire suite. Open the actual summary control, scroll the image into view, and bound decoding with a rejecting timeout; record incomplete checks on interruption rather than treating the hang as a broken production resource.
- **Batch each sub-procedure into one browser call** (navigate + wait + read +
  act). One call per tiny action loses progress on timeout and burns the context.
- **URL-encode every REST filter value with spaces or non-ASCII** (emoji, Cyrillic):
  a raw `note=eq.проверка 🐀` in the request path raises `InvalidURL` before the
  request even goes out — `urllib.parse.quote()` the whole query fragment. Same
  class of bug: an unencoded space in a multipart body suffix — append the trailing
  boundary as `.encode()`, not as a bare `str` mixed into `bytes`.

## Schema Change Required Mid-Task

When the app needs a new DB column and the backend has only a service_role key:

1. **Prove the column is missing first** — one query
   `GET /rest/v1/<table>?select=<col>&limit=1`; a non-2xx (PGRST column not found)
   is the fact you report. Do not guess from the code.
2. **Do not hunt for DDL credentials.** REST does not do DDL, the Management API
   with a service_role key returns 401 (it wants a personal access token), and the
   DB password usually isn't on disk. Searching session history for it is the last
   resort — if it was never given, it doesn't exist.
3. **Hand the user one SQL block to paste** (Supabase Dashboard → SQL Editor):
   `ALTER TABLE … ADD COLUMN IF NOT EXISTS …` — and meanwhile write frontend and
   backend so they work before the migration too: send the new column ONLY when
   the field is non-empty, so nothing breaks pre-migration and nothing needs
   rewriting after.
4. **Verify the UI mechanically while the column doesn't exist yet** (elements
   present, no JS errors), and run the real write→DB→notification→UI loop only
   after the user confirms the migration. Then delete the fixture back out.

## When the Visual Reviewer Is Unavailable

The screenshot-review model (vision) can return 429 with a long `retry_after`
(tens of minutes) while the change still needs proving. Do not stall the work
and do not ship unverified — prove the CSS shipped mechanically and defer only
the taste review:

```python
# per-screen computed values prove the stylesheet applied
pg.evaluate("getComputedStyle(document.querySelector('.card')).borderRadius")
# and sample the real background pixel instead of trusting a screenshot
from PIL import Image
Image.open(shot).convert('RGB').getpixel((5, h // 2))
```

- New values on every screen ⇒ the theme shipped; report that as the verified
  fact and say plainly the visual/taste review is pending.
- When vision frees up, run the design read then and finish the remaining
  polish — do not re-do the already-proven verification.
- Confirm theme *token* presence is not enough: `--bordo:` present in the file
  proves nothing. Read `getComputedStyle` of concrete elements (button
  `backgroundColor`, `fontFamily`, `textTransform`) — tokens can be declared and
  unused, or overridden by later rules.

## Using Vision to Review a Redesign

Screenshots + the vision model turn a redesign into an actionable list, but read
the verdict for signal, not for every suggestion:

- Send 2–3 representative screens (menu, a working screen, a report) in one
  batch; a redesign pass that only changes the landing screen is the classic
  complaint "начальный экран изменился, остальные нет".
- Filter the findings: **structure and semantics** (a misleading big number, an
  unreadable icon, a ragged grid, emoji in a themed UI) are real; micro-taste
  nits (slightly different red shades) are not worth another round. Say which
  findings you acted on and which you deliberately left.
- When the review calls out a palette that "reads as a random set", fix the
  *system* (assign colour roles: operations vs system functions), not the one
  colour named.

## Builder-mounted content (Tilda, Webflow, any hosted page builder)

A builder's own preview endpoint and its published URL are different runtimes.
Tilda's `page_preview` returns the editor placeholder for a T123 code block
(`Код будет выполнен на опубликованной странице`) — grepping it for your markup
reports a false miss on a block that saved correctly. Sequence:

1. Read the SAVED source with `get_record_html` and grep for escaped content
   (`&lt;div class=&quot;…`); that proves the write landed.
2. Publish, then `curl -sS https://<site>/` the live URL and grep for BOTH a text
   marker and a structural marker (class name), so a stripped CSS block is caught.
3. Re-curl after any settings change — page-level `title`/`descr` only reach the
   served `<meta>` after re-publish, while project-level `descr` never does.
4. Mobile check without a device: `Emulation.setDeviceMetricsOverride` width=390,
   then assert `documentElement.scrollWidth <= clientWidth + 1` and read the grid
   `gridTemplateColumns`; clear the override afterwards.

## Reporting Shape

```
| Проверка | Результат |
| Сервер отдаёт новый HTML | ✅ marker найден |
| Действие в UI | ✅ ожидаемый DOM-результат |
```

Name what is verified and what remains untested. Never present a single passing
browser run as proof that the whole flow works.
