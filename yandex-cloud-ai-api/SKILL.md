---
name: yandex-cloud-ai-api
description: "Use when integrating with YandexGPT or YandexART APIs."
version: 1.0.0
author: curator
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [yandex, api, gpt, art, image-generation, llm]
---

# yandex-cloud-ai-api

Integrate with Yandex Cloud AI services: YandexGPT (text generation) and YandexART (image generation).

## When to Use

- The user asks to generate text or images using YandexGPT/YandexART APIs
- A bot or automation needs AI-powered text or image generation
- Migrating from OpenAI to YandexGPT for cost or compliance reasons
- Building an image generation pipeline (e.g., artist agent, content creation)

## Authentication

Both APIs use the same auth pattern:

- **API Key**: Created in Yandex Cloud console (IAM → API keys). Starts with `AQVN`.
- **Folder ID**: The catalog ID where the service is activated (e.g., `b1ga9sfdlgsbhc20ds8r`).
- **Header**: `Authorization: Api-Key <key>`
- **Additional header for YandexART**: `OpenAI-Project: <folder_id>`

Store the key in `/root/.secrets/yandex_api_key.txt` (mode 600). Folder ID in `/root/.secrets/yandex_folder_id.txt`. Never hardcode in scripts.

## YandexGPT (Text Generation)

**Endpoint:** `POST https://llm.api.cloud.yandex.net/foundationModels/v1/completion`

**Request format:**
```json
{
  "modelUri": "gpt://<folder_id>/yandexgpt-lite",
  "completionOptions": {
    "temperature": 0.6,
    "maxTokens": 100
  },
  "messages": [
    {"role": "user", "text": "Your prompt here"}
  ]
}
```

**Response format:**
```json
{
  "result": {
    "alternatives": [
      {
        "message": {"role": "assistant", "text": "..."},
        "status": "ALTERNATIVE_STATUS_FINISHED"
      }
    ],
    "usage": {"inputTextTokens": "...", "completionTokens": "...", "totalTokens": "..."}
  }
}
```

**Available models:**
- `yandexgpt-lite` — fast, cheap, good for simple tasks
- `yandexgpt` — more capable, slower

**Pitfall:** The message field is `text`, not `content`. Using `content` returns a 400 error with "empty message text".

## YandexART (Image Generation)

**Working endpoint (SYNC, no extra roles needed):** `POST https://ai.api.cloud.yandex.net/v1/images/generations`

**Request format (uses `model` field, NOT `modelUri`):**
```json
{
  "model": "art://<folder_id>/aliceai-image-art-3.0",
  "prompt": "A cat in a hat, anime style",
  "size": "1024x1024"
}
```

**Response format:**
```json
{
  "created": 1792119246,
  "data": [
    {"b64_json": "<base64-encoded-image>"}
  ]
}
```

**Headers (BOTH required):**
- `Authorization: Api-Key <key>`
- `OpenAI-Project: <folder_id>`

**Available models:**
- `aliceai-image-art-3.0` — best quality, works out of the box
- `yandex-art/latest` — may require additional activation
- `yandex-art-lite/latest` — lighter version

**Pitfalls:**
- The async `foundationModels/v1/imageGenerationAsync` requires the `ai.imageGeneration.user` IAM role. If a key lacks that role and returns `Model art://... not allowed`, use the sync OpenAI-compatible endpoint instead — it works with no extra roles.
- The sync endpoint field is `model` (not `modelUri`) and requires the `OpenAI-Project` header — missing either one gives 400.
- When integrating YandexART into a backend, ALWAYS test the sync endpoint first — it works with a plain API key and folder ID, no IAM role setup needed.
- Max prompt length: 500 characters.
- Response is base64-encoded JPEG in `data[0].b64_json` — decode before saving.
- Decode with `base64.b64decode()` and save as `.jpg`.

## Python Example

```python
import requests
import base64

API_KEY = open('/root/.secrets/yandex_api_key.txt').read().strip()
FOLDER_ID = 'b1ga9sfdlgsbhc20ds8r'

# Text generation
resp = requests.post(
    'https://llm.api.cloud.yandex.net/foundationModels/v1/completion',
    headers={'Authorization': f'Api-Key {API_KEY}', 'Content-Type': 'application/json'},
    json={
        'modelUri': f'gpt://{FOLDER_ID}/yandexgpt-lite',
        'completionOptions': {'temperature': 0.6, 'maxTokens': 100},
        'messages': [{'role': 'user', 'text': 'Hello!'}]
    }
)
print(resp.json()['result']['alternatives'][0]['message']['text'])

# Image generation
resp = requests.post(
    'https://ai.api.cloud.yandex.net/v1/images/generations',
    headers={
        'Authorization': f'Api-Key {API_KEY}',
        'OpenAI-Project': FOLDER_ID,
        'Content-Type': 'application/json'
    },
    json={
        'model': f'art://{FOLDER_ID}/aliceai-image-art-3.0',
        'prompt': 'A cat in a hat, anime style',
        'size': '1024x1024'
    }
)
img_data = base64.b64decode(resp.json()['data'][0]['b64_json'])
with open('output.png', 'wb') as f:
    f.write(img_data)
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Wrong API key or missing header | Check key format and header name |
| 400 "empty message text" | Using `content` instead of `text` in messages | Change to `text` |
| 400 "invalid model schema. Available schemas: art" | Model URI not recognized | Use `art://` prefix, not `gpt://` |
| 403 "Model ... not allowed" | Missing `ai.imageGeneration.user` role | Use sync endpoint (not async) |
| 501 "unknown service" | Wrong endpoint for image generation | Use `ai.api.cloud.yandex.net/v1/images/generations` |

## Pricing

- YandexGPT Lite: ~0.02 ₽/1K tokens (input), ~0.15 ₽/1K tokens (output)
- YandexART: ~0.15-0.20 ₽ per image (1024x1024)
- Free tier: 1M tokens/month for YandexGPT, limited images for YandexART

## References

- Official docs: https://cloud.yandex.ru/docs/yandexgpt/
- API reference: https://cloud.yandex.ru/docs/yandexgpt/api-ref/
- YandexART: https://cloud.yandex.ru/docs/foundation-models/concepts/yandexart/
- `references/content-generation-example.md` — AI content plan generation with YandexGPT (SMM panel integration, prompt template, trends parsing)
