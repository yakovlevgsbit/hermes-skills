---
name: max-inbound-longpoll-support-triage
description: "Use when reading inbound MAX/Telegram messages for triage."
version: 1.0.0
author: Hermes Agent (Мария)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [max, support, triage, long-poll, llm]
    related_skills: [max-messenger-api, generated-client-text-quality]
---

# Reading inbound MAX messages (support triage)

## When to use

Building anything that reads what clients sent a bot — support triage, intake,
lead capture — or when `/updates` looks broken. Extends the send-side
`max-messenger-api` skill (which only covers outbound).

## A MAX bot CAN read inbound — two working paths

Clients often assume a bot can only send. It can read:

1. **`GET /updates`** — long-polling, **accumulating**. Returns
   `{"updates":[],"marker":N}`. Empty is NORMAL: it yields everything new
   since subscription, not a backlog. Persist `marker` across runs or every run
   re-reads the same window.
2. **`GET /messages?chat_id=<id>&limit=N`** — chat history. This is what makes a
   fresh agent useful immediately instead of blind until the next message.

Both use the same auth as sending: raw token, no `Bearer` (see
`max-messenger-api`).

## MAX has no forums / topics

The chat is flat. If the user talks about "topics 11/13", those exist only in a
**Telegram** forum group, not in MAX. Do not hunt for a topics endpoint.

## Telegram bot whose webhook is already taken

If the bot is already wired into another system (Hermes, n8n), `getUpdates`
returns `{"ok":true,"result":[]}` forever — not an error, just a busy webhook.
You still have options: `getChat` works (confirms membership and `is_forum`),
and the other system can hand you the messages (e.g. read them back through
that system's own session search). Check `getChat` first to learn what the bot
can actually do.

## Never let the LLM write the client-facing text

This is the important one. When asked to classify a support message, the model
will happily **invent business facts** — asked "are you open Sunday and how much
is a brow correction" it answered *"yes, we're open"* plus a price, none of
which it knows. Sending that to a real client is a live-business error.

Split the job:
- LLM picks the **category** only.
- The **reply text** comes from a fixed template keyed by category, containing no
  facts about the business.
- Record `reply_source` in the output so a fabricated reply is detectable.

Add a pre-LLM heuristic for obvious spam (2+ markers) so junk never costs a call.

## Free LLM routers hand out reasoning models

`openrouter/free` (the router alias) may serve a reasoning model that spends the
entire token budget on `reasoning` and returns `content: null` with
`finish_reason=length`. That reads as a broken classifier. Fix: pin a concrete
non-reasoning model, give a generous `max_tokens`, and **skip a model that
returns no content** instead of treating it as an answer. Also handle 429 by
falling through to the next candidate.

## Verify the send path without spamming a client

Send to the **owner's own DM**, read the message back with `/messages`, then
`DELETE /messages?message_id=<mid>`. That proves outbound works end to end while
touching no client. Only then consider a real reply, and keep real sends behind
an explicit flag (e.g. `--send`), with dry-run as the default.

## Deduplicate across runs

Hash `mid + text` into a `seen` file. A message pulled from both `/updates` and
`/messages` history would otherwise be triaged twice. Filter `is_bot` first so
the bot's own posts never enter the queue.
