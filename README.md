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

### development — боты, платежи, промпты, реверс-инженеринг

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
| `famulor-skill` | Голосовые агенты: ассистенты, звонки, кампании, телефония (hosted MCP) |
| `tweetclaw` | X/Twitter автоматизация: поиск, экспорт подписчиков, мониторы, посты |
| `cronalytics` | Диагностика cron-задач Hermes: здоровье, сбои, дрейф расписания |
| `figma` | Тянет дизайн из Figma REST API (нужен `FIGMA_TOKEN`) → реализация макетов |
| `ui-ux-pro-max` | UI/UX-дизайн интеллект: 79 стилей, палитры, шрифты, UX-правила (search.py, своя база) |
| `dewiar-reverse-engineering` | Голосовой ассистент Dewiar — 93 модуля, архитектура, mixin-паттерн |
| `comfyui-reverse-engineering` | ComfyUI — node system, caching, WebSocket, execution engine |
| `agent-skills-addy-osmani` | 25 production-скиллов, 9 slash-commands, dev lifecycle |
| `context7-docs` | MCP-сервер для актуальной документации библиотек |
| `graphify-knowledge-graph` | Knowledge graph из codebase, EXTRACTED/INFERRED, MCP tools |
| `magic-mcp-21st` | 10,000+ React/Tailwind компонентов, HTTP MCP, AI генерация |
| `strix-ai-pentesting` | AI-пентест, multi-agent orchestration, Docker sandbox |
| `rea-reverse-engineering` | REA — 324.7k stars, MCP для реверс-инженерии бинарников, JS, .NET, Android, firmware |

### devops — CI/CD, инфраструктура

| Навык | Зачем |
|---|---|
| `devops-tools-essentials` | ArgoCD, SOPS, Kestra, Gitea, Sentry — GitOps, secrets, self-hosted Git |

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

### payments — платежи, биллинг

| Навык | Зачем |
|---|---|
| `payments-billing-platforms` | Hyperswitch (45.3k), Polar (10.3k), Lago (10.7k) — composable, usage-based, AI billing |

### email — автоматизация почты

| Навык | Зачем |
|---|---|
| `email-ai-automation` | AI triage, three-tier classification, draft-first approach, Slack/Telegram |

### productivity — продуктивность

| Навык | Зачем |
|---|---|
| `jev-router` | Model routing by complexity, 5 вопросов, safety-first bias, ~$0.00006/решение |

## Формат

Каждый навык — папка `<category>/<skill-name>/` с файлом `SKILL.md`
(YAML-frontmatter + markdown). Опционально: `references/`, `templates/`, `scripts/`.

Секреты в скиллы не кладутся — только путь к ним. Конкретику (порты, ключи)
вносят на месте при установке.
