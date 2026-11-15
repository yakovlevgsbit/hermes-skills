# AnyModel Gateway API (AI video + image)

OpenAI-compatible gateway. Base URL and credentials live in the operator's secrets file —
never hard-code keys in scripts; read them from the operator's env file.

## Endpoints used by a pipeline

| Purpose | Endpoint |
|---|---|
| Text / prompt generation | `POST /v1/chat/completions` |
| Image generation | `POST /v1/images/generations` |
| Video generation | `POST /v1/videos/generations` |
| Video status | `GET /v1/videos/{request_id}` |
| Video download | `GET /v1/videos/{request_id}/content` |
| Balance | `GET /v1/balance` |

## Text generation

```json
{"model": "<model-id>", "messages": [{"role":"user","content":"..."}],
 "max_tokens": 1400, "temperature": 0.4}
```

- Parse the assistant content and extract JSON from the first `{` to the last `}`.
- Some models return the answer in `reasoning` with `content: null` — fall back to it.
- Reasoning tokens count against `max_tokens`; leave headroom or the JSON gets truncated.

## Image generation

```json
{"model":"<image-model>","prompt":"...","size":"1024x1792",
 "response_format":"b64_json"}
```

- `size` values are a fixed enum; the returned pixel dimensions are often NOT the
  requested ones (request `1024x1792` -> receive ~941x1672). Read the actual dimensions
  from the file, not the request.
- `b64_json` response — decode before saving. Some models return JPEG despite a `.png`
  filename; detect the real format from the magic bytes.
- Cost scales with a size multiplier and a quality multiplier, so the biggest size is the
  dominant cost in a package. Check the price before assuming a bigger image is better.

## Video generation

```json
{"model":"<video-model>","prompt":"...","duration":10,"resolution":"720p",
 "aspect_ratio":"9:16","image":{"url":"https://..."}}
```

- Polling is required; the create call returns only a `request_id`.
- Status values: `pending` -> `done` | `failed`.
- The returned video URL is on the provider's CDN — download it immediately, do not treat
  it as durable storage.

## Errors

- `upstream provider is temporarily unavailable` — capacity, not a content rejection.
  Retry with a delay (3 attempts, ~20s apart).
- Content filter rejection — a policy block. Nothing is charged. Rephrase or switch model.
- Cloudflare blocks `urllib` with `error 1010`; use `curl`.
- Rate limiting — rotate across models in the prompt's model list and back off.
