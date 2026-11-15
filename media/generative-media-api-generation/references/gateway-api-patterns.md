# Gateway API patterns — worked example

Depth behind `generative-media-api-generation`. Concrete probe sequence, the
balance-before/after check, and the catalog-drift caveat.

## 1. Prove the client works before blaming the key

A WAF can 403 every route regardless of the key. Test with an endpoint that is
public and unauthenticated, so a failure there isolates the client:

```bash
curl -sS -m 20 "https://<host>/v1/models" | head -c 200   # expect JSON, not "error code: 1NNN"
```

`error code: 1010` (or similar) is a Cloudflare TLS/HTTP2 fingerprint block —
switch to `curl`, do not regenerate the key.

## 2. Fetch the reference doc, then work from it

```bash
curl -sS "https://<host>/api-docs.md" -o /tmp/api-docs.md
wc -c /tmp/api-docs.md
grep -niE 'video|balance|image' /tmp/api-docs.md | head -40
```

A `404` whose body names a doc URL is the gateway telling you where the truth
lives. Do not infer endpoints from the host name or from the chat surface.

## 3. Enumerate what actually exists

```bash
KEY=$(grep '^API_KEY=' /path/to/secrets.env | cut -d= -f2)

# general list — chat models only
curl -sS -H "Authorization: Bearer $KEY" "https://<host>/v1/models" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['data']), 'models')"

# specialized kinds — these carry the billing blocks
for k in image video tts stt embedding rerank; do
  printf '%-10s ' "$k"
  curl -sS -H "Authorization: Bearer $KEY" "https://<host>/v1/models/$k" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('data',[])))"
done
```

Dump each kind's `billing` to a file rather than re-deriving it by hand — the
coefficient, `rates` and `scales` are the price contract and transcribing them
introduces silent errors.

## 4. Price a job and measure the debit

```bash
# before
curl -sS -H "Authorization: Bearer $KEY" "https://<host>/v1/balance"
# -> {"balance": 122922550, ...}

# create (save the header for continuations)
curl -sS -D /tmp/h.txt -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<video-model>","prompt":"...","duration":5,"resolution":"480p"}' \
  "https://<host>/v1/videos/generations" -o /tmp/job.json
grep -i 'x-9router' /tmp/h.txt

# poll until terminal
curl -sS -H "Authorization: Bearer $KEY" "https://<host>/v1/videos/<id>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status'))"

# after — the delta is the real charge
curl -sS -H "Authorization: Bearer $KEY" "https://<host>/v1/balance"
```

Compare the delta to `units × rate × coefficient`. When they agree, the formula
is validated and later jobs can be quoted from it with confidence; when they do
not, trust the balance and find the missing `scales` multiplier.

## 6. Where the money actually is in a chain

When one deliverable needs several models, price each leg before deciding where
to optimize. The legs are usually wildly unequal, and the instinct is to optimize
the wrong one.

Worked example — a vertical reel package (cover + video prompt + hashtags):

| Leg | Typical balance tokens | Share |
|---|---|---|
| text (prompts + hashtags) | ~500 | 0.03% |
| cover image | ~1.6 × 10^5 | ~8% |
| 10 s 720p video | ~1.75 × 10^6 | ~92% |

The video dominates by two orders of magnitude. Choosing a cheaper text model
changes nothing — the spread between the cheapest and dearest text model is worth
a rounding error against the video. Spend the optimization effort on the video
parameters (duration, resolution) and the cover model, and stop there.

**Then gate the cover choice on content, not cost.** The cover leg is small in the
bill and large in the artifact: it is the frame the video is generated from and
the thumbnail in the feed. Worked example on a branded vertical (cars):

| Cover model | Cost | Size | Brand names |
|---|---|---|---|
| free low-cost model | 0 | 768×1344 | **content filter rejects them** |
| mid model | ~1.6 × 10^5 | ~940×1672 | works |

The free option saves ~8% of a reel and produces **no image at all** for the
subject. Cheaper is not a saving when the deliverable does not exist.

Report the per-leg cost when the user asks which model to pick. "The cheap one
works" is not an answer to "which should I use" when the choice is worth 0.03%
— and "the cheap one is cheaper" is equally not an answer when it cannot render
the subject.


A gateway's catalog changes between sessions: a list of N models one month is a
different N the next, and models appear or vanish. Any figure written into a
notes file is stale the day after it was written.

- Re-query the API before quoting a count, a price, or a model id.
- Record the query date next to the figures so a stale number is detectable.
- Say explicitly when a quoted number came from the API versus from an older
  note — quoting a remembered balance is the failure that makes every downstream
  cost calculation wrong.
