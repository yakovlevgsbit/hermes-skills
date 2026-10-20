---
name: tilda-mcp-cdp
description: "Use when editing Tilda sites at scale."
---

# Tilda MCP CDP — массовое редактирование Tilda

GitHub: https://github.com/skiddgoddamn/tilda-mcp-cdp
MIT, 5 stars, TypeScript, Node.js >= 18.

> **Полный разбор**: `/root/kb/projects/tilda-mcp-cdp.md`

## What It Is

MCP-сервер для Tilda: 16 инструментов. 5 на чтение через официальный API + 11 на запись через залогиненный Chrome по CDP.

Официальный Tilda API (api.tildacdn.info) — только чтение. Этот сервер добавляет слой действий через CDP.

## Architecture

```
MCP-клиент (Claude Code, Cursor, Desktop)
  ↕ MCP (stdio/HTTP)
tilda-mcp-cdp (TypeScript)
  ├─ Чтение → api.tildacdn.info
  └─ Запись → Chrome CDP (localhost:9222)
      ├─ Яндекс.Метрика
      ├─ Код-блоки T123 (ACE-редактор)
      ├─ Ссылки Zero Block
      ├─ Редактор элементов Zero Block
      ├─ Публикация (#page_menu_publishlink)
      └─ Проверка живого кода
```

## Read Tools (5)

| Tool | Описание |
|------|----------|
| `get_projects` | Список проектов |
| `get_project_info` | Информация о проекте (домен, CSS/JS) |
| `get_pages` | Список страниц |
| `get_page` | Полная информация о странице |
| `get_page_export` | Экспорт для хостинга |

## Write Tools (6)

| Tool | Args | Описание |
|------|------|----------|
| `chrome_status` | — | Проверка CDP и сессии |
| `set_metrika` | projectid, metrikaId | ID Метрики |
| `replace_page_code` | pageid, find, replace | Замена в T123 (regexp) |
| `replace_zero_links` | pageid, find, replace | Замена ссылок Zero Block |
| `publish_page` | pageid | Опубликовать |
| `verify_live` | urls, contains?, notContains? | Проверка живого HTML |

## Zero Block Editor (5)

| Tool | Описание |
|------|----------|
| `zero_get_elements` | Список элементов: тип, текст, ссылки, геометрия |
| `zero_update_element` | Deep-merge JSON-патча |
| `zero_add_element` | Клон + патч или произвольный JSON |
| `zero_delete_element` | Удалить элемент |
| `zero_set_text` | Regexp-замена текста |

## Key Patterns

1. **CDP обход read-only API** — залогиненная сессия + DevTools Protocol = полный доступ
2. **Модель данных вместо UI** — `ab__getDBSaveData()` + POST `/zero/submit/`
3. **Schema-safe клонирование** — новые элементы из существующих, всегда валидны
4. **Regexp-массовые замены** — find/replace по модели
5. **Всегда публиковать** — publish: true по умолчанию
6. **Проверка через браузер** — обход кэша и 403 tilda.ws
7. **Отдельный профиль Chrome** — обход защиты debug-порта (Chrome 136+)

## Requirements

- Node.js >= 18
- TILDA_PUBLIC_KEY + TILDA_SECRET_KEY (чтение)
- Chrome с debug-портом + вход в Tilda (запись)

## Debug Chrome

```bash
google-chrome --remote-debugging-port=9222 \
  --user-data-dir="C:\chrome-debug-tilda"
```

## MCP Config

```json
{
  "mcpServers": {
    "tilda": {
      "command": "node",
      "args": ["/path/tilda-mcp-cdp/dist/index.js"],
      "env": {
        "TILDA_PUBLIC_KEY": "...",
        "TILDA_SECRET_KEY": "...",
        "TILDA_CDP_URL": "http://localhost:9222"
      ]
    }
  }
}
```

## Итог

tilda-mcp-cdp — 16 инструментов для Tilda через MCP + CDP. Ключевая идея: официальный API только читает → управляй залогиненным Chrome через CDP.

Самое ценное для Георгия:
- **CDP обход read-only API** — универсальный приём
- **Модель данных вместо UI** — надёжнее и быстрее
- **Schema-safe клонирование**
- **Отдельный профиль Chrome** — обход защиты Chrome 136+
- **Проверка живого кода через браузер**