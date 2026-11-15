# AI Video Generation APIs

When the panel needs to generate video content (not just publish it), these are the viable providers and their constraints.

## Kling AI

**Domain:** `api-singapore.klingai.com` (old `api.klingai.com` → 404 on all endpoints)

**Auth:** `Authorization: Bearer <API_KEY>` (new key format: `api-key-kling-l-...`)

**Endpoint:** `POST /v1/videos/text2video`

**Models (verified):**
- `kling-v2-6` — Standard, 5s/10s
- `kling-v3` — Standard, 3–15s
- `kling-v2-5-turbo` — Turbo, 5s/10s

**Models discontinued:** `kling-v1`, `kling-v2-master`, `kling-v2-1-master`, `kling-v1-6`, `kling-v2-1`, `kling-v2-5`, `kling-3.0`, `kling-2.0`, `kling-2.1`, `kling-2.5`

**Pricing:** Pay-per-generation. No free API tier. The 66 free credits/month are web-only and do NOT carry over to API. Account balance must be positive.

**Request shape:**
```json
{
  "model_name": "kling-v2-6",
  "prompt": "A cinematic tracking shot along a sunlit coastal road",
  "duration": "5",
  "aspect_ratio": "9:16"
}
```

**Response:** Async — returns `task_id`, poll with `GET /v1/videos/text2video/{task_id}`.

## Higgsfield AI

**Domain:** `api.higgsfield.ai`

**Auth:** `Authorization: Key <KEY_ID>:<KEY_SECRET>`

**Endpoint:** `POST /bytedance/seedance-2.0/text-to-video` (and other model paths)

**Models:** Seedance 2.5, Seedance 2.0, Kling 3.0, Kling 3.0 Turbo, MiniMax H3, Wan 3.0 Prime, and more (24+ models total)

**Pricing:**
- Free tier: playground only, no API access
- Starter: ~$19/mo (200 credits)
- Pay-as-you-go: from $0.084/sec (Kling 3.0 Standard)
- Sign-up bonus: $15 balance (requires card verification)

**No free API tier.** The playground is free for evaluation but API calls require payment.

## General rules

- **Always check account balance before promising generation.** A positive balance is the only way to verify a key works end-to-end. An API that returns 400 for "model not supported" is reachable — one that returns 401 is a key problem.
- **Model names change frequently.** The marketing names on the website (e.g., "Kling 3.0") may differ from the API parameter values (e.g., `kling-v3` or `kling-v2-6`). Always verify with a live call.
- **Async pattern is universal.** All providers return a task_id immediately and require polling. Build the poll loop into the worker, not the web request.
- **Free tiers are evaluation-only.** No major video generation provider offers a permanently free API tier. Free credits are either web-only or require card verification for a small sign-up bonus.
