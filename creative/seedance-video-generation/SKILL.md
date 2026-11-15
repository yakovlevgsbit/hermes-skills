---
name: seedance-video-generation
description: "Use when generating AI videos from text or images."
---

# Seedance 2.5 — AI Video Generation

Source: YouTube tutorial (Yevgeniy Kovalenko)

> **Полный разбор**: `/root/kb/projects/seedance-video-generation.md`

## What It Is

Seedance 2.5 — топ-3 AI модель для генерации видео. До 30 секунд, встроенный звук, высокое качество.

Leaderboard: #3 (после MiniMax H3 и H3 Max).

## Dola.com Platform

Dola.com — AI-платформа с доступом к закрытым моделям через Skills:

```
Dola.com
├── Чат-интерфейс (как ChatGPT)
├── Skills — загружаемые инструкции
│  ├── Загрузка файла (.txt, .md)
│  ├── Активация через /slash command
│  └── Расширение возможностей модели
├── Генерация видео (text-to-video, image-to-video)
└── Скачивание результата
```

## How Skills Work

Skill — файл с инструкциями, который загружается в AI-платформу:

```
1. Создать/скачать Skill-файл
2. Загрузить в Dola.com (Upload Skill)
3. Активировать в чате (/skill-name)
4. Модель следует инструкциям
```

## Workflow

```
1. dola.com → Login → Continue with Google
2. Подтвердить 18+
3. Skills → Add → Upload Skill
4. Загрузить файл Seedance 2.5
5. New Chat → /seedance
6. Промпт или изображение
7. Ждать ~1-2 мин
8. Скачать видео (~4-5 МБ)
```

## Text-to-Video

```text
Описание сцены, действия, камеры, света
→ Seedance 2.5 → Видео до 30 секунд со звуком
```

## Image-to-Video

```
Загрузить фото + промпт движения
→ Seedance 2.5 → Анимированное видео
```

## Key Patterns

1. **Skills as extensions** — загружаемые инструкции расширяют модель
2. **Free tier access** — закрытые модели через платформы с Skills
3. **Prompt + Skill combo** — Skill задаёт формат, промпт — запрос
4. **Platform hopping** — один интерфейс для разных моделей
5. **Skill editing** — любой может создать/изменить Skill

## Итог

Seedance 2.5 через Dola.com + Skills. Ключея идея: платные модели доступны бесплатно через агрегатор с загружаемыми инструкциями.

Самое ценное для Георгия:
- **Skills паттерн** — как расширять модели без кода
- **Бесплатный доступ** — к закрытым моделям
- **Свои Skills** — можно создавать инструкции под задачи
- **Image-to-Video** — анимация изображений