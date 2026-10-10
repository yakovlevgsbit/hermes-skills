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

## 5. Cost & reliability

- Free-tier models rate-limit per model; keep a fallback chain (see the
  research agent's `MODEL_FALLBACKS` pattern) so one 429 doesn't drop a job.
- Reasoning models (e.g. step-*) dump their thinking into `content` and can
  exhaust the token budget before answering — put non-reasoning models first
  for pure generation, and cut text before the last `Ответ:` marker if you must
  use one.
- Log prompt + output + model + cost per call from day one; it's how you debug
  and how you prove value to the client.

## Selling as a template

Deliver: the prompt, a runnable script (text→JSON→image), a test set of inputs
with expected outputs, and a short README on swapping models. A demo that turns
one input into a finished post + image sells the order. Never claim a model does
something you haven't run.
