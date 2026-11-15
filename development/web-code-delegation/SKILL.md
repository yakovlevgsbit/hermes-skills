---
name: web-code-delegation
description: "Delegate web code generation to the web-assistant engine."
version: 1.0.0
author: curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web-assistant, delegation, codegen, html, banner, cover, visual-asset, manager-subagent]
---

# Delegating web code to web-assistant

## When to Use

Load when the user asks for web code — a page, a landing, a dashboard, a banner,
a cover — or when a visual asset must match a reference the user supplied.
Also load when you catch yourself about to hand-write an HTML artifact: that is
the signal you are taking the coder's role instead of the manager's.

This user treats you as the **manager** and web-assistant as the **coder**. When
you hand-write a deliverable yourself, they call it out as a process failure,
not just a style nit. Delegate generation, then verify and integrate.

## Engine

`/root/web-assistant/scripts/codegen.py`:

```python
import sys; sys.path.insert(0, "scripts")
import codegen
html, status = codegen.generate_html(task_text, max_tokens=4000)
```

`status == "ok"` means the engine extracted a complete-looking HTML block and
passed its structural check. It does not prove that the response finished, that
the block is the final answer rather than an example, or that the app works;
validate the candidate and exercise the required flow before accepting it.

### Provider chain and its guards

`_providers()` tries **nous → openrouter (free) → anymodel (paid)**. Each entry
carries its own models, token floor and timeout; `call_model()` records the winner
in `LAST_MODEL` (`provider:model`) — read it before assuming which route paid.

Three guards are load-bearing, and removing any one degrades output silently:

- **User-Agent on every request.** anymodel sits behind a WAF: a valid key with no
  browser UA gets `403`, which reads as "the fallback is dead" rather than "the
  header is missing".
- **Per-provider token floor** (`ANYMODEL_MIN_TOKENS = 7000`). Flash and free
  models spend the budget on the reasoning trace: at 4000 the reply comes back
  empty with `finish=length`.
- **`MIN_RESPONSE_CHARS` floor (2500).** A free model answers a landing-page
  request with a ~700-character stub that passes structural validation and ships
  as an empty page. Treat a short reply as a refusal and let the chain escalate;
  `_is_tiny_task()` bypasses the floor for genuinely small artifacts.

**Free model IDs rot.** An entire `MODELS` list can point at models deleted
upstream, and the engine then returns `no-model-response` for weeks without ever
raising. Before debugging anything else on that status, diff `MODELS` against the
provider's live `/v1/models` and check for a per-account/day 429 — free tiers are
capped account-wide, so minting a second key does not restore quota.

## Design contract in the prompt

`codegen.py` carries `DESIGN_CONTRACT`, injected into every generation prompt: one
page job, one style family, system fonts with a 12→95px scale, `clamp()` hero,
60–75ch measure, one accent on ≤10% of pixels, colours only through `var()`,
4→96 spacing scale, alternating asymmetry, all interaction states, one `h1`,
concrete copy, explicit bans, and a 390/768/1440 check.

Point any new engine or fork at that constant instead of restating taste in the
task text: the task text is the brief, the contract is the floor.

What it reliably buys, measured across generations of the same task: no purple
gradients, no emoji icons, no CDN fonts or external URLs, tokens present,
`:focus-visible` present, specific copy. What it does **not** guarantee:
no horizontal overflow at 390px — that varied run to run even after adding a rule
for it. Prompt rules move the distribution, not the floor: verify layout by
rendering, and treat one good sample as one sample.

Source of the scale and the bans: the anti-slop catalog and typographic scale of
`AkyRayy/Frontend-Design-SKILLS-for-AI` (MIT), condensed into the `claude-design`
skill's style-families and anti-slop-catalog references.

For bounded patch snippets, use the same engine's `call_model()` raw-code path
instead of asking `generate_html()` to validate a JSON/fragment envelope as a
whole page. Save the raw response before parsing so a rejected envelope does
not discard otherwise complete code. Integrate only reviewed, complete snippets
against exact source boundaries and rerun the failing regression; do not pass off
an incomplete model response as a finished page.

## Rules

- **Never hand-write what the engine can generate.** Delegate, review, integrate.
- **Nous creds come from `agent_key` / `access_token`** in `/root/.hermes/auth.json`
  (`providers.nous`), NOT from `api_key` — that field is empty and every call
  returns 401. OpenRouter is the fallback.
- **Task text is the spec.** State target pixel size, layout direction, exact
  strings (title, subtitle, price), the accent color per item, and the palette.
  Output only what you actually need (e.g. an HTML document) — the engine pads
  with prose otherwise.
- **Reasoning models need token headroom.** Budget ≥2500 tokens for a full page;
  below that the model spends the whole budget thinking and returns nothing. On
  anymodel's flash models the practical floor is 7000 — the reasoning trace alone
  consumed ~6000 of a 7000-token request.
- **Generated scaffolds are often structurally broken.** One unclosed or
  mis-nested tag upstream makes the browser parser silently drop a later
  element: the source looks fine, the DOM is empty. Diagnose against the live
  DOM (element counts via `document.querySelectorAll`), never the source text.
- **Salvage, don't rewrite.** When a coding run ends unsuccessfully, inspect its
  saved source and run the existing checks before restarting generation: it may
  have persisted a complete layout but only part of the interactions. Preserve
  verified markup/styles and delegate the missing behaviour with exact selectors,
  edit boundaries and failing tests instead of regenerating the whole page.
  When the scaffold itself is broken, move the working functions into a scaffold
  verified in the browser. Report this as integrating delegated code.

## Functional applications and long code responses

For working applications, default to separate `index.html`, `app.css` and
`app.js` (plus small modules when useful), with relative asset/API paths. Keep
`script-src 'self'` and `style-src 'self'`; do not add inline event handlers,
`eval`, or weaker CSP to accommodate generated output. A one-off self-contained
visual artifact can still use the engine's single-document format.

Define separate acceptance gates for frontend behavior, genuine content/data,
and live backend integration before dispatch. Passing fixture or mocked-API tests
closes only the frontend gate, not the entire product. Keep fixtures outside
release data and label them visibly in any demonstration.

For this user, production means the requested content and real integrations are
present and verified, unless a reduced scope is explicitly approved. Do not turn
permission to publish into permission to promote a fixture demo or silently use a
different source edition. In status reports, distinguish content not yet authored
or built from content merely not connected; name each remaining gate plainly.

Follow `references/functional-app-generation.md` for the ordered generation,
repair and verification loop. Record which code is raw engine output, which
complete fragments were salvaged, and which bounded corrections the integrator
made; never present a repaired artifact as untouched model output.

## Handoff from an external design service

Treat a Stitch screen or similar generated design as a design input, not a
working application. Pass the approved HTML/screenshots, exact token contract,
project/screen revision, routes and preserved behavior in the executor's task.
Installing a skill in the manager's profile does not automatically make it
available to the web-assistant engine.

Keep client material and tokens project-scoped. Require explicit permission
before uploading private interfaces; use sanitized demo data for an initial
pilot. Do not infer upload permission from permission to inspect local code.

Retain our compile/render/interaction checks even if a foreign skill calls them
optional. Define a finite page list, generation ceiling and stop condition for
baton-style loops, rather than inventing pages after the approved backlog ends.
Research example: `/root/kb/projects/stitch-skills.md`.

## Existing-site redesign brief

1. Give the coder the audited, currently served source and a bounded working copy
   inside the existing project. Include the preserved services, published prices,
   exact demo/contact URLs and pages that must not change; an unrelated prototype
   is not a redesign of the user's site.
2. Separate confirmed working projects from prospect mockups and private
   applications. Supply actual captured interfaces with their access conditions;
   never turn a login screen into a fictional dashboard or claim a live client
   system is a safe sandbox.
3. State the real contact transport. Without a backend, require a working direct
   contact link or an explicitly labelled local message draft. Preparing, copying,
   opening a messenger and sending are different outcomes; do not permit a fake
   submission-success state. Require validation, invalidation after edits,
   clipboard-denial recovery and a no-JavaScript direct-contact fallback.
   Use `references/client-only-inquiries.md` for the implementation sequence and
   test matrix when a static site needs a draft-building form.
4. Preserve the approval boundary in the coder's brief. When publication is
   reserved for approval, deliver a local preview from the release source rather
   than uploading a public staging copy as an unannounced implementation step.

## Bound the critical path and finish the handoff

1. Define the required handoff before dispatch: saved source, an executable test
   command, a preview from that source and any deployment-approval gate. Separate
   these from optional polish so a reviewer cannot silently expand the task.
2. Bound the generation call and the implementer's scope. After a failed or
   interrupted run has ended, apply the salvage rule above: run the saved tests
   before commissioning a replacement. A failed worker status does not establish
   that its persisted code is incomplete.
3. Treat a complaint about delay as a scope-control signal. Stop an overlong
   optional run, wait for its terminal handoff, then finish from the saved
   artifact; do not restart the whole design or add another review layer. Keep
   backups, required functional checks and approval gates intact.
4. Once required checks pass, package and deliver the working result with a short
   verified summary and explicit limitations. Do not hold it for another agent's
   prose summary, speculative polish or new reporting machinery. This user values
   a working handoff over an expanding review process.
5. Pin the handoff to its tested artifact manifest and accepted generation runs.
   Reconcile a late completion against that record before acting: an earlier
   failed or superseded run does not invalidate the accepted build. Do not replay
   old patches, restart generation, or send a chat acknowledgement for every
   duplicate notification. Reopen work only for a new acceptance-relevant finding,
   and report that finding rather than the subprocess history.

## Verification is mandatory

1. Render headless (Playwright) at the **exact target pixel size** the consumer
   requires — ask or read the platform's spec, never guess from the earlier
   artifact's dimensions. For a responsive site, also test phone, tablet and
   desktop widths and record overflow and CTA placement.
2. Exercise the interactions separately from rendering: menu and keyboard paths,
   service selection, invalid input, draft preparation, editing after preparation,
   copy failure and the no-JavaScript contact fallback. A complete HTML document
   and a passing happy-path test do not prove that every visible button works.
   Check accessible names as well: keep a control's visible wording in its
   accessible name. Prefer native link/button text; when adding `aria-label`,
   retain the visible label and append context rather than replacing it. An
   unnecessary label can override a readable brand or CTA and break voice-control
   matching even though the screen looks correct.
3. Read the screenshots with `vision_analyze` against the user's reference. Keep
   measured layout/a11y results distinct from visual judgement; intentionally
   clipped screen-reader-only labels are not evidence of visible text clipping.
4. Fix and re-render confirmed defects. Report separately what rendered, which
   interactions passed and whether deployment was approved/performed. Deliver the
   actual preview/screenshots; do not substitute a description of the design.
5. For engine output, the static-and-render audit is already written:
   `/root/web-assistant/tests/contract_audit.py --skip-generate --audit <file.html>`
   checks the design contract statically and renders 390/768/1440 with
   screenshots plus `contract-audit.json`. Run it before delivery instead of
   hand-checking token counts; drop `--skip-generate` to exercise the whole
   provider chain on a fresh task.

## Pitfall: asset format drift

The consumer's required dimensions are the spec. A banner sized to a previous
artifact or a generic guess is rejected outright — re-render to the stated size
before showing anything. When the user sends a screenshot of the target
platform's form or reference, extract the concrete numbers from it first.

## Manager contract

- Deliver the real artifact plus the real tool output that proves it renders.
- When the user requests a test link, deliver a verified clickable URL and a short
  sequence of concrete interactions to try. A server filesystem path, an archive
  alone, or `127.0.0.1` on a remote host is not a link the user can open.
- Preserve the publication boundary. If a public demo is authorized but production
  changes are not, use an isolated temporary preview of the tested snapshot rather
  than modifying existing services. Label fixture data and unavailable AI/backend
  features, state the link's expiry, and verify the live URL before sharing it.
  If publication is not authorized, supply the runnable local artifact and say
  plainly that no public link exists; do not silently upload a staging copy.
- Batch related assets in one pass when they share a look.
- State what the user must verify, and where the source files live so they
  survive temp-directory cleanup — copy deliverables into the project's
  durable storage and commit them.

## Other delegated agents (same manager contract, different engines)

The role split is not specific to web code: when the user says "make an agent
for X", the deliverable is the full pipeline — task file → executable agent
script → output file → artifact delivered to their chat — never a SKILL.md
documenting the tool.

Currently wired this way:

| Agent | Engine | Trigger | Delivers |
|---|---|---|---|
| web-assistant | `/root/web-assistant/scripts/codegen.py` | web code / banner / cover requests | HTML artifact |
| «Крыса» (maps parser) | `/root/maps-agent/scripts/maps_agent.py` wrapping `/root/maps-agent/parser/` (ru-maps-parser) | «запусти крысу по <тема>» | xlsx base of organizations with phones/email |

### Tool-wrapping agent procedure (service lifecycle agents)

For an agent whose job is to run a tool that itself runs as a service (parser,
scraper, exporter), the script — not you — owns the lifecycle:

1. Parse the task file (`key: value` lines: source / query / city / format).
2. Start the tool on a **free port** — probe with a socket connect, never
   hardcode the first port (a previous run may still hold it).
3. Submit the job via the tool's REST API; record the job id.
4. Poll until a terminal status — accept **every** terminal spelling the tool
   uses (`finished`, `done`, `cancelled`, `failed`), or the agent hangs on a
   job that already ended.
5. Fetch the result and write `output/<task>.<ext>` + a report.

Run with `terminal(background=true, notify=true)` — these runs take minutes,
and holding the foreground burns the turn. When the completion notification
lands, verify the output file on disk and deliver it with `MEDIA:/path`.

### Pitfalls specific to tool-wrapping agents

- **The tool will close its API before you download.** A long job ends with
  the service shutting down right after saving its own result copy, so the
  export endpoint answers 404 by the time the agent polls. Always add a
  fallback that reads the tool's own saved artifact (its data dir, e.g.
  `~/.local/share/<tool>/results/<job>.csv`) and converts to the requested
  format (`csv_to_xlsx` via xlsxwriter) — the user must get the format they
  asked for, never a silent wrong-extension file.
- **Copy the vendored tool out of the scratch dir.** Scratch is pruned after
  24h — an agent whose engine lives there dies silently.
- **Honor the user's name and trigger verbatim.** Record the agent's name,
  trigger phrase, task-file format, and invocation recipe in KB + memory so
  future sessions answer the right trigger without re-deriving it.
- **Verify source viability before building.** A tool blocked by geo (RU-only
  service from a non-RU VPS) or whose ToS forbid scraping is not wired in —
  checking this up front avoids building an agent around a dead engine.