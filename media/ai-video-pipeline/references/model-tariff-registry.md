# Model tariff registry

## Why a registry

Tariffs (coefficient x base x size/quality multiplier) drift, and every pipeline script
that hard-codes a rate goes stale separately. When two scripts disagree about the same
model you get silently wrong cost estimates and no error to catch them. Make one module
the source of truth and have every script read from it.

## Where the numbers come from

Fetch the catalogue from the provider API rather than transcribing it:

| Kind | Endpoint shape | What to read per model |
|---|---|---|
| text | `GET /models` | `billing.coefficient.input` |
| image | `GET /models/image` | `coefficient`, `base_tokens`, `billing.scales.{size,quality}` |
| video | `GET /models/video` | per-resolution rate, coefficient |

Cache to a local JSON with a short TTL (an hour is fine) so the scripts do not each hit the
API, and so a cold start still prices a job. Re-fetch on demand and expose a `--report`
mode so you can eyeball the whole table in one command.

## Price formulas

- **text**: `(prompt_tokens + completion_tokens) * coefficient`
- **image**: `base_tokens * scales.size[size] * scales.quality[quality] * coefficient`
  (return `None` for an unknown size — it is an enum, and the requested pixel dimensions
  often are not what you get back)
- **video**: `rate_per_sec[resolution] * duration * coefficient`

## Per-script fallback

Keep a literal fallback value for each constant so a script still runs when the registry
cache is missing or the API is down:

```python
try:
    from tariff_registry import get_registry
    rate = get_registry().video_rate_per_sec(MODEL, RES) or FALLBACK_RATE
except Exception:
    rate = FALLBACK_RATE
```

Do NOT delete the local literal. It is the difference between "prices from the API" and
"crashes on a cold start".

## Verify against a known figure

After wiring the registry, assert the totals you already confirmed by hand. A registry
that silently returns a stale or misparsed coefficient is worse than a hard-coded number,
because it looks authoritative. Print the priced breakdown for one full job and compare it
to the amount actually charged.

## Rule of thumb for choosing a model

Choosing a model is rarely "which is smarter" — it is "which one does not break this
specific task". A free model that filters your core subject matter is unusable no matter
how cheap. Price is a secondary sort after the capability/filter check passes; when the
cheap model is within a few percent of the expensive one on a large artefact, the difference
is noise and the reliable model wins.
