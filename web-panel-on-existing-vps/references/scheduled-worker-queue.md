# Scheduled Publishing Worker (DB-as-Queue)

A panel whose core promise is "publish at time T" needs a second process: a
worker that wakes on a timer, finds what is due, and performs the publish. This
is the shape for that worker when the panel already has a SQL database and there
is no message broker on the host.

## Architecture: the table IS the queue

Do not add Redis/Celery for this. A `scheduled_posts` table with a `status`
column is a complete, durable, inspectable queue — and it survives a restart with
no extra machinery:

```
pending -> publishing -> uploaded
                     \-> retry  -> (back to pending when due)
                     \-> failed (terminal, after N attempts)
```

Two systemd units, one per process, both `Restart=always`:

| Unit | Runs |
|---|---|
| `panel` | the web app (uvicorn on a loopback port) |
| `worker` | the poller (`worker.py`, no port) |

The worker polls on an interval (`SMM_POLL_SECONDS=30` style env var) and does
nothing between cycles. A heartbeat log line every ~10 minutes keeps the journal
from looking dead.

## Claim atomically, or two runners double-post

Selecting the due rows is NOT the claim. Between the SELECT and the UPDATE a
second worker (or a retry of the same one) can pick up the same row. Claim with a
conditional UPDATE and check `rowcount`:

```python
rows = conn.execute(
    "SELECT * FROM scheduled_posts WHERE status='pending' AND scheduled_at <= ? "
    "ORDER BY scheduled_at LIMIT ?", (now, batch)).fetchall()

claimed = []
for r in rows:
    cur = conn.execute(
        "UPDATE scheduled_posts SET status='publishing' "
        "WHERE id = ? AND status = 'pending'", (r["id"],))
    if cur.rowcount == 1:          # we own it; 0 means someone else won
        claimed.append(r)
conn.commit()
```

This is what makes the worker safe to restart, safe to run twice by accident,
and safe to scale later without rewriting anything.

## Retry with backoff, then park it as failed

A transient failure (network, provider 5xx, a token refresh) must not lose the
job, and a permanent one (the source file is gone, the account is disconnected)
must not retry forever. Both come from one counter:

- `attempts` — incremented per try.
- `next_attempt_at` — set on failure; the claim step also promotes rows whose
  `next_attempt_at` has passed back to `pending`.
- Backoff 1 → 5 → 15 minutes, then `failed` with the reason in `error_msg`.

**A terminal `failed` row must carry the reason.** `error_msg` is what turns "it
did not work" into a fixable report; without it the operator has a red badge and
no lead. Store the human-readable exception string, and put the traceback behind
an env flag (`SMM_DEBUG=1`) so the log stays readable.

**Validate before the retry loop, not inside it.** A request the app already
rejected as invalid (a bad enum value, a missing field) should be a 400 at
creation, not something the worker retries three times. Only failures that could
plausibly resolve on a retry belong in the retry path.

## Rate limits are a scheduler concern, not a provider concern

A per-network daily cap lives in a settings row (JSON keyed by network) and is
checked by the worker *before* each publish. When the cap is hit, reschedule the
row an hour out rather than failing it — the job is still wanted, just not now.
Count "used today" from the rows already marked `uploaded` today, so the counter
is derived state and cannot drift from reality.

## Share the publish CODE between panel and worker, not just the format

If the web app has a "publish now" button and the worker publishes on a timer,
both must call the **same function in the same module** — a `publish.py` that
ows credential loading, the file lookup, the privacy decision and the provider
call. Two copies of that logic drift, and the drift shows up as "the button works
and the schedule does not" (or the reverse), which is a miserable bug to chase
because both paths look correct in isolation.

The web route becomes a thin wrapper: validate, call `publish_to_youtube(...)`,
mirror the outcome onto any matching schedule row. The worker calls the identical
function. One fix lands in both paths.

## Both processes must be able to bring the schema up

The worker and the web app share one SQLite file. If only the web app runs the
`ALTER TABLE ... ADD COLUMN` migrations at boot, then starting the worker first
(or alone, after a restart) crashes it on `no such column` and systemd restarts
it into the same wall. Put the migration in a function in the shared module and
call it from **both** entry points — start order must never be a failure mode.

```python
# publish.py
def ensure_schema():   # idempotent: PRAGMA table_info, ALTER only what is missing
    ...

# main.py (at import) and worker.py (in main(), before the loop)
ensure_schema()
```

## Operator controls that make the queue usable

- **Publish-now**: `POST /schedule/<id>/publish-now` sets `status='pending'` and
  `scheduled_at=now`, so the next poll picks it up. Do not publish inline in the
  request — the worker is the only writer, which keeps the status machine honest.
- **Surface the state in the UI**: status badge, the error text, the attempt
  count, and a link to the published artifact. A queue whose failures are
  invisible is a queue the operator stops trusting.

## Verify with a row dated in the past

The end-to-end test that proves the whole loop, in one pass: schedule a post with
`scheduled_at` one minute in the *past*, then poll the API every 10s and watch the
status walk `pending → publishing → uploaded`. That exercises the claim, the
publish, the status write and the UI read without waiting for real time.

Then test the failure path the same way — point a schedule at a video whose file
is NOT on disk and watch `retry` (with the reason) climb to `failed` after N
attempts. Confirm the reason string is stored, not just the terminal status.

**Confirm the artifact on the provider, then clean up.** A `uploaded` status is
the worker's own claim; read the item back from the provider API to prove it
exists, note the privacy state it actually landed in, then delete the test rows
and any test artifact. State in the report what was left behind.
