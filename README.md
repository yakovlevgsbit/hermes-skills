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

### development — боты, платежи, промпты
| Навык | Зачем |
|---|---|
| `telegram-bot-payments` | Платежи в боте: CloudPayments / ЮKassa, подписки, рекуррент, доступ |
| `stripe-link-cli` | Международные платежи: Stripe Link, карты, подписки, апрувы |
| `prompt-engineering` | Системные промпты, строгий JSON-вывод, text→image |
| `max-messenger-api` | Платформа MAX: sender в query, endpoints, ловушки верификации |
| `shopify` | E-commerce: Shopify Admin/Storefront GraphQL |
| `telephony` | Голосовые боты: Twilio номера, SMS/MMS, AI-звонки |
| `service-credentials-vault` | Хранение ключей: `/root/.secrets` (700/600), без утечек |
| `subagent-driven-development` | Делегирование кода сабагентам + 2-этапное ревью |
| `dynamic-workflow` | Fan-out планы, adversarial-верификация, волны |

### integrations — n8n, таблицы, деплой, скрапинг
| Навык | Зачем |
|---|---|
| `n8n-workflows` | n8n REST: аудит, PUT в живые воркфлоу, бэкапы, шаблоны |
| `google-sheets-writes` | Запись в Google Sheets через API v4 (Bearer) |
| `docker-management` | Управление контейнерами, образами, Compose |
| `publish-site` | Деплой на GitHub/Cloudflare/Netlify Pages |
| `cloudflare-temporary-deploy` | Показать демо клиенту за секунды, без аккаунта |
| `watchers` | Мониторинг RSS/JSON/GitHub с дедупом (усилитель лидов) |
| `searxng-search` | Бесплатный keyless мета-поиск (70+ движков) |
| `scrapling` | Скрапинг со stealth + Cloudflare bypass |

## Формат

Каждый навык — папка `<category>/<skill-name>/` с файлом `SKILL.md`
(YAML-frontmatter + markdown). Опционально: `references/`, `templates/`, `scripts/`.

Секреты в скиллы не кладутся — только путь к ним. Конкретику (порты, ключи)
вносят на месте при установке.
