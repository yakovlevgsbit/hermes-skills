# Content Generation with YandexGPT

Example: AI-powered content plan generation for SMM panel.

## Architecture

```
SMM Panel → [webhook] → n8n:
  1. Receives request (account, niche, period, audience)
  2. Code node: builds prompt with niche + trends + audience
  3. YandexGPT: generates content plan (topics, hashtags, descriptions)
  4. Code node: formats to JSON
  5. Returns slots → panel saves to SQLite
```

## Prompt Template

```
Ты — SMM-специалист. Создай контент-план на {period_days} дней для аккаунта в нише "{niche}".

Целевая аудитория: {audience}
Аккаунт: {username} ({network})

Тренды в нише (используй их в плане):
{trends_json}

Требования:
1. Для каждого дня — 1 пост
2. Каждый пост должен быть разным: рецепт, лайфхак, обзор, история, FAQ
3. Используй тренды в темах и хештегах
4. Хештеги — 5-8 штук, релевантные нише
5. Описание — 1-2 предложения, с призывом к действию

Формат ответа (строго JSON):
{
  "plan_name": "Название плана",
  "slots": [
    {
      "day": 1,
      "topic": "Тема поста",
      "hashtags": "#тег1 #тег2 #тег3",
      "description": "Описание поста"
    }
  ]
}

Только JSON, без пояснений.
```

## Parsing Response

```python
text = result["result"]["alternatives"][0]["message"]["text"]
text = text.strip()
# Strip markdown code fences if present
if text.startswith("```"):
    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
if text.endswith("```"):
    text = text[:-3]
text = text.strip()
plan = json.loads(text)
```

## Trends Integration

YandexGPT does not have built-in web search. For trend-aware generation:
- Parse trends from VK/TikTok separately (hashtags, topics, challenges)
- Include trends JSON in the prompt
- Update trends daily/weekly via scheduled parser

## VK Trends Parser

Uses VK `newsfeed.search` API with user token to collect trending hashtags and topics.

**Steps:**
1. Query `newsfeed.search` with cooking-related keywords
2. Filter hashtags against a cooking whitelist
3. Extract first-line topics that contain cooking keywords
4. Also query `video.search` for trending video titles
5. Save to `trends.json`

**Rate limit:** max 3 requests/second. Use `time.sleep(0.34)` between calls.

**Output format:**
```json
{
  "vk": {
    "hashtags": ["рецепты", "готовимдома", ...],
    "topics": ["topic1", "topic2", ...],
    "video_titles": ["title1", ...]
  }
}
```

**Common pitfall:** Without cooking-keyword filtering, the parser returns irrelevant hashtags (e.g., #alias, #лайф). Always whitelist hashtags and filter topics by keywords.

## Standalone Script Example

See `/root/.hermes/cache/scratch/content_plan_generator.py` for a complete working example that:
- Reads account info from SQLite
- Calls YandexGPT with trend context
- Saves generated plan back to SQLite
- Returns JSON for n8n integration