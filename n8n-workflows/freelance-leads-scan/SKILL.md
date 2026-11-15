---
name: freelance-leads-scan
description: FL.ru + Kwork lead scanner cron job.
version: 1.0.0
---

# Freelance Leads Scan

Система автоматического поиска заказов на Kwork с генерацией откликов.
FL.ru убран из парсинга по запросу пользователя.

## Архитектура

```
cron (каждые 30 мин)
  └─ scan_leads.py (no_agent, stdout → Telegram)
       ├─ submit.py --profile all  →  research agent daemon
       │    └─ RSS + browser парсинг → results.jsonl
       ├─ wait_for_results()  →  ожидание новых строк
       ├─ collect_candidates()  →  фильтр по NICHE_WORDS + NICHE_STOP
       ├─ check_open_and_budget()  →  headless Chromium
       └─ build_reply()  →  LLM (OpenRouter / Nous) → Telegram digest
```

## Ключевые файлы

| Файл | Назначение |
|---|---|
| `/root/.hermes/scripts/scan_leads.py` | Главный скрипт (cron job) |
| `/root/kb/agents/research/submit.py` | Отправка задач в research agent |
| `/root/kb/agents/research/agent.py` | Демон парсинга (запущен отдельно) |
| `/root/kb/agents/research/data/results.jsonl` | Результаты парсинга |
| `/root/kb/agents/research/data/seen.json` | Дедупликация (242 id) |
| `/root/kb/agents/research/data/queue.jsonl` | Очередь задач |
| `/root/.hermes/cron/output/8d557545a31e_*.txt` | История запусков |

## Cron Job

- **ID**: `8d557545a31e`
- **Name**: `freelance-leads-scan`
- **Schedule**: `every 30m`
- **Deliver**: `telegram:-1003646733293:11`
- **Script**: `scan_leads.py`
- **no_agent**: true
- **Interpreter**: `/root/.hermes/installs/8a4017c4cabfe15f/environments/8586a6b426684d48afd4cfc1a23bda08/venv/bin/python3.14`

## Фильтрация ниш

### NICHE_WORDS (заказ наш, если есть любое)
```python
NICHE_WORDS = [
    "telegram", "телеграм", "бот", "боты", "n8n", "автоматиз", "чат-бот",
    "интеграц", "скрипт", "парсер", "mini-app", "мини-апп", "mini апп",
    "supabase", "google sheets", "гугл таблиц", "вебхук", "webhook",
    "мессенджер", "vps", "crm", "api", "рассылк", "ai-консультант",
    "ии-консультант", "gpt", "нейросет", "ai-ассистент", "ai-",
    # e-commerce / payments
    "shopify", "интернет-магазин", "ecommerce", "e-commerce",
    "платеж", "эквайринг", "подписк", "рекуррент", "stripe", "robokassa",
    "cloudpayments", "юkassa", "онлайн-оплат", "checkout",
    # voice / telephony
    "голосов", "ivr", "twilio",
    # deploy / hosting
    "docker", "контainer", "деплой", "хостинг",
    "cloudflare", "netlify", "github pages",
    # max messenger
    "макс",
]
```

### NICHE_STOP (заказ НЕ наш, если есть 任何ое)
```python
NICHE_STOP = ["дизайн", "верстк", "макет", "облож", "объявлени", "кухон",
              "полиграф", "календар", "логотип", "иллюстрац", "3d",
              "монтаж видео", "фото", "видео", "тексты для", "копирайт",
              "перевод", "транскриб",
              # construction / documentation (FL.ru false positives)
              "акты скрытых", "кс-2", "кс-3", "dwg", "исполнительная документация",
              # landing pages (not our niche unless combined with our keywords)
              "лендинг", "продающ",
              # out-of-profile stacks
              "битрикс", "1с", "1с:", "битрикс24", "wordpress", "тильд",
              "tilda", "wix", "joomla", "drupal", "opencart", "modx"]
```

### CLOSED_MARKERS (закрытые заказы)
```python
CLOSED_MARKERS = [
    "исполнитель уже найден", "заказ закрыт", "в архиве",
    "исполнитель найден", "завершён", "завершен",
]
```

## Настройка откликов

### DEMO_LINKS
```python
DEMO_LINKS = {
    "beef": "https://openclaw70846.hostkey.in/beef/",
    "manicure_demo": "https://openclaw70846.hostkey.in/manicure-demo/",
    "portfolio": "https://openclaw70846.hostkey.in/portfolio/",
}
```

### Порядок моделей (fallback)
1. `meituan/longcat-2.5-preview:free`
2. `poolside/laguna-s-2.1:free`
3. `upstage/solar-mini4:free`
4. `stepfun/step-5-preview:free`

### Провайдеры
- **Nous Portal** (приоритет): `/root/.hermes/auth.json` → `providers.nous`
- **OpenRouter** (fallback): `/root/.secrets/openrouter.env` → `OPENROUTER_API_KEY`

## Добавление новых ключевых слов

1. Открой `/root/.hermes/scripts/scan_leads.py`
2. Добавь слово в `NICHE_WORDS` (если наш профиль) 或 `NICHE_STOP` (если чужой)
3. Учитывай склонения: substring match — "тильд" ловит "тильде", "тильда", "тильдой"
4. Перезапуск не нужен — скрипт читает конфиг при каждом запуске

## Управление через cronjob

```bash
# Список всех job
cronjob_manage(action="list")

# Приостановить
cronjob_manage(action="pause", job_id="8d557545a31e")

# Возобновить
cronjob_manage(action="resume", job_id="8d557545a31e")

# Запустить вручную
cronjob_manage(action="run", job_id="8d557545a31e")

# Обновить
cronjob_manage(action="update", job_id="8d557545a31e", ...)

# Удалить
cronjob_manage(action="remove", job_id="8d557545a31e")
```

## Troubleshooting

### Скрипт не находит новые заказы
- Проверь `seen.json`: `cat /root/kb/agents/research/data/seen.json | python3 -m json.tool | tail`
- Проверь `results.jsonl`: `tail -5 /root/kb/agents/research/data/results.jsonl`
- Проверь демон: `ps aux | grep agent.py`
- Проверь очередь: `cat /root/kb/agents/research/data/queue.jsonl`

### Демон не отвечает
```bash
# Перезапуск
pkill -f "agent.py --daemon"
sleep 2
/root/.hermes/installs/8a4017c4cabfe15f/environments/8586a6b426684d48afd4cfc1a23bda08/venv/bin/python3.14 /root/kb/agents/research/agent.py --daemon &
```

### Отклики не генерируются
- Проверь OpenRouter API key: `cat /root/.secrets/openrouter.env`
- Проверь Nous auth: `python3 -c "import json; print(json.load(open('/root/.hermes/auth.json'))['providers']['nous'])"``
- Проверь последний вывод: `ls -t /root/.hermes/cron/output/8d557545a31e_*.txt | head -1 | xargs cat`

### Много ложных срабатываний
- Добавь стоп-слова в `NICHE_STOP`
- Учитывай склонения (substring match)
- Проверь, что слово не является частью другого (например, "api" в "apis")

## Демо-прототипы

Для каждого нового заказа автоматически генерируется статичная HTML-страница-прототип и публикуется на VPS.

### Пайплайн
```
order → LLM generates HTML → docker cp → nginx → public URL → reply
```

### Файлы
- **Генератор**: `/root/.hermes/scripts/demo_gen.py`
- **Публикация**: `publish_kp.py` (docker cp → nginx-nginx-1)
- **URL**: `https://openclaw70846.hostkey.in/portfolio/prototypes/<order_id>.html`

### Требования
- Docker-контейнер `nginx-nginx-1` запущен
- Каталог `/usr/share/nginx/html/portfolio/prototypes/` существует
- nginx location `^~ /portfolio/prototypes/` настроен (добавлен 2026-10-19)

### Интеграция
В `scan_leads.py` после генерации отклика:
```python
from demo_gen import generate_and_publish
demo_url = generate_and_publish(title, brief, oid)
if demo_url:
    reply += f"\n\nСобрал прототип: {demo_url}"
```

## Демо-прототипы

Для каждого нового заказа автоматически генерируется статичная HTML-страница-прототип и публикуется на VPS.

### Пайплайн
```
order → LLM generates HTML → docker cp → nginx → public URL → reply
```

### Файлы
- **Генератор**: `/root/.hermes/scripts/demo_gen.py`
- **Публикация**: `publish_kp.py` (docker cp → nginx-nginx-1)
- **URL**: `https://openclaw70846.hostkey.in/portfolio/prototypes/<order_id>.html`

### Требования
- Docker-контейнер `nginx-nginx-1` запущен
- Каталог `/usr/share/nginx/html/portfolio/prototypes/` существует
- nginx location `^~ /portfolio/prototypes/` настроен (добавлен 2026-10-19)

### Интеграция
В `scan_leads.py` после генерации отклика:
```python
from demo_gen import generate_and_publish
demo_url = generate_and_publish(title, brief, oid)
if demo_url:
    reply += f"\n\nСобрал прототип: {demo_url}"
```

## Генерация демо-прототипов

Для каждого нового заказа генерируется статичная HTML-страница-прототип и публикуется в портфолио.

### Файлы
- **Генератор**: `/root/.hermes/scripts/demo_gen.py`
- **Обновление портфолио**: `/root/.hermes/scripts/update_portfolio.py`
- **Пересборка битых**: `/root/.hermes/scripts/fix_broken_prototypes.py`
- **URL**: `https://openclaw70846.hostkey.in/portfolio/prototypes/<order_id>.html`

### Грабли (важно)
- **Reasoning-модели рвут HTML.** `meituan/longcat-2.5-preview:free` тратит бюджет на
  размышления и возвращает ПУСТОЙ content с `finish_reason=length` — это давало
  «пустые страницы». Порядок моделей в `DEMO_MODELS`: solar-mini4 → laguna-s-2.1 →
  longcat → step-5 (reasoning — в конец).
- **Проверка полноты обязательна**: `html_is_complete()` требует `</html>` и `<body>`,
  иначе страница перегенерируется; если LLM ни разу не дал полный — детерминированный
  `fallback_html()`.
- **Права**: `docker cp` кладёт файл как `root:root`, nginx работает от `www-data` →
  без `chmod 644` отдаёт 403. Должен быть вызов `chmod` после публикации.
- **nginx**: нужен `location ^~ /portfolio/prototypes/` в HTTPS-сервере (порт 443),
  в HTTP-сервере работать не будет — там только редирект на HTTPS.

## Формат вывода Telegram

```
🆕 Новые заказы + готовый отклик

1. Название заказа
   Бюджет · платформа
   URL

   ✍️ Отклик:
   Текст отклика…

2. …

Всего новых: N
```
