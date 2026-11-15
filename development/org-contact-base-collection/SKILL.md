---
name: org-contact-base-collection
description: "Use when building a B2B org contact base for outreach."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [lead-gen, contact-base, email, parsing, 2gis, yandex-maps, outreach, b2b]
    related_skills: [freelance-order-response, telegram-chat-base-collection, maps]
---

# Organization contact base collection (B2B, for outreach)

Build a base of organizations in a niche with contact details — primarily
**email** — for a cold-outreach campaign. Load when the order is «собрать базу
<ниша> России», «нужно N контактов с email», «база для рассылки по почте».

## When to Use

- The user needs N organizations with contacts (email/phone/site) in a niche.
- The base feeds an email campaign, so wrong or missing addresses cost the
  client real money and the count is the deliverable.

Don't use for: Telegram group lists (see `telegram-chat-base-collection`), or
plain geocoding/POI lookup by name (see `maps`).

## Always-on rules

1. **Measure coverage before promising a count.** Map catalogs carry email for
   only a small minority of organizations, so «соберу 5000 email из 2ГИС» is a
   promise you cannot keep. Harvest a sample, measure the real hit rate, and
   size the job from it — then quote the count the method actually yields.
2. **Two stages, always.** Stage 1 collects organizations plus their **websites**
   from the map catalogs. Stage 2 extracts emails **from those websites**. There
   is no single source that hands you a niche email list.
3. **Dedup by normalized domain (and by phone), never by name.** Chain clinics
   share a name across cities; the same firm appears in several catalogs.
4. **Report coverage, not just the total.** Say how many rows have email, how
   many have phone, how many have a site — the client needs to see the shape of
   the base, and the email count is what they bought.
5. **Open organizational contacts only.** Company email/phone for business
   correspondence is open data; do not add personal data of individuals. Say
   that the advertising-law side of the mailing is the client's responsibility.

## Coverage you can expect (measured)

Numbers from a real 605-row base of clinics harvested from 2GIS:

| Layer | Share |
|---|---|
| Organizations with a filled `E-mail` column in the catalog | **~3%** |
| Organizations with a website | **30–60%** |
| Emails extracted from a live website (homepage + contact pages) | **50–70%** |

Consequence: to deliver ~5 000 emails you need roughly **20 000–25 000
organizations across many cities**, not a single-city run. Say this to the
client up front; a «соберите по Москве и Питере» scope tops out around
1 500–2 000 emails.

## Procedure

1. **Scope.** Fix the cities/regions and the target email count. Derive the
   organization count from the table above and state it.
2. **Harvest organizations** (stage 1) with the maps agent — the 2GIS / Yandex
   harvester at `/root/maps-agent/` (trigger «запусти Крысу по <тема>», task file
   `tasks/task-N.md`). Its raw export carries the columns that matter: name,
   address, city/region, phone 1–3, `E-mail`, website 1–3, VK/WhatsApp/Telegram,
   category. Keep the raw CSV; it is the parent of every later count.
3. **Extract emails** (stage 2) from every row that has a website: fetch the
   homepage, follow links whose href contains a contact/about hint
   (`contact`, `kontakt`, `контакт`, `about`, `o-nas`, `info`), same-host only,
   and run the email regex over all fetched HTML. Use
   `scripts/harvest_emails.py` — it implements this with a thread pool.
4. **Filter junk** (see Pitfalls) and dedup by domain.
5. **Export** xlsx/csv: name, city, region, address, phone, email, site, socials,
   category. Keep a per-row `email_source` when a row has several.
6. **Report** totals, coverage per contact type, and where the harvest thinned
   out (JS-only sites, blocked hosts).

## Email extraction details

- Regex: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` — then filter.
- Send a real browser `User-Agent` and `Accept-Language: ru-RU`; many RU clinic
  sites serve a stub to default clients.
- Fetch homepage + up to ~3 contact/about pages per host. That is where the
  address lives; it is rarely on the homepage alone.
- Run with a thread pool (8–10 workers) and a per-request timeout (8–12 s).
  ~20 000 hosts is hours of wall time — run it in the background and append
  results per batch so a timeout does not lose the run.
- Many hosts are unreachable or JS-only from a plain HTTP client. Record them as
  `unreachable`, not as `no email`, and put them through the browser tool in a
  second pass if the count falls short.

## Single-org lookup: «найди email вот этой организации»

Тот же метод в миниатюре: один салон/клиника по названию + телефону + адресу, нужен
email. Порядок источников (идти по нему сверху вниз, не перескакивать):

1. **Свой сайт есть?** Смотреть поле «сайт» в карточке 2ГИС/Яндекс.Карт. Если там
   `dkd.su`, `dikidi.net/ru/profile/...`, `yclients.com`, соцсеть или link-in-bio —
   своего сайта НЕТ, и дальше email брать физически неоткуда (это же и повод для
   аутрича про сайт, см. `salon-site-outreach`).
2. **Карточки карт** — 2ГИС, Яндекс.Карты, Google Maps: телефон, соцсети, онлайн-запись.
   Email там почти никогда нет (та же ~3%).
3. **Платформа онлайн-записи** (DIKIDI: `curl dikidi.net/ru/profile/<slug_id>` отдаёт
   SSR — телефон, соцсети, цены; email только `info@dikidi.net`, это платформа).
4. **Агрегаторы-справочники** (zoon, flamp, kitabi, blizko, orgs.biz, big-book-med,
   ir-kutsk и подобные): грепать `mailto:` и regex по HTML — но их email считать
   кандидатом, не фактом (см. Грабли).
5. **Соцсети** (VK/OK/IG bio, Telegram-описание) — если открыты.

Останавливаться и докладывать «email нет, канал — WhatsApp/Telegram по номеру, email
только звонком» — нормальный и правильный результат. Выдуманный или непроверенный
адрес в базе для рассылки дороже отсутствия адреса: он даёт bounce и портит домен
отправителя.

## Грабли

- **Парсер `ru-maps-parser` требует `mcp>=2.2,<3`.** В свежем venv Hermes стоит
  `mcp 1.26.0`, где модуля `mcp.server.mcpserver` нет → `ModuleNotFoundError` → агент
  падает молча с `RuntimeError: parser did not start on :8001` (лог парсера показывает
  трейсбек, лог агента — только эту строку). Фикс: `pip install "mcp>=2.2,<3"` в тот venv,
  откуда запускается агент. Диагностика: запустить `ru-maps-parser.py` напрямую и прочитать
  трейсбек, а не полагаться на лог агента.
- **Директория `logs/` может отсутствовать** — если `mkdir -p` не выполнен до редиректа,
  лог пишется в никуда и выглядит как «процесс молча ничего не сделал». Создавать до запуска.
- **SMTP-порты может резать хостер, а не наш фаервол.** Проверять исходящие
  порты до настройки почты: если 25/465/587 таймаутят, а 443 работает — это
  фильтр провайдера. `ufw` при этом может показывать `allow (outgoing)`, что
  сбивает с толку. Тестировать python-сокетом с таймаутом, а не `bash /dev/tcp`.
- **Маскирование телефонов в выводе агента.** Hermes маскирует номера в терминале
  (`+890****0099`), но на диске они полные. Проверять целостность записывая в файл
  (`full_len` vs `masked`), а не читая глазами — иначе решишь, что база битая.
- **Колонки xlsx на русском** (`наименование`, `телефон 1`, `e-mail 1`, `веб-сайт 1`,
  `telegram 1`, `whatsapp 1`, `вконтакте`). Искать и русские, и английские имена колонок.
- **Patch несуществующей строки PostgREST молчит** (HTTP 200, `[]`) — для upsert нужен
  `Prefer: resolution=merge-duplicates`, иначе «запись не создалась» выглядит как успех.
- **Asset and library strings pass the email regex.** `jquery@2.2.2.js` and
  `jquery.mcustomscrollbar@3.1.3.css` are not addresses. Reject any candidate
  containing `sentry`, `@2x`, `wixpress`, `u003`, `example.`, `yourmail`, and any
  ending in an asset extension (`.png`, `.jpg`, `.webp`, `.svg`, `.css`, `.js`).
  Without this filter the raw hit rate looks inflated and the client gets bounce
  mail.
- **Promising a count the source cannot give.** The email column in map catalogs
  is ~3% populated; build the promise on the two-stage method, not on the
  catalog.
- **Counting raw rows across catalogs.** The same firm appears repeatedly; dedup
  by domain before reporting.
- **Treating `unreachable` as `no email`.** A blocked or JS-rendered site may
  well publish an address — mark it and retry through the browser.
- **Skipping the legal line.** State that the base holds open organizational
  contacts and that compliance of the mailing itself is the client's side.
- **Агрегаторный email без второго источника — это кандидат, а не контакт.**
  Справочники умирают (`ir-kutsk.ru` отдаёт 522, снапшотов в Wayback нет), а их
  строки живут в индексе поисковика годами. Признак тухлой записи: указанный там
  же соцхэндл не резолвится. Отдавать такой адрес можно только с явной пометкой
  «не подтверждён» + предложением проверить отправкой, а не как найденный email.
- **Проверить существование адреса пассивно нельзя.** SMTP RCPT с VPS не сделать
  (исходящий 25 режется — `Network is unreachable`), публичные валидаторы требуют
  ключ. Единственный честный тест — отправить одно письмо через REST-почтовик и
  посмотреть, не придёт ли bounce; не выдавать «адрес валиден» без этого.
- **Поле «веб-сайт» в карточке ≠ сайт организации.** `dkd.su` — короткий домен
  DIKIDI, и битый ID проекта на нём («некорректно указан ID проекта») — это
  отсутствие сайта, а не «сайт не работает». Для питча про сайт так и писать:
  «своего сайта нет, вместо него страница записи в чужом сервисе».

## Верификация адреса: живой ящик или догадка

Когда email взят из справочника-агрегатора (а не с сайта), его надо проверить
фактом, а не рассуждением. SMTP-проверка с VPS часто невозможна (хостер режет 25),
но **bounce через AgentMail работает** и даёт однозначный ответ:

1. Отправить письмо из `AGENTMAIL_INBOX` (`POST $AGENTMAIL_API_BASE/inboxes/{inbox}/messages/send`).
2. **Контрольный адрес обязателен**: параллельно послать на заведомо несуществующий
   `nope-<random>@gmail.com`. Он получает label `bounced` + DSN от
   `mailer-daemon@amazonses.com` за ~1 секунду.
3. Через 5–15 минут смотреть `labels` отправленного сообщения. `sent` без `bounced`
   при живом контроле = ящик существует. `bounced` = адреса нет, из базы выбросить.

Метод говорит только «ящик существует», не «его читает владелец». Для Gmail
письмо чаще уходит в спам, так что первый контакт всё равно лучше в мессенджер.

**Грабли AgentMail API:**
- В `.env` `AGENTMAIL_API_BASE` уже содержит `/v0` — путь собирать как `$BASE/inboxes/...`, иначе `404 Route not found`.
- Ключ обычно inbox-scoped без `inbox_read`: `GET /inboxes` и `/inboxes/{id}` дают `403 missing_permission`, а `GET /inboxes/{id}/messages` и `send` работают. Не считать это «ключ сломан».
- `message_id` вида `<...@email.amazonses.com>` в путь подставлять только через `urllib.parse.quote(mid, safe='')`.
- Историю bounce'ей и настройку рассылки вести по labels (`sent`, `delayed`, `bounced`, `complained`), отдельного поля delivery status в объекте сообщения нет.

## Холодная отправка: платформы не дают писать первым

Собрав базу, не рассчитывай отправить первым — это ограничение API, а не настройка:

- **Telegram:** бот не может начать диалог с пользователем, который ему не писал.
- **MAX:** то же — `404 dialog.not.found`, бот отвечает только в существующий диалог.
- **SMTP:** если в `.env` строки `EMAIL_SMTP_*` закомментированы — канал выключен.
- **WhatsApp:** нужен Business API аккаунт.

Реальные варианты: настроить SMTP (email), заставить клиента написать первым,
либо ручной обзвон по телефону. Скажи это клиенту до обещания «рассылку сделаю».

**Если SMTP-порты закрыты** (хостер режет исходящий 25/465/587, доступны только
80/443 — типично для зарубежных VPS), SMTP-блок в `.env` заполнять бессмысленно:
письма уходить не будут. Обходной путь — **REST API почтового сервиса через 443**.
Выбор сервиса решает **наличие верифицированного домена и карты**: Resend требует
домен и без него пишет только на свой адрес; Mailgun без карты — 5 «авторизованных»
получателей; **AgentMail работает без домена и без карты** и пишет кому угодно. Таблица
выбора, процедура для обоих и грабли — в `references/email-delivery-resend.md`.

## Холодная отправка: SMTP закрыт у хостера — только REST API

**Симптом:** `smtp.*` таймаутит, а `imap.*:993` и `:443` работают. Это исходящий
фильт хостера (Hostkey/NL режет 25/465/587/143/995), НЕ фаервол — проверять
`ufw status verbose` (у нас `default: allow (outgoing)`). Обход через VPN/SSH-туннель
не поможет, если фильт на уровне сети хостера.

**Вывод:** обычный SMTP не поднять. Работают только REST API почтовых сервисов
через 443. Выбор сервиса решает наличие домена и карты:

| Сервис | Домен | Карта | Пишет чужим адресам |
|---|---|---|---|
| Resend | обязателен | нет | нет — только на адрес аккаунта |
| Mailgun | обязателен | обязательна | нет — без карты только 5 «авторизованных» |
| **AgentMail** | **не нужен** | **нет** | **да** |

**AgentMail** (agentmail.to) — если нужен старт без домена и без карты: ящик
`xxx@agentmail.to`, отправка через `POST /v0/inboxes/{inbox}/messages/send`,
вложения как base64. Free: 10 писем/день, 300/мес. Ограничение нового аккаунта:
5 адресатов/час, 10/24ч (потом снимается). Ответы от уже писавших в лимит не идут.

**ГРАБЛИ:**
1. **Cloudflare перед многими API режет не-браузерный TLS-fingerprint.** Python
   `urllib`/`requests` → `403 error code: 1010`, а `curl` → 200. Лечится
   `pip install curl_cffi` и `requests.post(..., impersonate='chrome')`.
2. **Права ключа проверяй по делу, а не по догадке.** Один и тот же inbox-scoped
   ключ AgentMail может иметь `message_read`+`message_send`, но НЕ иметь
   `message_update` (метить письма) и `inbox_read`. Метод — прогнать матрицу
   зондов и записать коды: `GET /v0/inboxes/{id}` (inbox_read),
   `GET .../messages` (message_read), `POST .../messages/send` (message_send),
   `PATCH .../messages/{mid}` (message_update). Вывод по одному упавшему эндпоинту
   неверен: у ключа отсутствовал `inbox_read`, но `message_read` был — и ящик
   читается целиком, вместе с телами и вложениями. Отсюда: если метить письма
   нечем — веди «прочитанность» локально (seen-log), а не через labels.
3. **Идентификаторы с угловыми скобками надо URL-кодировать.** `message_id` в
   AgentMail выглядит как `<010...@email.amazonses.com>`; без
   `urllib.parse.quote(mid, safe='')` CloudFront отдаёт `400` с пустым телом и
   заголовком `x-cache: Error from cloudfront`, полностью маскируя настоящую
   ошибку (напр. `403 missing_permission`). Это выглядит как баг API.
4. **SMTP-фильт хостера — сначала проверь, где блок.** `smtp.*` таймаутит при
   рабочих `imap.*:993`/`:443` — значит режет хостер, не локальный фаервол;
   VPN и SSH-туннель не помогут. Решение: REST API почтовиков через 443.

## Next stage: is the org's site actually worth anything?

A base is also the input for selling **websites**: the pitch is built on which orgs
have no own domain, a dead site, or a visibly broken/crusty one. That audit is a
different procedure (host-level dedup, aggregator/platform classification, liveness
probe, mobile measurement over CDP, era markers, weighted ranking) — follow
`references/site-audit-ranking.md`. Two numbers from it belong in every such report:
**distinct hosts**, not filled `Веб-сайт` rows, and **rows with no own domain at all**
(aggregators and link-in-bio pages are not websites, and that count is the easiest
selling point to establish).

## Verification

- Email count comes from the extracted set, not from a catalog column.
- Every reported count is deduped by domain; junk-asset matches are excluded.
- Coverage percentages (email / phone / site) are stated with the total.
- A spot-check of 10 random rows: open the site and confirm the email is really
  there and not a library string.

## Support files

- `scripts/harvest_emails.py` — thread-pooled email harvester (homepage +
  contact pages, junk filter). Feed it a list of domains or a CSV with a website
  column; it prints hit rate and unique addresses.
- `references/site-audit-ranking.md` — auditing and ranking the base's websites
  (liveness, aggregator vs own domain, mobile breakage over CDP, era markers,
  weighted xlsx deliverable) for a "your site is bad / you have no site" pitch.
