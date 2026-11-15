---
name: generative-media-api-generation
description: "Use when generating images/video via a provider API gateway."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [video, image, generation, api, gateway, async, billing, curl]
    related_skills: [seedance-video-generation, ffmpeg-video-concat, generated-client-text-quality]
---

# Generative media through a provider API gateway

## When to use

Generating video or images **programmatically** through a gateway that fronts
several vendors behind one OpenAI-compatible endpoint — as opposed to clicking
a web studio. Covers the class: find the right endpoint, price the request
before sending it, run the async job, verify the artifact, and know what the
catalog is lying about.

`seedance-video-generation` is the UI path (Dola.com); this is the API path.
For ffmpeg post-processing of the result see `ffmpeg-video-concat`.

## Read the selected provider's API contract first

Follow the vendor's actual documentation and model reference; do not infer a
route from a catalog label. Some gateways used in the examples publish
`/api-docs.md`; Higgsfield uses `https://docs.higgsfield.ai/`. Neither path nor
endpoint shape is universal.

The `/v1/...` routes, connection header, credit multipliers, and refund-on-poll
behavior below are provider-specific examples, not promises about every media
API. Verify authentication, pricing, request lifecycle, refunds, and retention
against the selected provider before executing.

A `400` can mean a wrong endpoint, an invalid body, unsupported parameters, or an
unavailable model. Read the machine-readable error and contract before deciding
which. Do not infer model absence from a generic error, or infer an endpoint
mistake from status alone.

For ad-system reviews, distinguish a web game builder, an Enterprise playable-ad
exporter, and a conventional image/video API, even under one brand. An image
endpoint called Ads Studio does not prove playable HTML export. Load
the ad-creative systems reference in the `third-party-tool-vetting` skill for
that review.

## Media is not chat: separate async endpoints

Chat completions are synchronous; image and video are **create → poll → download**:

```
POST /v1/<kind>/generations   -> {"request_id": ...}
GET  /v1/<kind>/{request_id}   -> {"status": "done", ...}   (poll)
GET  /v1/<kind>/{id}/content   -> the bytes
```

Two details that matter:

- **Save the `x-9router-connection-id` response header** on create. Some providers
  need it to continue the job later.
- **Download through the gateway's `/content` route, not the provider URL.** The
  provider's own URL is behind its cookie wall; the same-origin route is not, and
  it supports range requests.

## Image-to-video: the source frame must be a REAL https URL

Text-to-video takes only a prompt. Image-to-video adds `image`, and the provider
accepts **only** `{ "url": "https://..." }` — not a `dataUrl`, not a bare base64
string. A `dataUrl` is rejected at create time with
`Image input must have either 'url' or 'file_id' set`.

The URL must also be **fetchable by the provider**, which means the failures are
about the host, not about the JSON shape. Rule out each in order:

| Symptom | Cause |
|---|---|
| `Invalid argument: Image input must have either 'url' or 'file_id' set` | you sent `dataUrl` instead of `url` |
| `Fetching images over plain http:// is not supported` | URL is `http://` — must be `https://` |
| `could not reach the image host ... Ensure the URL is correct and reachable over HTTPS` | self-signed / untrusted cert, or the host blocks the provider |
| `Unsupported content-type encountered when downloading image` | the URL 302-redirects to something that is not an image |
| `Invalid PNG image` | the bytes at the URL are not a decodable image |

**A self-signed certificate is not accepted**, even when `curl -k` fetches it fine
locally. Serve the frame from a host with a valid public certificate.

The workaround when you control a domain: put the frame behind your own HTTPS
reverse proxy and pass that URL.

```bash
# 1. serve the frame from an origin with a valid cert
cp frame.png /usr/share/nginx/html/<dir>/
# add the location, reload, verify the bytes arrive intact
curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" \
  "https://<your-domain>/<dir>/frame.png"

# 2. pass that URL to the video endpoint
-d '{"model":"<video-model>","prompt":"...",
    "image":{"url":"https://<your-domain>/<dir>/frame.png"},
    "duration":10,"resolution":"720p","aspect_ratio":"9:16"}'
```

Verify the byte count at the URL matches your local file — a 302 to a login page
returns HTTP 200 with the wrong bytes and only fails later, at the provider.

For a vertical reel use `aspect_ratio: "9:16"`; the output comes back portrait
(e.g. 720×1280 at 720p). `duration` is **1–15 seconds, billed per started
second** — 10 s at 720p on a ×1 model is `10 × 175000 = 1,750,000` balance tokens.

## A capability flag is not proof of generation

A catalog entry that says a model can output images may still only write a
*prompt for* an image when asked to draw one — the response is prose, not an
image payload. Do not trust the flag or the `imageOutput` capability: ask the
model to actually produce the asset and inspect what came back. A "package"
(cover + video prompt + hashtags) is therefore normally a **two-model chain**,
never one model.

## Producing a whole package in one run

Drive it as a chain and **assert the schema** rather than eyeballing the JSON:

1. Ask the text model for **strict JSON** with named fields (`video_prompt`,
   `image_prompt`, `hashtags`). Validate all three are present and non-empty
   before using any of them — a truncated response still parses as JSON and
   silently drops the last field.
2. Render the cover from `image_prompt` with an image model.
3. Animate from the cover with a video model, passing `video_prompt`.
4. Give the small fields a token budget of their own: with a tight `max_tokens`
   the hashtags are the first thing truncated, and a partial hashtag is a broken
   hashtag. 600 is too tight, 900+ is safe.

State the target length in the prompt as well as in the body — a text model told
nothing will describe a different duration than the one you are paying for.

## Generating a SERIES: rotate every axis, not just the subject

A one-off package is a different job from a channel that publishes N of them. When
the deliverable is a series, **every axis of visual variation must rotate — a
hardcoded prompt field silently pins that axis forever.** Rotating only the
subject while the setting is a literal string in the template produces a feed of
different objects in identical scenery, and it looks fine on the first item.

Enumerate the axes and give each its own rotation list:

| Axis | Example values |
|---|---|
| subject | 55 car make/model pairs |
| setting | 30 environments (street, garage, desert, snow, port, terraces…) |
| action | drift, launch, cruise, burnout, reveal |
| camera | tracking, dolly-in, orbit, overhead, push-in |
| lighting | neon, sunset rim, blue hour, fluorescent, volumetric fog |

Pass the chosen value into the prompt as an instruction the model cannot drift
from — `Environment (use THIS exact setting): ...` — and **also list the recently
used values as an explicit do-not-repeat**, because the model will otherwise
default to the most stereotyped option for the niche.

**Detect a pinned axis by diffing the generated prompt FIELDS, not the titles.**
Pull the N most recent rows and compare the `image_prompt` / `video_prompt`
text: if a phrase dominates every row, that field is hardcoded in the template.
Titles are a weak signal — they are deliberately varied and will look diverse
while the scenery stays the same.

**Store the rotation state in the data, not in the code.** Persist the chosen
index per artifact so the next run can exclude it; a rotation that lives only in
a script's memory resets on every restart and repeats immediately.

See `references/series-variation.md` for the rotation recipe, the
same-shape-output detector, and the cron-wrapper contract.

## Choose the image model by the CONTENT it must render, not by its price

A zero- or low-coefficient image model looks free until it cannot produce the
asset. Probe it with **your actual subject** before quoting a saving:

```bash
# the subject the job needs, verbatim — not a neutral test prompt
for p in "a tuned Nissan GT-R on a neon street" "a Porsche 911 in the rain"; do
  curl -sS -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
    -d "{\"model\":\"$IMG_MODEL\",\"prompt\":\"$p\",\"size\":\"1024x1792\"}" \
    "https://<host>/v1/images/generations" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('error',{}).get('message','OK')[:80])"
done
```

Read the rejection text before assuming the whole prompt was the problem. A
provider may allow the scene and still refuse the **brand name inside it**, so
narrow the variable (drop the brand, keep the scene) rather than rephrasing
everything at once.

- **`The provider's content filter rejected this prompt`** — content policy, not
  capacity. Usually keyed to brand / trademark names in niche verticals (cars,
  fashion, alcohol). Generic phrasing passes; the specific subject does not.
- **`upstream provider is temporarily unavailable`** — overloaded vendor, **not**
  a filter and not a block. Retry; do not blacklist the model on one occurrence.

For a branded vertical the filter is a hard disqualifier: a model that cannot draw
the thing the deliverable is *about* saves nothing. State the difference between
"cheaper" and "usable for this subject" in the recommendation — a cheaper model
that returns no image is not a saving.

## Name the artifact after the object it depicts

When the cover is the input frame for image-to-video, derive the filename from a
`key_object` field in the package and slugify it:

```
key_object: "tuned skyline gtr"  ->  tuned-skyline-gtr.png  ->  tuned-skyline-gtr.mp4
```

Ask for `key_object` (2–4 words, lowercase) as a fourth field in the package
JSON. The slug ties cover, reel and any post text to one asset, so the pair is
recognisable in a directory listing without opening either file.

## Published byte count ≠ image dimensions

The size multiplier is charged on the **requested** size; the returned file is not
that size, and the file's own signature — not its extension or the JSON — tells
the truth. Gateways rename the bytes, so read the magic bytes:

```python
import struct
def dims(fn):
    d = open(fn, 'rb').read()
    if d[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', d[16:24])
    if d[:2] == b'\xff\xd8':                     # JPEG: scan for an SOF marker
        i = 2
        while i < len(d) - 9:
            if d[i] == 0xFF and d[i+1] in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack('>HH', d[i+5:i+9]); return w, h
            i += 1
    return None
```

Expected reality for a vertical reel: `1024x1792` returns **~940×1672** (ratio
0.5628, close to 9:16's 0.5625); a free model may return **768×1344** as JPEG
(ratio 0.5714). When the deliverable is a public thumbnail, check whether the
model writes the requested overlay text cleanly — cheaper models garble letters
and add stray signage, which is a bigger disqualifier than a resolution gap.

## Publish the frame from your own host, not a local one

Serving the source frame over plain `http://` or a self-signed cert fails at the
provider, and a throwaway local server dies the moment the script exits. Publish
it from the project's existing HTTPS origin (an nginx vhost with a real
certificate) and hand the provider that URL. Then **verify the bytes arrive**:

```bash
curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" "https://<domain>/<dir>/frame.png"
```

A 302 to a login page returns 200 with the wrong bytes and only fails later at
the provider. Check the byte count against the local file, not just the status.

## Always send the pricing parameters explicitly

A request that omits the parameters the rate table is keyed on is **billed at that
model's dearest rate** — the request is legal and the cost is a surprise. Compute
`units × rate[parameter] × coefficient` and show it to the user *before* the send.

- Default to **plan/dry-run, write only on an explicit opt-in** (`--apply`). A
  media run that is a fraction of a balance will not stay a fraction if someone
  forgets the flag. Do not infer "go" from an unrelated selector flag such as
  `--make <name>` / `--make-all` — that inference is how a dry-run silently
  produces paid output. Test the boundary on the real flag (`--make <name>` must
  print a plan and stop), and count what actually happened: print both an
  "attempted" and an "applied" number, or a dry-run reports 0 changed while
  having found work.
- **`GET /v1/balance`** returns the remaining balance in balance tokens — one
  call, no params. Print it before *and* after, and report the delta against your
  own estimate. A formula that matches the live debit to the token is worth more
  than the catalog's arithmetic, so verify it once and then trust it.

## Read-only calls that need a real HTTP client

A WAF in front of the gateway fingerprints the TLS/HTTP2 client and returns
`403 error code: 1010` for non-browser clients. A bare stdlib `urllib` request
fails on every route including ones that are public and unauthenticated. **Use
`curl`** (subprocess is fine) and keep a `pick_client()` that falls back to it —
the failure looks like a bad key or a bad URL and is neither.

## The general catalog lies about specialized models

`/v1/models` lists chat models. Image, video, audio, embedding and rerank models
carry a `kind` field and appear **only** in the per-kind listing
(`/v1/models/<kind>`), which is the only place their `billing` block is published.

So: grep the general list for `video`/`image` before concluding a model is absent,
then query the kind endpoint. The reverse also holds — the general list is not a
superset.

## Billing block semantics

The `billing` object is the price contract; read it rather than eyeballing a rate:

- `unit` — what the coefficient multiplies: `token`, `image`, `character`,
  `minute`, `second`, `request`.
- `base_tokens` — fixed charge per unit, present when the unit is not a token.
  **This is the cheapest variant, not the price of an arbitrary request.**
- `scales` — further multipliers applied before the coefficient (images:
  `quality` and `size`). A `high` quality tier is ×4 of base.
- `rates` — charge keyed by a request parameter (video: per second per
  resolution).
- `coefficient` — `{input, output}`. Outside chat both are equal and the charge
  uses `output`. A model at coefficient 0 costs nothing.

**Combo models carry no `billing` at all** — the id names a fallback chain and the
charge belongs to whichever member answered. Its cost cannot be predicted from the
catalog; measure `balance` before and after.

- **The provider prefix is part of the price.** A bare id and a prefixed id are
  different routes with different coefficients (one model differs ×4.5 vs ×0.5). The
  price published belongs to the exact id it is published under — call the id whose
  price you read.
- **`base_tokens` is the floor, not the price.** It is the cheapest variant of the
  request; an arbitrary quality/size costs a `scales` multiple of it. Price the
  variant you actually asked for.

## anymodel.org image models (current, 2026-11-01)

The catalog is live — read `/v1/models` and filter for `kind:image`, or grep for
`image` in the general list. Known image models, with price per the `billing`
block (unit = image):

| model id | tariff | coefficient |
|---|---|---|
| `cx/gpt-image-2` | 100,000 × quality (low×0.25, medium×1, auto×1, standard×1, high×4, hd×4) | 0.9375 |
| `cx/gpt-image-2.5` | 100,000 × quality (low×1, medium×1, auto×1, standard×1, high×2, hd×2) | 1.25 |
| `flow/nano-banana` | 100,000 × 1.5 | 1.5 |
| `flow/nano-banana-lite` | 100,000 × 0.75 | 0.75 |
| `flow/nano-banana-pro` | 100,000 × 3 | 3 |
| `xai/grok-imagine-image` | quality ladder above | 1.733333 |
| `xai/grok-imagine-image-quality` | quality ladder above | 4.333333 |
| `am/flux.2-klein-4b` | 100,000 × 0 | 0 |

Read your own `GET /v1/models` before choosing — the catalog is a snapshot and
drifts. Every id in the catalog belongs to the exact id it was published under;
a bare `gpt-image-2` is a different route with a different coefficient.

**Default for a text-to-image agent: `cx/gpt-image-2` (1024×1024, quality=medium).**
`nano-banana` variants are 9:16-friendly and sometimes cheaper per image, but
profile your real subject against the default first — a zero- or low-coefficient
model looks free until it cannot render the asset.

## Prompt pipeline for image generation

1. Build the prompt from the task as a whole: `topic + description + title +
   hashtags` (artists-agent / vk-reel-agent pattern). short/generic prompts fail
   a diffusion model — the prompt must name the subject, setting and mood.
2. Pass the prompt with `size` and `quality` explicitly — a request that omits the
   rate-keyed parameters is billed at the model's dearest tier (a `medium`
   request for `cx/gpt-image-2` costs 100,000 × 1 × 0.9375 = 93,750 tokens).
3. Save the returned image bytes, never the URL, and record `model`, `size`,
   `quality`, `prompt`, `timestamp` in the slot record.

## Verify the artifact, not the job status

`status: done` says the job finished — assert the bytes:

```bash
file out.png                                   # expect PNG/JPEG magic
python3 -c "import struct;d=open('out.png','rb').read();print(struct.unpack('>II',d[16:24]))"
```

A gateway may serve a JPEG under a `.png` name. Measure requested vs delivered
size: `1024×1024` often returns ~940×1024 — that gap is billed, not free.
## Pitfalls

- **Classify a media `400` from the provider's error and contract.** Check the
  documented endpoint, input shape, parameters, and model availability rather
  than treating status alone as a diagnosis.
- **Use the documented generation endpoint.** Do not assume a chat endpoint
  accepts asynchronous video jobs, or that every provider uses the same routes.
- **Omitting the rate-keyed parameters bills the maximum.** Always send
  `duration`/`resolution`/`size`/`quality` explicitly.
- **`edits`/`extensions` routes are flat-billed** at the model maximum regardless
  of what the body claims — the duration field there describes the *input* clip.
- **A failed job refunds the charge, but only on the poll that first reports the
  failure.** Keep polling a job you have given up on; abandoning it forfeits the
  refund.
- **A 403 with a Cloudflare error code is a client fingerprint, not a permission
  problem.** Switch to `curl`; never report it as a bad key.
- **Do not treat `/v1/models` as the complete catalog** — it omits media models
  entirely.
- **A capability flag does not mean the model generates.** Ask for the asset and
  inspect the response before building a workflow on the flag.
- **Rotating only the subject pins the setting.** In a series, a literal string in
  the prompt template is an axis that never varies — check every field, not just
  the one you remembered to rotate.
- **The model copies the topic verbatim into the title field.** Passing
  "car + action" as the topic makes the action land in the title. Pass only the
  subject as the topic, and strip action words defensively from the title field.
- **A cron wrapper must forward `sys.argv` and the child's exit code.** Dropping
  argv silently ignores `--dry-run` and spends the money; dropping the exit code
  makes a failed run report `ok` and deliver nothing.
- **Re-assert the output schema after editing a prompt template.** A richer
  template can stop returning a field the pipeline requires, and the run still
  exits 0 — the failure surfaces much later as a missing value.
- **A low coefficient is not a recommendation.** A zero-cost image model can be
  unusable for the job — probe it with the real subject. A content-filter
  rejection of the brand name is a hard disqualifier for a branded vertical.
- **`upstream provider is temporarily unavailable` is load, not a verdict.**
  Retry before drawing a conclusion about the model.
- **Do not trust the extension or the JSON for the artifact's format and size.**
  Read the magic bytes; a gateway may serve a JPEG under a `.png` name.
- **Publish the source frame from an existing HTTPS host.** Plain http, self-signed
  certs, redirects and non-image bytes each fail separately at the provider, and a
  local throwaway server is gone before the job runs.
- **Never quote a cost, count or balance from a note instead of the API.** Any
  figure written to disk is stale the moment it is written, and a stale balance
  makes every downstream "can we afford this" calculation wrong while still
  looking like a considered answer. Query the live endpoint, and say the number
  came from it; if you are quoting a remembered value, say that too.

## References

- `references/gateway-api-patterns.md` — worked example: probing a gateway, the
  balance-before/after check, per-model rate table, and the catalog-drift caveat.
- `references/series-variation.md` — generating a varied SERIES: rotating every
  visual axis (subject, setting, action, camera, light), the same-shape-output
  detector, title/description policy enforcement, and the cron-wrapper contract.
