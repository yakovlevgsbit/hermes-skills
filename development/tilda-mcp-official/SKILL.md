---
name: tilda-mcp-official
description: "Use when managing Tilda sites via MCP."
---

# Tilda MCP (official) — 278 инструментов

Tilda's own MCP server. Manages sites, pages, blocks, feeds, store, settings, statistics.

> **Полный разбор**: `/root/kb/projects/tilda-mcp-official.md`

## What It Is

Официальный MCP-сервер Tilda. **278 инструментов** (проверено 2026-11-08; в октябре было 235). Расклад: `store_*` 112, `stats_*` 40, `feeds_*` 34, остальное — страницы, блоки, публикация, SEO, настройки.

Группа `stats_*` — новая: статистика страниц, магазина, UTM, гео, вовлечённость. Набор инструментов растёт, поэтому число в доке не догма — актуальный список берётся из `tools/list`.

## Key scope: 200 OK на tools/list ≠ доступ к проекту

Ключ может быть валиден и при этом не видеть ни одного проекта. Симптом:

```
tools/list        → 200, 278 tools
get_profile       → 200 (username, userplan, endsubscription)
get_projects      → []
get_pages {pid}   → -32031 Forbidden: MCP key does not have access to project <pid>
                    error_code: insufficient_project_access, retryable: false
```

Это не истёкший ключ и не сбой сети: у ключа пустой/неверный scope проекта. Диагностика — сравнить `get_profile` (работает) и `get_projects` (пусто).

**Починка — ТОЛЬКО новый ключ.** Проверено 2026-11-08 на живом кабинете: правка scope существующего ключа через ⋯ → «Редактировать» сохраняется в UI (после перезагрузки таблицы проекты видны, «Полный доступ»), но MCP продолжает отвечать `[]` и `-32031 Forbidden`. Ключ остаётся мёртвым для проектов. Рабочий путь:

1. «Новый ключ» → название → «Выбранные» → отметить нужные проекты → права → срок «Бессрочно» → «Создать ключ».
2. Ключ показан один раз в модалке; модалка закрывается сама, и `innerText` его НЕ содержит — значение лежит в поле (`input`/`code`). Читать `document.querySelectorAll('input,textarea,code')` → `.value`, иначе ключ потерян безвозвратно (пересоздавать).
3. Записать в `/root/.secrets/tilda.env` (не печатать в чат) и заменить литерал в `/root/.hermes/config.yaml` → `mcp_servers.tilda.headers` — Hermes держит ключ там, а не из env.
4. Проверить: `get_projects` непустой, `get_pages` по каждому проекту отдаёт список страниц, `tilda projects list`.

Живой процесс Hermes держит MCP-клиент со старыми заголовками до перезапуска — CLI и боты (читают `.env`) работают сразу, инструменты `mcp__tilda__*` в текущей сессии — только после рестарта.

В списке ключей есть колонка «Использован» — по ней видно, какой ключ реально ходит в API; свежая отметка после теста подтверждает, что тестируется тот ключ.

**Удаление ключа:** три точки в строке → «Удалить» → подтверждение в `#confirm-dialog` (`input.js-ps-popup-yes`). Меню может открыться ниже вьюпорта (высота окна 577px по умолчанию) — перед кликом расширить окно через `Emulation.setDeviceMetricsOverride` (height 1000) и брать координаты из `getBoundingClientRect`; иначе клик уходит мимо и диалог не появляется.

Проверять доступ сразу после создания ключа: `get_projects` должен вернуть непустой список.

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

Access: full or limited (modules + actions). Expiry: 1h to unlimited — **не редактируется** после создания, только удалить ключ и создать новый. Scope проекта и модули редактируются в любой момент.

Подключение: только к агентам, установленным как приложение на устройстве; облачная версия в браузере не подойдёт. Hermes на VPS работает (это не браузер) — проверено.

Тариф: Personal или Business. `get_profile` → `userplan` и `endsubscription` (epoch) показывают фактический статус.

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

## Tool categories (278)

| Category | Count / examples |
|----------|----------|
| Store | 112 `store_*` (products, orders, discounts, connectors, loyalty) |
| Stats | 40 `stats_*` (page/store stats, UTM, geo, involvement, charts) |
| Feeds | 34 `feeds_*` (posts, parts, publishing, templates) |
| Pages | `add_blank_page`, `delete_page`, `duplicate_page`, `move_page`, `get_pages` |
| Zero Block | `get_zero_block`, `update_zero_block`, `update_zero_block_title` |
| Publishing | `publish_page`, `unpublish_page`, `page_preview`, `page_undo`, `page_redo` |
| Settings | `update_project_head_code`, `update_page_head_code`, `update_project_css_code` |
| SEO | `update_project_robots_txt`, `update_project_sitemap_xml`, `update_project_redirects_301` |
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