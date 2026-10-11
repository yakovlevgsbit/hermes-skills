---
name: figma
description: Fetches design data directly from the Figma REST API and uses it to implement or reference designs. Use automatically when the user shares a Figma URL (figma.com/design/..., figma.com/file/..., figma.com/proto/...), asks to implement, build, or inspect a Figma design, mentions "from Figma", "this Figma", or "the Figma file", pastes a node ID (formats like 1-2, 1:2, or 1%3A2) or a file key, or asks to extract styles, variables, tokens, colors, typography, or components from a Figma file.
---

# Figma Design Fetch & Implement

Fetch design data directly from the Figma REST API using a personal access token. This works for any Figma account (including free) and does not require the Figma desktop app or an MCP server.

---

## Step 1 — Parse the URL

Extract `fileKey` and `nodeId` from the user's message or `$ARGUMENTS`.

URL shapes to handle:

| URL pattern | fileKey | Notes |
|---|---|---|
| `figma.com/design/:fileKey/:name?node-id=1-2` | `:fileKey` | Current format |
| `figma.com/file/:fileKey/:name?node-id=1-2` | `:fileKey` | Legacy format, still valid |
| `figma.com/proto/:fileKey/...` | `:fileKey` | Prototype links |
| `figma.com/design/:fileKey/branch/:branchKey/...` | `:branchKey` | Branches have their own key — use the branch key in API calls, NOT the parent file key |

**Node ID normalization.** The API requires colons (`1:2`), but URLs may contain any of:
- `node-id=1-2` → replace `-` with `:` → `1:2`
- `node-id=1%3A2` → URL-decode `%3A` to `:` → `1:2`
- `node-id=1:2` → use as-is

Always normalize to the colon form before calling the API. If no `node-id` is present, treat the request as a full-file overview (Step 3b).

---

## Step 2 — Check for token

```bash
if [ -z "$FIGMA_TOKEN" ]; then
  echo "FIGMA_TOKEN_MISSING"
fi
```

If the token is missing, stop and tell the user:

> `FIGMA_TOKEN` is not set. To fix:
> 1. Go to Figma → account menu (top-left) → **Settings → Security**
> 2. Scroll to **Personal access tokens** → **Generate new token**
> 3. Set scopes: `file_content:read` and `file_metadata:read`
> 4. Add it to `~/.claude/settings.json` under an `env` block — see the skill's README for exact instructions
> 5. Restart Claude Code

Do not attempt any API calls until the user confirms the token is set.

Also check once whether `jq` is available — it affects later steps:

```bash
command -v jq >/dev/null 2>&1 && echo "HAS_JQ" || echo "NO_JQ"
```

---

## Step 3 — Fetch design data

### 3a. Specific node (preferred when a node ID is available)

```bash
curl -sS -w "\nHTTP_STATUS:%{http_code}\n" \
  -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/nodes?ids={nodeId}&depth=4"
```

The `depth=4` parameter limits nested children to avoid huge responses. Increase to `6` or omit only if the user needs deeper detail (e.g. a nested design system component).

If `jq` is available, extract just the node:

```bash
curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/nodes?ids={nodeId}&depth=4" \
  | jq '.nodes | to_entries[0].value.document'
```

### 3b. Full-file overview (when no node ID was given)

Do not fetch the full tree — use `depth=1` to get just pages and their top-level frames:

```bash
curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}?depth=1" \
  | jq '{name: .name, lastModified: .lastModified, pages: [.document.children[] | {id: .id, name: .name, frames: [.children[]? | {id: .id, name: .name, type: .type}]}]}'
```

Present the list to the user and ask which frame to implement before fetching deeper data.

### 3c. Handle errors

Check the HTTP status before parsing. Common cases:

- **403** — token is invalid, expired, or missing the required scopes. Ask the user to regenerate it with `file_content:read` and `file_metadata:read`.
- **404** — wrong file key, wrong node ID, or the file was moved. Double-check that the node ID was normalized to colon form and that the user has access to the file.
- **429** — rate limited. Wait a few seconds and retry once; if it persists, tell the user to try again later.

Surface these as short, actionable messages — do not dump the raw JSON error.

---

## Step 4 — Fetch a rendered image (optional, recommended)

For visual reference, especially for complex layouts, fetch PNG render URLs from the API:

```bash
curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/{fileKey}?ids={nodeId}&format=png&scale=2" \
  | jq -r '.images | to_entries[0].value'
```

This returns a signed S3 URL (valid for ~30 days). The `Read` tool cannot open remote URLs — use the bundled script to download images to a local temp directory first, then read them from there.

**macOS / Linux** — use `scripts/download-images.sh`:

```bash
bash scripts/download-images.sh <name> <url> [<name> <url> ...]
# Images saved to /tmp/figma-images/<name>.png
```

**Windows** — use `scripts/download-images.ps1`:

```powershell
.\scripts\download-images.ps1 <name> <url> [<name> <url> ...]
# Images saved to $env:TEMP\figma-images\<name>.png
```

Both scripts accept any number of name/url pairs and print the saved paths on completion. Pass all frames at once — the shell script downloads in parallel.

After the script finishes, use the `Read` tool on each local path to view the images. Seeing the rendered design alongside the JSON dramatically improves implementation accuracy.

Use `scale=2` for crisp renders. Use `format=svg` for icons or vector-heavy frames.

---

## Step 5 — Fetch styles (optional)

Named styles (fills, text, effects) defined in the file:

```bash
curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/styles"
```

This returns style metadata (names, descriptions, style keys) but not the actual values. To get the values, fetch the nodes those styles are attached to, or fetch the full file and resolve `styles` references inside each node.

### Variables (design tokens)

```bash
curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/variables/local"
```

**Note:** This endpoint requires a Figma **Enterprise** plan and returns 403 on Starter / Professional / Organization plans. If it fails, fall back to extracting color/spacing values from the node JSON directly — `fills[].color`, `style.fontSize`, etc.

---

## Step 6 — Implement the design

From the node JSON, the fields that matter most:

- `type` — `FRAME`, `TEXT`, `RECTANGLE`, `INSTANCE` (component usage), `COMPONENT`, `VECTOR`, etc.
- `name` — often a useful hint for the component/class name
- `absoluteBoundingBox` — `{x, y, width, height}` in file coordinates
- `layoutMode` — `HORIZONTAL` / `VERTICAL` / `NONE`; maps to flexbox direction
- `primaryAxisAlignItems` / `counterAxisAlignItems` — flex justify/align
- `itemSpacing`, `paddingLeft/Right/Top/Bottom` — gap and padding
- `fills`, `strokes`, `strokeWeight`, `cornerRadius`, `effects` — visual style
- `style` — typography on TEXT nodes: `fontFamily`, `fontWeight`, `fontSize`, `lineHeightPx`, `letterSpacing`
- `children` — nested nodes
- `componentId` / `componentSetId` — resolves to entries in the top-level `components` / `componentSets` maps for reusable components

Implementation guidance:

- Prefer `layoutMode` + `itemSpacing` + padding over absolute positions. Figma's auto-layout maps cleanly to flexbox; absolute coordinates rarely should.
- Match the project's existing tokens and components before inventing new ones — check the repo for SCSS/CSS variables, Tailwind config, or component libraries.
- Convert Figma colors (`{r, g, b, a}` with values 0–1) to hex or rgba for the target stack.
- `INSTANCE` nodes point to existing components — resolve them before treating as bespoke UI.

---

## Endpoint reference

| Goal | Endpoint | Notes |
|---|---|---|
| Full file structure | `GET /v1/files/{fileKey}` | Use `?depth=N` to limit size |
| Specific node(s) | `GET /v1/files/{fileKey}/nodes?ids={nodeId}` | Comma-separate multiple IDs |
| Rendered image | `GET /v1/images/{fileKey}?ids={nodeId}&format=png&scale=2` | Also supports `svg`, `jpg`, `pdf` |
| File styles | `GET /v1/files/{fileKey}/styles` | Metadata only |
| Design variables | `GET /v1/files/{fileKey}/variables/local` | **Enterprise plan only** |
| Comments | `GET /v1/files/{fileKey}/comments` | |
| File metadata | `GET /v1/files/{fileKey}/meta` | Lightweight — name, thumbnail, last modified |

All requests require the header `X-Figma-Token: $FIGMA_TOKEN`.

Rate limits are per-token and generous for typical use, but aggressive polling or fetching many full-file trees can hit them — prefer node-scoped fetches with `depth` limits.