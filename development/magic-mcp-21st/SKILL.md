---
name: magic-mcp-21st
description: "Use when searching React UI components."
---

# Magic MCP → 21st MCP — UI Component Generation

GitHub: https://github.com/21st-dev/magic-mcp
ISC, 5.9k stars. By 21st.dev.

> **Полный разбор**: `/root/kb/projects/magic-mcp-21st.md`

## What It Is

HTTP MCP-сервер для поиска и генерации React/Tailwind UI компонентов. Каталог 10,000+ компонентов. AI-генерация новых UI.

Magic MCP переименован в **21st MCP**. Старый пакет `@21st-dev/magic` остаётся как compatibility proxy.

## Tools

| Tool | Что делает |
|------|-----------|
| `search` | Поиск компонентов по запросу |
| `get_component` | Получить код компонента |
| `get_inspiration` | Получить идеи для UI |
| `search_logo` | Поиск логотипов |
| `generate` | AI-генерация нового UI (требует AI access) |
| `iterate_generation` | Итерация над сгенерированным UI |
| `tools/list` | Список доступных инструментов |
| `get_usage` | Проверить AI generation enabled |

### Legacy Tool Names

| Legacy | New |
|--------|-----|
| `21st_magic_component_builder` | `generate` |
| `21st_magic_component_inspiration` | `get_inspiration` |
| `21st_magic_component_refiner` | `generate` (from refinement prompt) |
| `logo_search` | `search_logo` |

## Configuration

### HTTP MCP
```json
{
  "mcpServers": {
    "21st": {
      "url": "https://21st.dev/api/mcp",
      "headers": {
        "x-api-key": "YOUR_21ST_API_KEY"
      }
    }
  }
}
```

### CLI
```bash
npx @21st-dev/cli@latest init
```

### Environment Variables
- `API_KEY_21ST` — основной
- `TWENTY_FIRST_API_KEY` — legacy
- `API_KEY` — legacy positional

### Stdio Proxy (legacy)
```bash
npx -y @21st-dev/magic@latest API_KEY="..."
```

## Platforms

| Платформа | Установка |
|-----------|----------|
| Claude Code | `/plugin install` from repo |
| Cursor | Cursor Marketplace → "21st" |
| Codex CLI | `codex plugin install` |
| Windsurf | Config |
| Grok Build | `grok plugin install 21st --trust` |

## Business Model

| Что | Free | Paid |
|-----|------|------|
| Search components | ✅ | ✅ |
| Get component code | ✅ | ✅ |
| AI generation | ❌ | ✅ (AI subscription) |
| Iterate generation | ❌ | ✅ |
| Team libraries | ❌ | ✅ |

## Key Patterns

1. **HTTP MCP** — не stdio, а HTTP endpoint с API-ключом в header
2. **Compatibility proxy** — старый пакет форвардит на новый сервер
3. **Legacy tool names** — сервер принимает старые имена и транслирует
4. **AI access gate** — `generate` и `iterate_generation` только с AI subscription
5. **Plugin marketplace** — репозиторий = marketplace, можно установить напрямую
6. **Multi-platform** — один сервер, много клиентов

## API Key

Получить: https://21st.dev/mcp

Старые Magic API keys сброшены. Нужен новый ключ.

## Итог

21st MCP — 5.9k stars, каталог 10,000+ React/Tailwind компонентов. Ключевая идея: искать готовые UI компоненты вместо генерации с нуля. AI-генерация для кастомных вариантов.

Самое ценное для Георгия:
- **Search first** — не генерировать с нуля, а искать готовое
- **HTTP MCP** — проще чем stdio, API-ключ в header
- **Legacy compatibility** — старые конфиги работают через proxy
- **AI gate** — платная AI-генерация, бесплатный поиск