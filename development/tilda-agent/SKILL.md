---
name: tilda-agent
description: "Use when running mass ops on Tilda sites via MCP."
version: 0.1.0
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tilda, mcp, seo, head, css, sitemap, robots, redirects, ads, llms, automation, agent]
---

# Tilda Agent — CLI surface over Tilda MCP

The standalone CLI has no LLM/model of its own: it executes typed MCP operations. A manager or separate coding agent supplies the design and content; do not attribute a fixed neural model to this wrapper.

`tilda-agent` wraps the 278-tool Tilda MCP server at `tilda.ru/api/mcp/`
behind a typed CLI with dry-run/apply semantics and auto-backup before
every write. Lives at `/root/tilda-agent/`. Secret at
`/root/.secrets/tilda.env`. Smoke test: `python3 tests/test_smoke.py`
(25 checks: ping + 10 reads + 7 write cycles with auto-restore + 6 block
content checks — safe on production accounts). Takes ~14 min: Tilda rate-limits
heavily, the retries dominate the runtime.

## When to use

- Первым делом — проверка доступа: `get_projects` должен вернуть непустой список. Пустой список при рабочем `get_profile` означает пустой scope ключа, а не истёкший токен; лечится редактированием scope в Tilda → Профиль → MCP-сервер → ⋯ → Редактировать. Каждый `get_pages` тогда отвечает `-32031 insufficient_project_access`.
- Batch-edit SEO, head_code, CSS, sitemap, robots, ads.txt, llms.txt, 301
  redirects across Tilda sites — anything the editor does in 50 clicks,
  do in 1 shell command.
- Audit a Tilda site: `tilda seo audit <project_id>` walks every page
  and dumps titles, descriptions, head/page-head lengths.
- Run any of the 237 raw tools when the typed wrappers don't cover the
  case: `tilda call <tool> --json '{...}' --apply`.

## The non-standard MCP protocol (don't try the official library)

Tilda's MCP is **not** standard MCP over HTTP. Three things differ:

1. **Host**: `tilda.ru`, NOT `tilda.cc`. The same key works on one and
   fails on the other with `401 MCP key is not valid`. Default to `.ru`.
2. **Headers on every request**: `Mcp-Method: <initialize|tools/list|tools/call>`
   plus `Mcp-Name: <tool>` on tools/call. Standard `mcp` Python client
   has no hook for these — use raw httpx.
3. **`_meta` block** on every JSON-RPC body, holding protocolVersion,
   clientCapabilities, clientInfo. Missing it returns
   `Invalid params: _meta.X is required`.

Skipping any of these makes every call fail with cryptic errors.

## Tool quirks that burned real time — bake them in, never re-derive

- Parse each mutator's actual return shape: `add_blank_page` can return a numeric page ID, while `add_record` returns `{recordid: ...}`. Persist created IDs immediately; if parsing fails after a write, inspect the target before retrying so you do not create duplicate blocks.
- The tool gateway's `describe_tool` helper may not exist on the raw MCP endpoint (`Unknown tool`). For the raw CLI client, inspect `list_tools()` and the exact record's editor schema instead of repeatedly calling a gateway-only helper.
- HTTP 429 bodies can carry JSON-RPC `error.data.retry_at` even when Retry-After is absent. Respect that epoch deadline; header-only exponential retries can exhaust before the reset. Pace successful read/write/readback calls too. Keep task-specific retry changes in the task adapter rather than modifying shared production clients mid-build.
- For image-free native SV402 cards, a requested settings `height="auto"` may save canonically as `""`. Use the accepted empty value and verify it; do not weaken readback checks for unrelated values.

- **`head_code` is `headcode`** (one word) on the setter, NOT
  `head_code`. Wrong key → server silently ignores, returns OK.
- **`css_code` is `csscode`** — same trap.
- **`ads.txt`** requires BOTH `ads` and `appads` even if one is empty.
- **`llms.txt`** requires BOTH `llms` and `llmsfull` even if one is empty.
- **`sitemap`** requires `mode` (auto/manual) + optional `sitemapxml`.
- **`robots` `manual`** is the string `"on"` or `""` — NOT bool/int.
  Passing int returns OK and silently no-ops. The top-level `manual`
  field is not in the read response either; the mode lives in
  `project.json` as `{"robotstxt_manual": "on"}` vs `[]`.
- **`redirects`** wants `data: [{url_from, url_to}, ...]` — NOT
  `from`/`to`, NOT JSON-string. Wrong shape returns "Wrong redirects
  format!" or "Internal error".
- Do not assume page removal is unavailable: current catalogs include `delete_page` and recovery tools. Discover the current schema and key permissions, and use them only for explicitly authorized cleanup of a disposable target; absence from the high-level CLI is not absence from MCP.
- **`pages create` ignores the alias** — the published URL comes out as
  `page<id>.html`, and the alias field stays `""` unless set separately via
  `update_page_settings`.
- **`get_page` does not exist.** `page_preview` (full HTML) or
  `get_page_records` (block list).
- **`edit_record` on a Vibe Block (1370)** returns ONLY the field schema —
  `record` carries just id/pageid/tplid, no current `code`. Reading the stored
  code of a Vibe Block is not possible via MCP.
- **`edit_record` on a Zero Block (396)** returns the string
  `"Error.. This is zero"` — not a schema, not an envelope. The agent turns it
  into `{}` and every later `update_record` silently no-ops. Use `zero get`/
  `zero set`, never `record get`/`record set`, on tplid 396.
- **`edit_record` on a code-type block (131)** returns schema AND the current
  `record.code` — this is the read-modify-write path.
- **`get_zero_block` on a non-Zero record** returns the string
  `"It is not ZeroBlock!"` (not an error envelope). Treat a str result as failure.
- **Rate limits**: HTTP 429 or JSON-RPC `-32033 rate_limited` with
  `data.retry_at` (epoch seconds). The client retries with backoff
  (honours Retry-After / retry_at, exponential 1-2-4-8s, capped 30s,
  5 attempts). Batch jobs still need pacing.
- **`include_html`** on `get_page_records` must be a real boolean, not "y".

## Read-side: results are nested under `project`/`page`

Tilda's `get_*` tools return UI form dumps, not the bare value:

- `get_head_code` → real value at `.project.headcode`
- `get_sitemap_xml` → `.sitemapxml` (top-level)
- `get_robots_txt` → `.manualrobotstxt` / `.generatedrobotstxt` (mode in `project.json`)
- `get_redirect_301s` → `.project.json` (a list, possibly empty)
- `get_ads_txt` → `.project.adstxt` / `.project.appadstxt`
- `get_llms_txt` → top-level `.llmstxt` / `.llmsfulltxt`
- `get_page_settings` → already top-level (title, descr, alias, etc.)

The wrapper functions in `lib/commands.py` extract the real value so
callers get a clean string/list/dict.

## Zero Block (tplid 396) — the biggest trap. Read this before any zero edit.

**A Zero Block is JSON, not HTML. `record set` does NOT work on it.**
Sending HTML through `update_record` returns **OK while changing nothing** —
the write is silently swallowed and `page_preview` shows no new content.
Verified failure: a 2573-char hero HTML block landed nowhere.

Correct path, in this order:

1. `tilda instructions zero_block_instructions` — ALWAYS. 33 KB of format spec.
2. `zero get <record_id>` → JSON: numeric element keys (`"0"`, `"1"`) plus
   `groups`, `ab_*`, `timestamp`, `meta`.
3. Edit the JSON. Keep `ab_screens`, `meta`, `timestamp`.
4. `zero set <record_id> --from-file x.json --apply` → **whole JSON replaces
   the block**. Omitted elements keep their values.
5. Verify with `pages get <pid> --preview` — grep for your text. `update_*`
   returning OK is NOT proof of the write.

**`elem_id` MUST be unique per element or the styles silently collapse.**
Format: 13-digit ms timestamp + 6-digit counter → 19 chars
(`1792679094359000001`, `1792679094359000002`). Tilda generates one CSS rule
per `data-elem-id`; duplicate ids make the last rule win for ALL elements.
Symptom: every text renders at one size/colour — e.g. all 4 hero elements
came out 14px grey instead of 64px/22px/16px/14px.

**Zero Block structure by `elem_type`:**

| key | meaning |
|---|---|
| `text` | `text` (HTML: `<br>`,`<b>`,`<a>`,`<span style>`), `tag` (`h1`/`h2`/`h3`), `fontsize`, `color`, `fontfamily`, `lineheight`, `fontweight`, `textfit` (`fixedsize`/`autoheight`) |
| `button` | `caption` (plain text, no HTML), `link`, `bgcolor`, `color`, `borderradius`, `textfit`, `align` |
| `shape` | `figure`, `bgcolor`, `borderradius` |
| `image` | CDN url from `upload_image` — never raw base64 or external links |
| `html` | `code` — embed/widget/script/map ONLY. Stripped on the free plan. |

Common keys on every element: `elem_id`, `elem_type`, `top`, `left`, `width`,
`height` + `*units` (`px`), `zindex`, `hidden`, `padding`, `borderradius`,
`valign`, `shadow_text_opacity`.

Artboard: `ab_height`, `ab_bgcolor`, `ab_screens` (`360,480,640,960,1200`),
`ab_valign`, `ab_upscale`.

**Tilda's own rule: do NOT put a whole HTML page in an `html` element.**
Translate HTML into native elements (`text`/`button`/`image`/`shape`), because
page markup in one element is uneditable, ignores breakpoints and project
fonts, and is stripped on the free plan.

**A fresh `add_record 396` ships editor demo content** — a sample image and a
yellow square. Replace the elements; keep `ab_screens` and `meta`.

## Content: pages and blocks (records)

MCP reads AND writes block content. There is **no `get_page` tool** — reading a
page is done through `page_preview` (full HTML) or `get_page_records`
(block list). Writing a block's HTML/CSS/JS is `update_record` with
`tab="content"`, `only_field="code"`, `fields={"code": "<...>"}`.

CLI surface:

```bash
tilda pages get <page_id> --project <pid>                 # block list
tilda pages get <page_id> --project <pid> --preview --to-file p.html
tilda record get <record_id> --page-id <pid> --project <pid> --code
tilda record set <record_id> --page-id <pid> --project <pid> --from-file f.html --apply
tilda record html <record_id> --page-id <pid> --project <pid>
tilda record add 131 --page-id <pid> --project <pid> --after <rec> --apply
tilda zero get|set <record_id> --page-id <pid> --project <pid>
tilda tpls --filter zero
```

TplIDs: **131** = HTML/code block, **1370** = Vibe Block, **396** = Zero Block
(JSON only — see the Zero Block section above, `record set` does NOT apply).
Read-modify-write is safe for 131: `record get --code` returns the CURRENT
value, so you send back exactly what you read (plus your change).

**Verify every write by reading the page back.** `update_record` and
`update_zero_block` return `OK` for content they did not save — the only
proof is `pages get <pid> --preview | grep -c '<your text>'`.

**An empty Zero Block still occupies 600px of artboard.** Adding a block
before writing content pushes the real block below the fold — the page looks
blank on the first screen. Add ONE block, fill it, then delete the leftovers:
`record delete <record_id> --page-id <pid> --project <pid> --apply`.

## Server convention: call `*_instructions` first

The server's initialize response says: *"Before a task that needs
several tool calls, call the matching tool ending in `_instructions`
and follow the step-by-step instructions it returns."* Always do this
for multi-step ops (Zero Block edits, page import, vibe block).
Wrapper: `tilda instructions zero_block_instructions`.

## Safety posture

- Write commands default to **dry-run** — show diff and backup plan,
  apply nothing. Add `--apply` to commit.
- Every write first saves current state to
  `output/backups/<kind>_<id>_<timestamp>.json`. Restore by feeding the
  backup's `value` back through `tilda <cmd> set --code '...'` +
  `--apply`.
- Secret in `/root/.secrets/tilda.env` (chmod 600). Never hardcode, log,
  or commit.
- The CLI itself uses HTTPS MCP, not browser automation. Account setup or scoped-key creation outside its permissions may use the authenticated editor with browser-vault tools. Never change existing keys or other projects as collateral work; never put passwords in chat or ordinary browser input tools.
- If vault fill reports success but the active login form's password-readiness boolean is false, inspect duplicate login tabs opened for the task. Reconcile those duplicates and use one target rather than assuming bad credentials or copying a password manually. Never print password values while diagnosing.

## Layout

```
/root/tilda-agent/
├── agent.py              CLI (argparse), dry-run/apply, backups
├── lib/client.py         raw httpx MCP client (retries on 429/5xx)
├── lib/commands.py       typed wrappers (get/set/audit + block content)
├── tests/test_smoke.py   smoke: reads + 6 write cycles + block RMW
├── output/backups/       auto-backups before every write
└── README.md
```

## Unpublished-site delivery and QA

- Inspect the account and existing project before creating a new one. A project-scoped MCP key cannot create projects outside its scope; do not mistake its filtered `get_projects` list for the full account. Reuse an existing draft only after the user identifies/authorizes it. Keep the build key limited to that project and omit publication rights when publication is not authorized.
- Treat Tilda preview as a distinct runtime: native forms render as `.t-form` DIVs, submission is disabled, and page-head/T123 custom code is omitted. Open the authenticated editor with `?pageid=...&previewmode=yes` and inspect its iframe; a direct `/page/preview/` navigation can return a blank document. Do not publish to work around this boundary.
- Capture exact `page_preview` HTML and run isolated browser replay with real CDN assets when preview interaction tools are limited. Label replay, explicit saved-head injection, authenticated live preview, and end-to-end form delivery separately. Never call local validation or an injected script proof of actual submission.
- Verify native form time ranges, not just masks: a `tm` field can accept `29:99`. For a booking inquiry, a required native `sb` dropdown of valid demonstration times avoids that gap without custom JavaScript; label choices as preferences, not available appointment slots.
- Test FAQ keyboard state after automatic sibling closure and rapid toggling. In tplid 1119, exclusive `checkbox3="on"` can leave stale ARIA or pending timers that hide newly opened panels. When exclusivity is not required, `checkbox3=""` enables independent panels and avoids the sibling-close race; recheck the rendered state after the write.
- Use `.t-zoomer__wrapper` and `body.t-zoomer__show` for gallery assertions, not a nonexistent `.t-zoomer`. Always close overlays in `finally` and isolate test contexts so one failed gallery check cannot cascade into false form/navigation failures.
- Keep contacts fictional honestly: a configurable Telegram link may target an explanatory local anchor until the owner supplies a real handle. Do not connect receivers belonging to other sites just because the account-wide editor lists them. Native Leads storage and external receivers are separate; actual delivery still needs an authorized published-page test.

## Known limitations

- **No visual-editor automation.** Nothing drives clicks, drag-and-drop, or the
  mobile-view adaptive settings in the Tilda editor. Page assembly = create the
  page (`pages create`), add blocks (`record add`), write HTML/CSS/JS into them
  (`record set`, `zero set`), set SEO/head/CSS/sitemap/redirects, publish.
  Zero Block and custom HTML blocks do NOT produce a mobile version by
  themselves — that is checked by a human in the editor's mobile view.
- Some account/plan combinations silently no-op certain writes (e.g.
  redirects on the test account respond OK but persist nothing).
  Always verify with the corresponding `get` after a real write.
- The agent owns 1 account (whatever key is in `.secrets`). For
  multi-account work, swap the env file or pass `TILDA_MCP_KEY` /
  `TILDA_MCP_URL` explicitly to the client.
