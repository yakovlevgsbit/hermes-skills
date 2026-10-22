---
name: tilda-agent
description: "Use when running mass ops on Tilda sites via MCP."
---

# Tilda Agent — CLI over Tilda MCP

A typed CLI wrapping the 237-tool Tilda MCP server at `tilda.ru/api/mcp/`, with
dry-run/apply semantics and auto-backup before every write.

> **The MCP protocol itself** (host, headers, `_meta`, 237 tools) is documented in
> the `tilda-mcp-official` skill. This one covers the **operating procedure**:
> how to drive bulk edits and read/write block content safely.

## When to use

- Bulk-edit SEO, head_code, CSS, sitemap, robots, ads.txt, llms.txt, 301
  redirects across Tilda sites — what the editor does in 50 clicks, done in
  one shell command.
- Audit a site: `tilda seo audit <project_id>` walks every page and dumps
  titles, descriptions, head/page-head lengths.
- Read and write **block content** (HTML/CSS/JS) programmatically.
- Drive any of the 237 raw tools when the typed wrappers don't cover it:
  `tilda call <tool> --json '{...}' --apply`.

## Install / connect

```bash
# 1. The MCP server must be configured in Hermes (see tilda-mcp-official for
#    the protocol). The CLI reads the key from /root/.secrets/tilda.env:
#      TILDA_MCP_KEY=mcp_tilda_...
#      TILDA_MCP_URL=https://tilda.ru/api/mcp/
#    chmod 600 on that file.

# 2. If the agent is not on PATH yet:
ln -s /root/tilda-agent/agent.py /usr/local/bin/tilda   # or use the wrapper
#    The wrapper is /usr/local/bin/tilda -> `python3 /root/tilda-agent/agent.py`

# 3. Verify:
tilda ping          # -> {"server": {...}, "tool_count": 237}
```

If `hermes mcp test tilda` fails with `mcp.client.streamable_http is not
available`, that is a missing venv extra, not a dead key — see
`hermes-mcp-server-setup` (fix: `hermes pm install --extra mcp` +
`hermes gateway restart`). A long-lived gateway activates its venv once at
boot, so MCP servers added later need a restart.

## Read commands (safe)

```bash
tilda ping
tilda projects list
tilda pages list <project_id>
tilda pages get <page_id> --project <pid>          # block list
tilda pages get <page_id> --project <pid> --preview --to-file page.html
tilda seo audit <project_id>
tilda head get|css get|sitemap get|robots get|ads get|llms get <project_id>
tilda redirects list <project_id>
tilda record get <record_id> --page-id <pid> --project <pid> --code
tilda record html <record_id> --page-id <pid> --project <pid>
tilda zero get <record_id> --page-id <pid> --project <pid> --to-file block.json
tilda tpls --filter zero
```

## Write commands (dry-run by default, `--apply` to commit)

```bash
tilda head set <project_id> --from-file head.html --apply
tilda css set <project_id> --from-file style.css --apply
tilda sitemap set <project_id> --from-file sitemap.xml --mode manual --apply
tilda robots set <project_id> --from-file robots.txt --apply
tilda ads set <project_id> --from-file ads.txt --apply
tilda redirects set <project_id> --from-file redirects.json --apply
tilda seo update <page_id> --project <pid> --title "..." --description "..." --apply
tilda record set <record_id> --page-id <pid> --project <pid> --from-file f.html --apply
tilda record add 131 --page-id <pid> --project <pid> --after <rec> --apply
tilda zero set <record_id> --page-id <pid> --project <pid> --from-file block.json --apply
tilda pages create <project_id> "Title" --apply
tilda pages publish <page_id> --project <pid> --apply
```

## Content: pages and blocks

MCP reads AND writes block content. There is **no `get_page` tool** — reading a
page is `page_preview` (full HTML) or `get_page_records` (block list). Writing a
block's HTML/CSS/JS is `update_record` with `tab="content"`,
`only_field="code"`, `fields={"code": "<...>"}`.

TplIDs: **131** = HTML/code block, **1370** = Vibe Block, **396** = Zero Block.
900 templates are listed by `tilda tpls` (with `cod` codes like `T123`, `VIBE`).

Read-modify-write is safe: `record get --code` returns the CURRENT value, so you
send back exactly what you read (plus your change). `tilda zero get` dumps the
whole Zero Block JSON — edit it, send it back with `zero set`.

## Pitfalls baked into the code — never re-derive

- **`head_code` is `headcode`** on the setter, NOT `head_code`. Wrong key →
  server silently ignores, returns OK.
- **`css_code` is `csscode`** — same trap.
- **`ads.txt`** requires BOTH `ads` and `appads`; **`llms.txt`** requires BOTH
  `llms` and `llmsfull` — even when one is empty.
- **`sitemap`** requires `mode` (`auto`/`manual`) + `sitemapxml`.
- **`robots` `manual`** is the string `"on"` or `""`, NOT bool/int. Passing an
  int returns OK and silently no-ops. The read side has no top-level `manual`
  either — the mode lives in `project.json` as `{"robotstxt_manual": "on"}`.
- **`redirects`** wants `data: [{url_from, url_to}, ...]` — NOT `from`/`to`, NOT
  a JSON string.
- **`add_blank_page`** ignores a `title` param — pages always spawn as
  "Blank page"; set the title via `update_page_settings` after.
- **`edit_record` on a Vibe Block (1370)** returns ONLY the field schema — no
  current `code`. Reading stored Vibe Block code is not possible via MCP.
- **`edit_record` on a code-type block (131)** returns schema AND the current
  `record.code` — this is the read-modify-write path.
- **`get_zero_block` on a non-Zero record** returns the string
  `"It is not ZeroBlock!"` (not an error envelope). Treat a str result as failure.
- **Rate limits**: HTTP 429 or JSON-RPC `-32033 rate_limited` with
  `data.retry_at` (epoch seconds). The client retries with backoff (honours
  Retry-After / retry_at, exponential 1-2-4-8s capped 30s, 5 attempts).
- **`include_html`** on `get_page_records` must be a real boolean, not `"y"`.

## Server convention: call `*_instructions` first

The server's initialize response says: *"Before a task that needs several tool
calls, call the matching tool ending in `_instructions` and follow the
step-by-step instructions it returns."* Do this for Zero Block edits, page
import, and vibe blocks. Wrapper: `tilda instructions zero_block_instructions`.

## Safety posture

- Write commands default to **dry-run** — show the diff and backup plan,
  apply nothing. Add `--apply` to commit.
- Every write first saves current state to
  `output/backups/<kind>_<id>_<timestamp>.json`. Restore by feeding the backup's
  `value` back through `tilda <cmd> set --code '...' --apply`.
- Secret in `/root/.secrets/tilda.env` (chmod 600). Never hardcode, log, or commit.
- No browser automation. Pure HTTPS MCP. No passwords in chat ever.

## Limitations

- **No visual-editor automation.** Nothing drives clicks, drag-and-drop, or the
  mobile-view adaptive settings in the Tilda editor. Page assembly = create the
  page, add blocks, write HTML/CSS/JS into them, set SEO/head/CSS/sitemap/
  redirects, publish. Zero Block and custom HTML blocks do NOT produce a mobile
  version by themselves — that is checked by a human in the editor's mobile view.
- Some account/plan combinations silently no-op certain writes (e.g. redirects
  on a test account respond OK but persist nothing). Always verify with the
  corresponding `get` after a real write.
- One account per install (whatever key is in the env file).

## Verify

```bash
python3 tests/test_smoke.py
```

Runs reads, 6 write cycles with auto-restore, and a block content
read-modify-write (byte-for-byte restore). Safe on production accounts.
