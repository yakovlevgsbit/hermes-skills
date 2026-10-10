# hermes-skills

Набор навыков (skills) для [Hermes Agent](https://hermes-agent.nousresearch.com/),
собранный под заказы на ботов и автоматизацию (Telegram / MAX, n8n, платежи, промпты).

## Установка

```bash
# добавить этот репозиторий как источник навыков
hermes skills tap add yakovlevgsbit/hermes-skills

# проверить, что Hermes их видит
hermes skills search payments

# установить конкретный навык
hermes skills install yakovlevgsbit/hermes-skills/development/telegram-bot-payments
hermes skills install yakovlevgsbit/hermes-skills/development/prompt-engineering
```

## Что внутри

| Навык | Зачем |
|---|---|
| `development/telegram-bot-payments` | Платежи в боте: CloudPayments / ЮKassa, подписки, рекуррент, выдача и отзыв доступа |
| `development/prompt-engineering` | Системные промпты, строгий JSON-вывод, text→image |

## Формат

Каждый навык — папка `<category>/<skill-name>/` с файлом `SKILL.md`
(YAML-frontmatter + markdown). Опционально: `references/`, `templates/`, `scripts/`.

Секреты в скиллы не кладутся — только путь к ним. Конкретику (порты, ключи)
вносят на месте при установке.
