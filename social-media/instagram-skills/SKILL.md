---
name: instagram-skills
description: "Use when creating or auditing Instagram content."
---

# Instagram Skills (sergebulaev/instagram-skills)

GitHub: https://github.com/sergebulaev/instagram-skills
MIT, 357 stars. 9 скиллов для Claude Code / Codex.

> **Полный разбор** (references, формулы, humanizer): `/root/kb/projects/instagram-skills.md`

## Быстрый старт

| Скилл | Что делает |
|-------|----------|
| `ig-caption-writer` | Капшен: хук в первых 125 символах + читаемое тело + 1 CTA |
| `ig-carousel-planner` | Карусель 2-10 слайдов: хук → ценность → payoff |
| `ig-hook-extractor` | Анализ вирального Reel: какую из 10 формул использует |
| `ig-hashtag-strategist` | 3-5 хэштегов (niche/mid/broad), не 30 |
| `ig-humanizer` | Удаление AI-следов: scrub → rhythm → add → self-check |
| `ig-content-planner` | План на неделю: Reels/карусели/сторис |
| `ig-repurposer` | LinkedIn/YouTube/X → Instagram карусель |
| `ig-profile-optimizer` | Аудит профиля: bio, highlights, сетка 9 |
| `ig-audience-insights` | Apify: сканирование хэштегов + статистика профиля |

## 10 формул хуков

| Код | Формула | Цель |
|-----|---------|------|
| IG1 | Number-First Result | saves |
| IG2 | Contrarian Truth | shares |
| IG3 | Relatable Cold-Open | comments |
| IG4 | Mini-Story Confession | comments, follows |
| IG5 | Listicle Carousel | saves |
| IG6 | Before/After | saves, follows |
| IG7 | Myth-Buster | shares |
| IG8 | Steal-This Framework | saves |
| IG9 | Pattern-Interrupt Reel | shares |
| IG10 | How-I Reel | saves, follows |

## 7 голосовых правил (запечены в каждый скилл)

1. Em dashes: кап ~1 на 100 слов. Один — не маркер. Не точка.
2. `..` или перенос строки как мягкая пауза.
3. Капитализация всех имен.
4. Предложения могут быть с маленькой буквы.
5. Избегать: leverage, fundamentally, streamline, harness, delve, unlock, elevate, foster.
6. Конкретные числа лучше прилагательных.
7. Одна идея на капшен. Первые 125 символов = хук.

## Humanizer V3 — 4 прохода

1. **SCRUB** — density-based (3+ маркера в параграфе = переписать). AI-словарь 2026, reveal bridges, staccato.
2. **RHYTHM** — только анти-униформность. Никогда не добавляет вариативность.
3. **ADD** — человеческие отпечатки: нечетное число + референт, именованная сущность, датированный факт.
4. **SELF-CHECK** — проверяет что Pass 1-3 не создали тех же паттернов.

## Публикация (Publora)

```
POST /create-post         → postGroupId
POST /get-upload-url      → S3 pre-signed URL
PUT  /upload (S3)         → 2-10 файлов по порядку
POST /update-post/:id     → status=scheduled + scheduledTime
```

Требует Business или Creator аккаунт. Media mandatory.

## Установка

```bash
git clone https://github.com/sergebulaev/instagram-skills.git
# Для Hermes:
cp -r skills/ ~/.hermes/skills/instagram-skills/
```