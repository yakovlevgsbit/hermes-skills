# Live surface — verified endpoints, ports, real responses

Сверено вживую. Не утверждай про сервис по документации — проверь этим же probe.

## Веб-домен `openclaw70846.hostkey.in` (nginx vm)

| Путь | Реальный ответ | Примечание |
|---|---|---|
| `/` | **200** (302 → `/login?next=%2F`) | `location /` → `:9119` (живой Hermes). Раньше был **502**: проксировал на мёртвый `:18789`. |
| `/portfolio/` | 200, ~43 КБ | публичный лендинг |
| `/beef/` | 200, ~112 КБ | статика mini-app; `HEAD` → **501** (нет `do_HEAD` в backend) |
| `/web-assistant/` | 200 | лендинг + UI |
| `/manicure-demo/` | 200, ~10 КБ | booking-демо (форма: `#datePick`, `#duration`, `#publish`) |
| `/n8n/` | 200, HTML-шелл | веб-морда n8n |

## beef API (`/beef/api/` → `127.0.0.1:8101`)

| Роут | Ответ без ключа | Вердикт |
|---|---|---|
| `/api/healthz` | 200 `{"ok":true}` | **открыт по дизайну** — не ассерть 401/403 |
| `/api/stock` | 200, данные остатков | **открыт по дизайну**, НЕ утечка: фронт зовёт его на `DOMContentLoaded` до идентификации |
| `/api/cabinet` | 200 (название, логотип, `owner_assigned`) | **открыт по дизайну**, НЕ утечка: брендинг должен отрисоваться до авторизации |
| `/api/supabase/**` | **403** | прокси с service_role-ключом. Был открыт (аноним читал `app_users`) — закрыт проверкой роли |
| `/api/cabinet/users` | 403 | закрыт корректно |
| `/api/cabinet/actions` | 403 | закрыт корректно |

Backend: systemd `beef-app.service`, порт **8101**. `:3900` — чужой контейнер (`vs-test`).

> Оба «публичных» роута — не находка. Проверяй, что они **достижимы** (иначе приложение
> ломается), а не что они закрыты. Настоящая дыра была в catch-all прокси
> `_supabase_proxy()`: привилегированный ключ + ноль проверок актора.

## n8n (`/n8n/`)

- `/n8n/healthz` → 200 JSON `{"status":"ok"}` — единственный честный health-check.
- `/n8n/workflows`, `/n8n/executions` → 200, но **HTML-шелл веб-морды**, не REST. Ключ в `/root/.secrets/n8n.env` (`N8N_API_KEY`).
- Стоковый `/workflows/{id}/executions` на этой машине ведёт себя иначе — проверяй тело ответа.

## Supabase

- `SUPABASE_URL` из `/root/.secrets/supabase.env`.
- `GET /rest/v1/?select=count&_count=1` → **400 `PGRST100`** (нужен FROM). Не баг продакшена — особенность PostgREST. Рабочий вызов: `?select=id&limit=1` по таблице.

## OpenRouter

- `/api/v1/models` → 200 **без ключа** — не годится как проверка ключа.
- Проверяй ключ через `/api/v1/key` (401 без ключа, 200 с ключом).

## Интерпретатор

`python3` в PATH = bundled-питон Hermes без `requests`. Бери `/usr/bin/python3` (проверяй `import requests`).
