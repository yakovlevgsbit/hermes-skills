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
| `development/max-messenger-api` | Платформа MAX: sender в query, endpoints, ловушки верификации |
| `development/service-credentials-vault` | Хранение ключей: `/root/.secrets` (700/600), проверка, без утечек в код |
| `integrations/n8n-workflows` | n8n REST: аудит, PUT в живые воркфлоу, бэкапы, шаблоны |
| `integrations/google-sheets-writes` | Запись в Google Sheets через API v4 (Bearer, обход ловушек) |

## Формат

Каждый навык — папка `<category>/<skill-name>/` с файлом `SKILL.md`
(YAML-frontmatter + markdown). Опционально: `references/`, `templates/`, `scripts/`.

Секреты в скиллы не кладутся — только путь к ним. Конкретику (порты, ключи)
вносят на месте при установке.
