---
name: prompt-engineering
description: "Use when an order needs LLM prompts or text/image output."
version: 1.0.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [prompts, llm, claude, gemini, gpt, text-generation, image-generation, json-output, промт]
---

# Prompt Engineering (production prompts)

Build and sell production-grade prompts: system prompts, variable templates,
stable JSON output, and text→image pipelines. Load when an order is about
"промт", "генерация текстов/картинок", "системный промпт", or structured LLM output.

## Typical order shape (from FL.ru)

> Системный промпт + шаблон запроса с переменными (возраст, имя, тема).
> Методика — пошаговый алгоритм внутри промпта. Вывод в JSON.
> Картинки через Gemini API.

That is three deliverables: prompt, JSON contract, image call. Bill them as one
pipeline, not three tiny tasks.

## 1. System prompt structure

Order the sections so the model can't skip steps:

```
# Role — one line, who it is.
# Goal — the single output it must produce.
# Inputs — the {{variables}}, what each means.
# Method — numbered algorithm (see below).
# Output contract — exact JSON schema + rules.
# Language — always answer in <lang>, regardless of input language.
# Hard rules — what it must never do (no invention, no extra keys).
```

Keep the method as **numbered steps**. Models follow numbered steps far more
reliably than prose paragraphs.

## 2. JSON output that doesn't break

- Give the **exact schema** with types and an example, not a description.
- Say: *return only the JSON object, no markdown fence, no commentary.*
- Validate on your side anyway — parse with a fallback (strip ```json fences,
  take the first `{...}` block) before trusting it.
- For strictness prefer the provider's native JSON mode / tool-use / response
  schema over prompt-only enforcement.
- Test edge cases: empty input, very long input, weird characters, non-target
  language. These are what break naive prompts in prod.

## 3. Variable templates

Expose inputs as named placeholders (`{{name}}`, `{{age}}`, `{{topic}}`) and
document each. Provide a filled example so the client sees the mapping. Never
let free text from one variable inject instructions — wrap user values and
state they are data, not commands (prompt-injection guard).

## 4. Text → image (Gemini / others)

- Build the image prompt from the *generated text*, not raw user input, so the
  picture matches the copy.
- Keep a style block (medium, lighting, palette, composition) as a separate
  reusable fragment.
- Handle: NSFW/safety refusals, empty results, and rate limits gracefully.
- Store the image prompt alongside the text JSON so output is reproducible.

## 6. Generator prompts: the planner emits prompts, the generator emits content

Some pipelines have one LLM that must do two things: author a plan **and** produce
the final text/image/video. Split them. The planning agent is a separate prompt,
and for every dated item it emits a **generator prompt** written into a schema
column (`prompt`) for a downstream generation model (text, image, video).
The generation model is then given only the prompt plus the stored source data —
never the planning prompt.

Reasoning: an LLM that both plans and generates drifts from the brief when it
writes final copy. The planner picks the *what*; the generator gets the *how*.

### Format-specific generator prompts

Build the generator prompt from the item's `format`, `idea`, `goal`.
Do not reuse one prompt for every format — each generation model needs a
different shape of instruction.

| Item `format` contains | Generator prompt rule |
|---|---|
| `video` | 10 seconds, vertical 9:16. Cinematic/short style, concise, no on-screen text, no markers, specific and detailed. |
| `картинка` / `карточка` / `изображение` | 9:16 image for a generation model. Concrete visual, no lists, no explanations. |
| otherwise (post / article / review / story) | Plain text content. Concise brief: topic, goal, concise style, text only, no headings/markers. |

### Example generator prompts

**Text.** `Gотовь текст-контент (пост/статью/опрос/серию сторис) под тему {idea}, цель {goal}. Стиль: лаконичный в духе целевой аудитории. Промпт для модели: только текст, без заголовков и маркеров.`

**Video.** `Готовь промпт для видео (10 сек, вертикальный 9:16). Тема: {idea}. Цель: {goal}. Стиль: короткий, сценографический, без текста на кадре. Промпт для модели: конкретно, подробно, без маркеров.`

**Image.** `Готовь промпт для генерации картинки 9:16 (фото/иллюстрация). Тема: {idea}. Цель: {goal}. Промпт для модели: конкретный визуал, без списков и пояснений.`

### What to store vs generate

- Store: the generator prompt (it is reproducible and can be re-run), plus the
  item's `idea`, `goal`, `format`, `date`, `hashtags`.
- Do NOT store a second prose copy of the prompt; keep it as a single field so a
  downstream generator can read it directly.
- Store the prompt per item, not one shared prompt for the whole plan.

## 7. Delivering generation output to a client

## Selling as a template

Deliver: the prompt, a runnable script (text→JSON→image), a test set of inputs
with expected outputs, and a short README on swapping models. A demo that turns
one input into a finished post + image sells the order. Never claim a model does
something you haven't run.
