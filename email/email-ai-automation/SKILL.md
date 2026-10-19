---
name: email-ai-automation
description: "Use when automating inbox triage or email workflows."
---

# Email AI Automation

> **Полный разбор**: `/root/kb/projects/email-ai-automation.md`

## Top Repositories

| Репозиторий | Stars | Тема |
|-------------|-------|------|
| Inbox Zero | ~6k | AI email assistant (Superhuman alternative) |
| Email Triage Plugin | ~1k | AI triage для Claude |

## Key Patterns

1. **AI triage** — LLM читает и классифицирует email
2. **Three-tier classification** — Direct Asks (🔴), Account Updates (🟠), FYI (🟢)
3. **Draft-only, never sends** — безопасный подход
4. **Voice-matched responses** — черновики в твоём стиле
5. **Persistent index** — `triage-index.jsonl` отслеживает каждый email
6. **Multi-platform** — Slack, Telegram, CLI
7. **Calendar integration** — meeting briefs
8. **Smart filing** — автоматическое сохранение вложений

## Inbox Zero

- Open source альтернатива Superhuman
- AI drafting, calendar, attachments
- Slack & Telegram integration

## Email Triage Plugin

```bash
/email          # Full inbox triage
/email work     # Only work emails
/email personal # Exclude work
/summary        # Alias for /email
```

Three tiers:
- 🔴 Direct Asks → Draft reply
- 🟠 Account Updates → Draft reply
- 🟢 FYI → Archive

## Итог

Email automation: AI triage, draft-first approach, multi-platform. Ключевая идея: LLM как executive assistant для inbox.