# Quota-aware idempotent sender (rate-limited new accounts)

Use when the sending channel is a brand-new account with recipient quotas: the
first sends succeed, then the provider returns a rate-limit response naming the
limit and the lift time. Do not abandon the channel — batch it.

## 1. Journal first

A local CSV is the only source of truth for what was sent.

Fields: `sent_at, company, email, subject, message_id, status, detail`.

Rules:
- Write a row for every real attempt outcome (`ok` or `fail`), with the provider's
  detail. A failed send is logged as `fail` and is **not** an "already sent" marker —
  retry it.
- Never derive "sent" from the inbox. A key without read permission, or an empty
  inbox because nobody replied, makes an inbox-checking sender re-send the whole
  list.

## 2. Compute the quota from the journal, not from memory

```
sent_24h = count(journal rows where status == "ok" and sent_at >= now - 24h)
quota    = DAILY_LIMIT - sent_24h
todo     = [r for r in base if r.email not in journal_ok_emails]
batch    = todo[:max(0, quota)]
```

Compute the window from the journal itself; do not cache "what I think I sent".

## 3. Stop on the limit

If the provider returns a rate-limit response, stop the batch immediately and
record nothing for the remaining addresses. Print the provider's message verbatim
— it carries the exact lift time, which the report needs.

## 4. Cron the batch

Hermes cron, `--no-agent`, stdout delivered locally:

```
hermes cron create "30 9 * * *" --name <job> --script <wrapper>.py \
  --interpreter <venv python> --no-agent --deliver local
```

- The script must be a real file under `~/.hermes/scripts/` — cron refuses
  symlinks (realpath escape).
- Keep the wrapper tiny: it re-executes the real script under `/root/<project>/`
  so the job launches from anywhere.
- Verify by running the wrapper directly with the same interpreter before trusting
  the schedule; `hermes cron tick` fires due jobs and `hermes cron runs <id>` shows
  attempts.

## 5. Report cadence, not just the total

Tell the user: batch size, cadence, remaining count, and the date the quota lifts
(read it from the provider's rate-limit message). A 135-address base at 10/day
clears in ~13 days — say that up front so the number does not read as a stall.

## 6. Probe permissions before building anything

Probe each endpoint and record the codes; never infer from one failure.

| Probe | Permission |
|---|---|
| `GET /v0/inboxes/{inbox}` | `inbox_read` |
| `GET /v0/inboxes/{inbox}/messages` | `message_read` |
| `POST /v0/inboxes/{inbox}/messages/send` | `message_send` |
| `PATCH /v0/inboxes/{inbox}/messages/{mid}` | `message_update` |

If `message_update` is absent, read-state (seen-log) must be local. If
`message_read` is present, the inbox can be polled for replies.

`message_id` values contain angle brackets — URL-encode them
(`urllib.parse.quote(mid, safe='')`) or the CDN returns a bare `400` that masks the
real error. See `org-contact-base-collection` for the delivery-side pitfalls.
