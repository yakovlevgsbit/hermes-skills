---
name: context7-docs
description: "Use when fetching current library docs for AI agents."
---

# Context7 — Up-to-date Code Documentation for LLMs

GitHub: https://github.com/upstash/context7
MIT, 62.8k stars, 3.1k forks. By Upstash.

> **Полный разбор**: `/root/kb/projects/context7-docs.md`

## What It Is

Context7 Platform — MCP-сервер который даёт AI-агентам доступ к актуальной документации библиотек вместо устаревших training data.

## Architecture

```
Clients (30+): Claude Code, Cursor, Codex, Windsurf, Gemini, Antigravity
  ↕ MCP (JSON-RPC over stdio/HTTP)
context7-mcp (TypeScript) — OPEN SOURCE
  ├─ resolve-library-id (resolve)
  └─ query-docs (fetch)
Context7 API — PRIVATE (not in repo)
  ├─ API backend
  ├─ Parsing engine
  └─ Crawling engine
```

## MCP Tools

### 1. resolve-library-id

Вход: `libraryName` + `query`
Выход: список библиотек с score (name, libraryId, benchmark score)

### 2. query-docs

Вход: `libraryId` (напр. `/vercel/next.js`) + `query` (один концепт)
Выход: актуальная документация с code examples

## 3 Skills

| Skill | Что делает |
|-------|----------|
| `context7-mcp` | Основной: resolve → query → документация |
| `context7-cli` | CLI usage через `ctx7` |
| `find-docs` | Поиск документации если не знаем точное имя |

## Key Principles

1. **Training data ≠ current docs** — LLM обучены на данных с датой окончания. Context7 даёт актуальную документацию.
2. **One topic per query** — multi-topic → несколько вызовов. Combined queries размывают ranking.
3. **Version-aware** — "React 19" → version-specific ID.
4. **Benchmark scoring** — качество документации оценивается автоматически.
5. **Private backend + open server** — сервер открыт, backend закрыт.
6. **Rules + Skills + Plugins** — три уровня интеграции для агентов.
7. **Multi-agent support** — `.claude-plugin/`, `.cursor-plugin/`, `.agents/plugins/`, `.gemini/`, `.opencode/`.

## Packages

| Пакет | NPM |
|--------|-----|
| `@upstash/context7-mcp` | MCP server |
| `ctx7` | CLI |
| `@upstash/context7-sdk` | TypeScript SDK |
| `@upstash/context7-tools-ai-sdk` | Vercel AI SDK tools |
| `@upstash/context7-pi` | pi.dev extension |

## Installation

```bash
npm install -g @upstash/context7-mcp
npm install -g ctx7
# or: npx skills add upstash/context7
```

## Key Patterns

1. **MCP tool design** — resolve → query (двухшаговый)
2. **One topic per query** — разбивать сложные вопросы
3. **Version-aware resolution** — всегда учитывать версию
4. **Training data ≠ current docs** — сверяться с актуальной документацией