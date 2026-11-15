---
name: motion-sites-landing
description: "Use when building a premium landing from studio prompts."
version: 1.0.0
author: Мария
license: MIT
metadata:
  hermes:
    tags: [landing, motionsites, prompt, single-file, ai-generation]
---

# MotionSites: премиум-лендинг одним файлом

Метод сборки продающего сайта из готовой студийной спецификации: ИИ получает
инженерное ТЗ реального премиум-сайта + анкету проекта и отдаёт один `index.html`.

## When to Use

Нужен продающий лендинг для продукта или клиента: премиальный вид, анимации,
параллакс, без ручной вёрстки. Также — когда нужна быстрая визуальная обёртка
поверх уже работающего продукта.

## Откуда брать промты

Библиотека: `https://motionsites-prompt-collection.vercel.app/search` (646 промтов,
все бесплатны). Официальный каталог: `https://motionsites.ai`.

**Промты лежат в JS-бандле**, не в HTML. Извлекать так:

```bash
curl -sS -L https://motionsites-prompt-collection.vercel.app/search | grep -oE 'assets/index-[^"]+\.js'
# → https://motionsites-prompt-collection.vercel.app/assets/index-<hash>.js
curl -sS -L <bundle> -o ms.js
```

В бандле объекты вида `{id:\`x\`,slug:\`n-name\`,title:\`Name\`,prompt:\`...\`}`.
**Грабли парсинга:**
1. Промты в **бэктиках** (`prompt:\`...\``), не в одинарных кавычках — парсер по
   `'` вернёт 0 символов.
2. Минифицированный JS — искать через `re.search`, а не `re.match` (между полями
   бывает много текста).
3. Экранирование: `\n`, `\'`, `\`` — разворачивать обратно.

Готовый скрипт: `/root/tire-fit/scripts/extract_motion_prompts.py` (извлекает все
промты + строит индекс по размеру).

## Схема промта

Три части одним сообщением:

```
1. Управляющая шапка — 8 правил (см. build_prompt.py → HEADER)
2. Анкета проекта — ниша, бренд, заголовок, тексты, картинки, контакты, цены
3. Промт шаблона — спецификация с motionsites
```

Собирает `scripts/build_prompt.py <slug-шаблона>`.

## Восьмь правил шапки (ядро метода)

1. **Один файл** — `<!DOCTYPE html>` … `</html>`, библиотеки через CDN.
   React/Vite из спецификации → Tailwind CDN + GSAP CDN + vanilla JS.
2. **Дизайн 1-в-1** — сетка, отступы, цвета, параллакс, анимации не упрощать.
3. **Типографика** — шрифты из спецификации (не случайные), `clamp()` для кириллицы.
4. **Полная замена контента** — `lang="ru"`, никакого Lorem ipsum и чужих цен.
5. **Короткие шаблоны** — Hero дословно + ещё 4 секции в том же стиле.
6. **Картинки** — локальные пути → Unsplash по теме, ни одной битой ссылки.
7. **Кнопки соцсетей** — Telegram/WhatsApp, SVG-иконки, в шапку и подвал.
8. **Полный код** — без пропусков и «остальной код здесь».

## Генерация через API

Готовый скрипт: `/root/tire-fit/scripts/gen_landing.py <model> [slug] [out]`.

**Грабли:**

1. **Cloudflare режет не-браузерный TLS** — `urllib`/`curl` → `403 error code: 1010`.
   `curl` иногда проходит, но ненадёжно. Решение: `curl_cffi` с
   `impersonate='chrome'`.
2. **`finish_reason: length`** — модель упирается в `max_tokens` и файл обрывается
   на середине. Ставить запас (64k), а в парсере — `find('```')` вместо `index()`,
   чтобы не падать на незакрытом блоке.
3. **Обрыв без `</html>`** — дописать закрывающие теги (`close_html()` в скрипте),
   иначе файл битый.
4. **Unsplash режет датацентровые IP** — часть ссылок мёртвая. Проверять каждую
   ссылку запросом перед вставкой (`scripts/find_images.py`).

## Модели

Нужна большая генерация кода. Проверено на anymodel: `ag/claude-sonnet-4-6`,
`cx/gpt-6.1-sol`, `ds/deepseek-v4-pro` — все с 1M ctx.

## Проверка

1. Открыть в браузере, посмотреть первый экран.
2. `document.querySelectorAll('section').length` — секции на месте.
3. Мобильный эмулятор 390px и 320px: `scrollWidth > innerWidth` → false.
4. `document.querySelectorAll('img')` — картинки есть (иначе правило №6 не сработало).
5. Браузерная вкладка **сбрасывается в `about:blank` между вызовами** — все замеры
   делать в ОДНОМ `js()`-вызове, иначе получишь пустой DOM и белый скриншот.

## Деплой

```bash
docker cp <file> nginx-nginx-1:/usr/share/nginx/html/<dir>/
docker exec nginx-nginx-1 nginx -s reload
```

Location в nginx: `root /usr/share/nginx/html; try_files $uri $uri/ /<dir>/index.html;`

## Пример результата

`/tire-fit-landing/` — 7 секций, 54 КБ, тёмный дизайн, фото механика на фоне,
форма заявки, тарифы. Сгенерировано за 242 сек, 21 116 токенов вывода.
