# Delegating UI Design to an LLM

## When to Use
The user asks which free model can produce a modern UI redesign, or wants a
model to generate a screen for a mini-app. Covers testing models on OpenRouter,
what their output actually looks like, and how to audit it.

## Procedure
1. Save the current screen as a reference file before any model run, so the
   output has something to be compared against.
2. Write the brief to a file, covering: app context (what workers do with it),
   the screen structure to keep, the current design tokens, and hard technical
   constraints (single HTML file, CSS custom properties in `:root`, dark theme
   via `body.dark` token overrides, mobile-first, interface language).
3. Call OpenRouter chat completions — key at `/root/.secrets/openrouter.env`
   (`OPENROUTER_API_KEY`), endpoint `https://openrouter.ai/api/v1/chat/completions`,
   headers `HTTP-Referer` + `X-Title`. Ask for concept + tokens + full
   HTML/CSS + a diff list, so the answer is actionable.
4. Try candidates in order until one answers; record which worked.

## Model availability traps
- A model listed on the OpenRouter models page may have NO active endpoint:
  `nousresearch/hermes-4-70b` answers 404 "No endpoints found" even though the
  page lists it as the free Nous tier. Never promise a model from the listing
  alone — one cheap call first.
- Filter the listing strictly for the free tier: `pricing.prompt == "0"` AND
  `pricing.completion == "0"`. Prompt-only-zero entries include per-item paid
  models (Google's Lyria audio is billed per clip/song) and will 402.
- `thinkingmachines/inkling*` answers **403 "only available on agentic"** — it
  exists for agent harnesses, not plain chat completions. No retry helps.
- Free tiers rate-limit upstream (`inclusionai/ling-3.1-flash` → 429
  "temporarily rate-limited upstream"). Fall through to the next candidate in
  the same run instead of waiting.
- A free model that worked: `apodex/apodex-1.1-mini:free` (~21s for a full
  concept + code answer).
- **403 "only available on agentic"** — some free models refuse plain chat
  completions (they exist for agent harnesses only). No retry helps — skip.
- **`choices: None` in a 200 response** — the provider returned an error body in
  a success envelope; reading `r["choices"][0]` raises TypeError. Guard the
  parse and treat the model as skipped.
- Free-tier limits are per-provider and reset at provider speed, not yours:
  Google's free tier stayed 429 across 30s-spaced retries for a whole session.
  Cap at two attempts per model, then move on.
- **Availability churns between sessions** — the working set is per-run state.
  Re-probe every candidate each run; a model list from a previous session is a
  starting order, not a promise.

## Split the candidate list by task class, not by size
Coding models and general/reasoning models are not interchangeable, and a
single "best free model" answer is wrong. When the user asks which free model
suits a task, partition the list:

- **UI/code generation:** `cohere/north-mini-code:free` (holds a written brief
  best — scored highest against a mechanical requirement checklist),
  `poolside/laguna-s-2.1:free` (fastest full-screen draft), plus the
  `laguna-xs` sibling when it is up.
- **Prose/content generation (content plans, copy, strategy):** the large
  Nemotron tiers. `nvidia/nemotron-3-ultra-550b-a55b:free` was the only free
  model that returned a usable multi-day plan — the smaller Nemotron tiers
  truncated or dropped sections. Coding models compress prose hard (one
  returned 645 chars for a 7-day plan) and are the wrong tool here.
- **Never use `openrouter/free` as a measured candidate.** It is a router that
  silently picks an upstream free model, so a run through it cannot be
  attributed or reproduced; keep it only as a last-resort fallback.

## Markdown-table output from an LLM
When a generation task asks for a table, the parser must survive real model
output:

- **Inject the current date into the prompt.** LLMs do not know today, so
  "начиная с завтра" produces stale dates (a 2025 plan). Compute the start
  date in code (`datetime.date.today() + timedelta(days=1)`) and write the
  concrete date and weekday into the brief.
- **Row separators are `| :--- |`, not `|---|`.** Drop any line whose cells
  all match `:?-{3,}:?`, or separator rows parse as data rows.
- **Free-text sections after the table start with arbitrary prefixes** — `«…»`,
  digits, `-`, `•`. A parser that only accepts list markers silently returns
  zero items. Take every non-empty, non-separator line after the section
  heading and strip the marker with `^[\d\-\*•\.\)\s]+`.
- **One day per line.** Say so explicitly in the brief; otherwise a model
  emits one table per day, each with its own repeated header row, and the
  row count matches the day count only by accident.
- **Guard `content is None`** on reasoning models and fall back to
  `message["reasoning"]`; some Nemotron tiers return an empty `content` with
  the answer in `reasoning`.

## Generating into a store instead of a sheet
When the deliverable is a generated plan rather than a UI, the store-side shape
is the one from the Supabase skill: header row + one row per item, `plan_id`
foreign key with `ON DELETE CASCADE`, idempotent on the natural key (delete the
previous plan with the same topic, then insert fresh). Confirm the schema note
in `supabase-crud-patterns` covers the two-party ALTER before promising the
run.

## Comparing several free models in one run

When the user asks to run every candidate ("прогони все которые под код/дизайн"),
batch-run them on the SAME brief and tolerate failures:

1. One brief, one output dir, one screenshot script. Send models sequentially
   with a short sleep between calls — a parallel burst just triggers rate limits.
2. On failure, skip and record the error shape (see traps above). One retry with
   ~15–30s delay salvages models whose limiter resets fast (Poolside came back
   on retry); a provider locked for the day stays 429 regardless.
3. Extract HTML from fenced blocks — `re.search(r'```html\s*(.*?)```', text,
   re.S)` with a fallback to raw content when it starts with `<!DOCTYPE`. Some
   models wrap in fences, some don't; never save a fence marker into the file.
4. Render every output to a PNG with the standalone-playwright script at the
   bottom and deliver all screenshots at once (`MEDIA:<path>` per file) —
   "покажи что они сделали" means the artifacts, not a prose summary.
5. Score each output against the brief with a mechanical checklist (one row per
   requirement, present/absent) before presenting — it turns "какое лучше"
   into a defensible verdict instead of a vibe.

Free models work best as a **drafting tier in rotation** (2–3 models, skip on
429); the finishing stays by hand (see verdict below).

## Expected quality — the review checklist
Free models produce a good visual surface but do not hold the domain. Audit
every generated screen for:
- **Duplicated items** — given N actions the model may repeat one label twice
  (two cards both named "ОТЧЁТЫ") instead of inventing distinct ones.
- **Hallucinated domain words** — a sub-label like "остатки трубков" replaces
  the real noun from the brief. Re-read every user-visible string against the
  brief.
- **Inconsistent units** — different unit labels per card ("отрубов" vs
  "туш") with no stated rule.
- **Indistinguishable status badges** — "в наличии" and "мало" in the same
  colour; statuses need colour coding, not just text.
- **Generic metaphors** — a download icon for physical receipt, etc.

## Preventing the bugs in the prompt (self-check pattern)
Empirically tested: the same model with the same brief produced duplicates and
a hallucinated word WITHOUT a self-check requirement, and clean output WITH it.
Put these three in the brief itself:

- **Exact element list.** "Используй ТОЛЬКО эти 6 кнопок: A / B / C…" — nothing
  to invent, duplicates disappear.
- **Self-check requirement.** "Перечисли все кнопки по именам. Убедись: нет
  дублей. Проверь названия — не выдуманы." The model verifies its own output
  before delivering.
- **Hard output rules.** "НЕ пиши '// остальной код', TODO, псевдокод — только
  полный готовый файл."

Self-check fixes mechanical bugs (duplicates, invented words, truncation). It
does NOT fix UX decisions — functional duplication (a theme toggle in two
places), icon semantics, hierarchy. Those need the human reviewer.

Truncation is normal: `max_tokens: 6000` can cut the HTML mid-tag. Rebuild the
full file from the model's tokens + concept rather than pasting the fragment.

## Verdict framing for the user
Free models give "красивая обёртка с функциональными дырами" — a pretty shell
with functional holes. For a working tool the hand-built themed design wins:
the agent knows the domain (who receives what, unit rules, real menu items) and
ships no duplicates or hallucinations. Recommended use: borrow the model's
surface ideas (badge shapes, horizontal scrollers, hover motion) and
re-implement them by hand.

## Visual audit when vision is rate-limited
`vision_analyze` returns 429 with a `retry_after` of tens of minutes under
load. Do not loop on it. Verify structurally first:
- computed styles prove tokens landed: `getComputedStyle(el).borderRadius` /
  `.backgroundColor` / `.backgroundImage` on each page
- pixel sampling proves the body background: PIL `getpixel((5, h//2))` on a
  screenshot compared against the expected token hex
Then run the vision audit once the limit clears.

## Screenshotting for audit
When `browser_exec`'s `capture_screenshot` daemon times out, render with a
standalone playwright script through `execute_code` (same chromium as the PNG
reports):
```python
script = '''
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 440, "height": 820}, device_scale_factor=2)
    pg.goto("https://.../?v=cachebust")
    pg.wait_for_timeout(3000)
    pg.screenshot(path="/tmp/screen.png", full_page=False)
    b.close()
print("ok")
'''
```
