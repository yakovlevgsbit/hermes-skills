---
name: tilda-mcp-official
description: "Use when managing Tilda sites via MCP."
---

# Tilda MCP (official) — 235 инструментов

Tilda's own MCP server. Manages sites, pages, blocks, feeds, store, settings.

> **Полный разбор**: `/root/kb/projects/tilda-mcp-official.md`

## What It Is

Официальный MCP-сервер Tilda. **235 инструментов**: страницы, Zero Block, публикация, SEO, магазин (~90), Потоки (~25), медиа.

## CRITICAL: host is tilda.ru, NOT tilda.cc

```
❌ https://tilda.cc/api/mcp/  → 401 "MCP key is not valid"
✅ https://tilda.ru/api/mcp/  → 200 OK
```

The key is bound to the Russian account (tilda.ru). tilda.cc is the international site — the same key is rejected there.

## Auth

```
Authorization: Bearer <mcp_tilda_KEY>
```

Key created at: **Tilda → Профиль → MCP-сервер → Новый ключ**

Key format: `mcp_tilda_` + 48 hex chars (58 total). Shown ONLY once.

Access: full or limited. Expiry: 1h to unlimited (cannot be changed after creation).

## Protocol (non-standard, critical)

Three required headers per request:

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <key>` |
| `MCP-Protocol-Version` | `2026-07-28` |
| `Mcp-Method` | method name |
| `Mcp-Name` | tool name (tools/call only — NOT standard MCP) |

Missing `Mcp-Method` → `Header mismatch: Mcp-Method header is required`
Missing `Mcp-Name` → `Header mismatch: Mcp-Name header is required`

## Call sequence

```
1. initialize   (Mcp-Method: initialize)
2. notifications/initialized
3. tools/call    (Mcp-Method: tools/call, Mcp-Name: <tool>)
```

## Required _meta

```json
{"_meta": {
  "io.modelcontextprotocol/protocolVersion": "2026-07-28",
  "io.modelcontextprotocol/clientCapabilities": {},
  "io.modelcontextprotocol/clientInfo": {"name": "hermes", "version": "1.0"}
}}
```

Missing fields → `Invalid params: _meta.X is required`.

## Tool categories (235)

| Category | Examples |
|----------|----------|
| Pages | `add_blank_page`, `delete_page`, `duplicate_page`, `move_page` |
| Zero Block | `get_zero_block`, `update_zero_block`, `update_zero_block_title` |
| Publishing | `publish_page`, `unpublish_page`, `page_preview`, `page_undo`, `page_redo` |
| Settings | `update_project_head_code`, `update_page_head_code`, `update_project_css_code` |
| SEO | `update_project_robots_txt`, `update_project_sitemap_xml`, `update_project_redirects_301` |
| Store | ~90 `store_*` (products, orders, discounts, connectors) |
| Feeds | ~25 `feeds_*` (posts, sections, publishing) |
| Media | `upload_image` |
| Instructions | `zero_block_instructions`, `vibe_block_*_instructions`, `website_import_instructions` |

## Working example

```bash
curl -s -X POST https://tilda.ru/api/mcp/ \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" \
  -H "Mcp-Method: tools/call" \
  -H "Mcp-Name: get_projects" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_projects","arguments":{},"_meta":{...}}}'
```

## Key patterns

1. **Non-standard headers** — `Mcp-Method` + `Mcp-Name` beyond spec MCP
2. **Host matters** — `.ru` vs `.cc` decides which account owns the key
3. **Strict protocol** — 3 protocol versions, full `_meta` required
4. **No split** — one endpoint, no SSE

## Итог

Tilda MCP — 235 инструментов для полного управления сайтом. Ключевая идея: официальный MCP вместо ручной автоматизации браузера.

Самое ценное для Георгия:
- **Хост `tilda.ru`** — ключ к разгадке "invalid_token"
- **Заголовки `Mcp-Method` / `Mcp-Name`** — нестандартное расширение
- **235 инструментов** — полное управление сайтом
- **Ключ показывается один раз** — сразу сохранять