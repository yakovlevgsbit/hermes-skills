---
name: ai-video-pipeline
description: Use when generating/publishing AI video to a channel.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ai-video, youtube, prompt-engineering, automation, content-pipeline]
    related_skills: [generative-media-api-generation, reels-publisher, hermes-cron]
---

# AI Video Pipeline

Generating AI video content end-to-end: prompt the LLM, generate a cover, generate the
video, publish to a platform. Used for YouTube Shorts/Reels channels.

## When to use

- Building or debugging an AI video generation pipeline (cover + video + publish).
- Writing prompts for video models that keep coming out with identical backgrounds.
- Publishing AI-generated video to YouTube / Instagram / TikTok via API.
- Automating a content channel on a schedule or a queue.

## Architecture: the pipeline shape

```
rotate subject -> LLM pack (title + prompts + tags) -> queue table
              -> generate cover -> generate video -> publish -> mark done
```

**Split the work by cost and reversibility.** Text generation is nearly free and
reversible — never let a failure there cost you a video generation. Generate the
expensive artefact only after the free steps are committed to the queue. On a
platform publish failure, keep the artefact and mark the row `quota_exceeded` or
`pending_publish` rather than `failed`, so a retry does not re-generate it.

**Use a status column as the queue.** `pending -> generating -> ready -> published`
plus `failed` and `quota_exceeded`. Each transition is one idempotent UPDATE.

**Idempotency key = the human-facing topic, not a derived slug.** LLM output for a
"key object" is unstable across runs, so any slug derived from it differs between
runs and the dedupe check silently never fires. Store a normalized topic and match
on that.

## Pitfalls (these each cost real time)

1. **A hard-coded setting in the prompt defeats subject rotation.** If the prompt says
   "night scene, neon, sakura", every video gets that background regardless of subject.
   Rotate the SETTING (environment) as well as the subject, and pass the chosen setting
   into the prompt explicitly. Check the artefact's prompt field afterwards to confirm it
   actually changed — otherwise the fix is cosmetic.
2. **The LLM copies your whole topic string into the title field.** If the topic is
   "Nissan GT-R idling, engine rumbling, then revving once", the title comes back the
   same. Derive the title by splitting the topic on action/scene markers, and validate the
   returned value against a regex of action words before accepting it.
3. **A generic-object regex is a trap.** Match the WHOLE string, never a substring: a
   pattern like `(sports?\s+car|...|car)` also matches "Mazda RX-7" and rewrites a good
   tag into garbage. Same rule for normalization functions — test that valid values pass
   through unchanged.
4. **A cron wrapper must propagate the child's exit code.** `subprocess.call(...)` alone
   loses it; if you don't `sys.exit(rc)`, a crashed pipeline reports `ok` and the failure
   arrives as silence. Also forward `sys.argv` or `--dry-run` is silently ignored and a
   "dry run" spends real generation budget.
5. **YouTube has a per-day upload cap that a service account cannot raise.** When the
   upload API returns a limit error, the video is already generated — mark the row
   `quota_exceeded`, keep the file, and retry later. Return the INNER error message from
   the provider, not the bare `HTTP 400`, or the log tells you nothing.
6. **A model's declared capability is not a guarantee it can render.** Chat models with
   an image-output capability may return a *textual prompt* instead of an image. Verify
   with a real request before building on it.
7. **A free/cheap model may silently filter your content.** Brand names, place names and
   stylistic terms are common triggers. Test each candidate with the actual subject
   matter before adopting it — a model that rejects your core subject is unusable however
   cheap it is.
7a. **`youtube.readonly` reads any public channel, not just the token's own.** The token's
   channel ownership only gates writes (uploads, playlists). Reuse one stored OAuth token
   for cross-channel research, competitor scans and trend analysis instead of minting a
   credential per job.
8. **`urllib` gets blocked by CDN WAFs** on many API gateways (Cloudflare `error 1010`).
   Use `curl` for provider API calls.
9. **Ask for an explicit duration in the prompt.** Video models default to 30-45s when
   you say "short"; state the exact length or the artefact is the wrong format.
10. **A provider often needs a real HTTPS URL, not a local path**, for image-to-video
    input. Publish the frame behind a valid TLS host and pass that URL.
11. **Model-returned JSON can be incomplete.** Validate required fields before writing to
    the DB, and retry once when a field is missing — the fix is usually one line in the
    prompt (e.g. an omitted field the contract requires).
12. **A hosted DB key is usually CRUD-only; schema changes need a human.** A
    service-role key can insert and select but not `ALTER TABLE` — adding a column means
    pasting the DDL into the provider's SQL editor. Two consequences: (a) the API answers
    a missing-column write with `400` and a `PGRST204 "Could not find the 'X' column"`
    body, so treat that exact body as a schema-drift signal, not an app bug; (b) make the
    write conditional — probe the column once, and skip the field when it is absent so the
    pipeline still runs on the old schema instead of hard-failing every row. Keep the
    migration SQL next to the pipeline so it is discoverable.
13. **A UNIQUE index on a derived slug turns a repeated subject into a 409.** Once the
    slug comes from a canonical name rather than a free-form model field, two different
    topics can produce the same slug and every repeat publish dies with
    `duplicate key value violates unique constraint`. Drop the unique index to a plain one
    and dedupe in code (see the idempotency rule above) — an index is not a substitute for
    a dedupe check that actually runs.

## Publishing rule of thumb

When the channel has an established style, read a few recent published items and encode
the pattern as an explicit rule rather than letting the model improvise. Title and
description conventions are per-channel decisions, not model defaults.

## References

- `references/anyvideo-provider-api.md` — provider gateway API: models, endpoints,
  request/response shapes, retryable errors.
- `references/prompt-engineering-for-video.md` — prompt structure, environment/action/camera
  rotation, consistency constraints, common failure modes.
- `references/youtube-data-api-v3.md` — OAuth token handling, resumable upload, quota
  limits, error meanings, verification.
- `references/model-tariff-registry.md` — single-source model tariff registry: where
  coefficients come from, price formulas, per-script fallback, refresh/verification.
