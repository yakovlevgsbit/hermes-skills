---
name: max-messenger-api
description: "Use when calling the MAX messenger platform API."
version: 1.0.0
metadata:
  hermes:
    tags: [max, messenger, api, bots, automation]
---

# MAX Messenger API

## When to Use
Any call to platform-api2.max.ru — reading or pinning group messages, editing or deleting messages, sending DMs, checking chat info — for the MAX booking bot or any other MAX bot. Also load this when an MAX call returns a 401 (check the Bearer-prefix pitfall first) or a permission error on pin/delete (check chat-admin rights).

## Sending: the recipient is a QUERY parameter, never a body field

This is the single biggest time sink. Putting `user_id`/`chat_id` in the JSON body returns `400 proto.payload "Unknown recipient"` even when the token and the id are both correct — the error reads like a bad-recipient problem and sends you chasing ids.

```
✅ POST /messages?user_id=121119600        body: {"text": "..."}
✅ POST /messages?chat_id=-79638499377264  body: {"text": "..."}
❌ POST /messages   body: {"user_id": ..., "text": "..."}   → Unknown recipient
```

The body carries message content only. Sending to a user returns a synthetic `recipient.chat_id` (a `dialog` chat) in the response — keep it if you later need to read that DM history via `GET /messages?chat_id=<dialog id>`.

Rate limit: 30 rps on platform-api2.max.ru.

## Bots cannot open a dialog with a user who never wrote to them

`POST /messages?user_id=<client>` returns **`404 {"code":"dialog.not.found"}`** when no personal dialog exists yet — verified 2026-10-05 against a client who only ever spoke in the group chat. The same token successfully DMs a user who has an existing dialog.

So bot-to-client notifications need a fallback: on `dialog.not.found`, post into the group instead. Anything that assumes "DM the client" works out of the box on a fresh audience will silently fail.

How to tell "no dialog" from a real failure: the HTTP code is 404 **and** `code == "dialog.not.found"`. Other 404s mean a bad path.

## Reading and deleting

- `GET /messages?chat_id=<id>&to=<unix_ms>` → `{"messages": [...]}`; `to` bounds results from that timestamp onward, useful for incremental reads.
- `GET /messages?message_ids=mid1,mid2` or `GET /messages/{messageId}` → single message.
- `DELETE /messages?message_id=<mid>` → 200. Deleting a bot's own message needs no special flag; deleting someone else's does.
- `GET /chats/{chatId}/members` → member list with `user_id`, `is_bot`, `is_admin`. Good way to resolve a real user_id before DMing.
- `DELETE /chats/{chatId}/pin` → 200; after unpinning, `GET /chats/{chatId}/pin` returns `{}` rather than an error.

## Editing a message, and how to verify it

`PUT /messages?message_id=<mid>` with `{"text": "..."}` returns `200 {"success": true}`. Verified 2026-10-04 that an edit is **durable** — re-read it after 45s and 105s and the new text was still there, so MAX does not revert edits over time.

Two traps:

1. **It can return HTTP 200 with `{"success": false, "message": "Error on message edit"}`.** Always check the `success` field, not just the status code — that is what a deleted or foreign message looks like.
2. **`GET /chats/{chatId}/pin` can return STALE text after an edit.** Verified: `GET /messages/{mid}` and `GET /messages?chat_id=…` both showed the new text while the pin endpoint still served the pre-edit version — same `mid` and `seq` in all three.

**When verifying an edit, read `GET /messages/{mid}` or the chat history. Never the pin endpoint.**

**But do NOT conclude from a pin/message mismatch that a real client sees stale text.** When the user reported the MAX app showing the correct updated list while the pin API served the old one, the divergence existed only in the API projection — the actual client rendered the fresh text. So: pin is useless for verification, and a pin mismatch is not a bug report, it is a measurement artefact.

## Basics
Base URL: `https://platform-api2.max.ru`. Resolve credentials for the specific bot from its project configuration; do not assume MAX and Telegram tokens are interchangeable or that a generic `MAX_TOKEN` belongs to the intended bot. Verify identity through read-only `GET /me` before using a discovered credential. Some older integrations reused a token, but that is a per-integration fact, not a platform rule. Forge AI specifically uses `MAX_FORGE_TOKEN` or vault `MAX_TOKEN_FORGE`, not the generic `MAX_TOKEN`.

## Auth quirk (the one that wastes time)
The `Authorization` header takes the **raw token with NO `Bearer` prefix**.

- ✅ `Authorization: <raw_token>`
- ❌ `Authorization: Bearer <token>` → `401 verify.token "Malformed access token"`

## Endpoints that get used
| Call | Method + path |
|---|---|
| Chat info | `GET /chats/{chatId}` |
| Get pinned message | `GET /chats/{chatId}/pin` |
| Unpin | `DELETE /chats/{chatId}/pin` |
| Message info | `GET /messages/{messageId}` |
| Delete message | `DELETE /messages?message_id=...` |
| Edit message | `PUT /messages?message_id=...` |
| Pin message | `PUT /chats/{chatId}/pin?notify=false` with JSON body `{"message_id":"..."}` |

The bot must be a **chat admin** to delete or pin — otherwise these return a permission error even with a valid token, which looks like an auth failure but isn't.

## Media: images and files need a two-step upload

`POST /messages` cannot take a local path. Upload first, then attach the token:

```
POST /uploads?type=image|video|audio|file     -> {"url": "https://iu.oneme.ru/...", "token": optional}
POST <that url>  Content-Type: multipart/form-data  -F 'data=@file'  (no Authorization header)
   image -> {"photos": {"0": {"token": "..."}}}      attach {"type":"image","payload":{"photos": <that dict>}}
   file  -> {"fileId": 1, "token": "..."}            attach {"type":"file","payload":{"token": "..."}}
```

- An image can also be sent by URL only: `{"type":"image","payload":{"url":"https://..."}}` — MAX fetches it itself. Handy for public links, useless for private/local files.
- **Files are processed asynchronously.** Attaching immediately after upload returns `400 {"code":"attachment.not.ready","message":"...attachment.file.not.processed"}`. Retry the send with backoff (0.5s → 4s, ~5 attempts); images usually land first try, PDFs/TXT regularly need a retry.
- A 1×1 base64 PNG is rejected with `{"error_code":"503","error_data":"IMAGE_INVALID_FORMAT"}` — test uploads with a real (e.g. 240×120 PIL) image, or you will chase a phantom auth problem.

## Typing indicator

`POST /chats/{chatId}/actions` with `{"action": "typing_on"}` → `{"success": true}`. Works with a **dialog** chat_id (a DM's synthetic id) as well as a group id. Other actions: `sending_photo|sending_video|sending_audio|sending_file|mark_seen`.

## Long polling: `GET /updates`

`GET /updates?limit=100&timeout=30&marker=<int>&types=message_created,bot_started` — true long poll (server holds up to 90s; a 3s timeout is enough for a probe). Response `{"updates": [...], "marker": N}`; **passing the returned marker commits everything up to it**, so persist it between process restarts or a restart replays the backlog. Update `message_created` carries the full `message` object (sender / recipient / body.mid / body.text / body.attachments).

For a production bridge prefer webhooks (`POST /subscriptions`) — MAX documents long polling as speed- and retention-limited. Long polling is still the right choice when the host has no public HTTPS endpoint.

Sending text: `format` accepts `markdown` or `html`, `text` maxLength **4000**. A 400 is worth retrying once without `format` — broken markup must not drop the message.

## Inline keyboards

Attachment shape (one attachment in `attachments`):

```json
{"type": "inline_keyboard", "payload": {"buttons": [
  [{"type": "link", "text": "Открыть", "url": "https://example.com"}],
  [{"type": "callback", "text": "Остатки", "payload": "stock"}]
]}}
```

- Up to 210 buttons, 30 rows, 7 per row (3 per row for `link`, `open_app`, `request_geo_location`,
  `request_contact`).
- `callback` buttons only do something if something consumes updates: a webhook (`POST /subscriptions`)
  or a long-poll loop on `GET /updates`. A bot with no handler answers nothing, and `/start` sent to it
  is silently lost — check `GET /subscriptions` and look for a handler process before promising buttons.
- Answer a callback with `POST /answers?callback_id=<id>` and body `{"notification": "…"}` (or
  `{"message": {…}}` to edit the message). A made-up `callback_id` returns
  `400 Callback identifier is invalid`, so the answer path can only be tested by a real press.
- `message` type buttons send a preset text to the bot — useful as menu entries for a long-poll bot.

## `open_app` buttons need the mini-app registered on MAX's side

A bot cannot open an arbitrary URL as a mini-app. The button schema is
`{"type":"open_app","text":…,"web_app":"<https url>","payload":"<id, no slashes>"}` (snake_case
`web_app`; camelCase `webApp` is not recognised and yields `Field 'webApp' cannot be null`), and the
URL is looked up in MAX's own link registry:

```
404 {"code":"not.found","message":"Key: common.finder, args: [link,… Link not found with pk =
  LinkPK{name='https://…', space=TAMTAM}]"}
```

Registration happens in the MAX business cabinet for a verified legal entity (since Aug 2026 only
verified RU organisations may publish bots/mini-apps) and is **not** available through Bot API calls.
A `link` button to the same URL works but opens a plain browser without `initData`, so a mini-app
identity flow (MAX launch data) cannot be reproduced through it — say so instead of shipping a button
that lands the user on a login wall.

## Pitfalls
- Message ids are strings in the pin body, ints elsewhere; send the pin body exactly as `{"message_id":"..."}`.
- `notify=false` on pin matters: without it MAX sends an extra system notification to the group.
- Unpin (`DELETE /chats/{chatId}/pin`) takes no body — do not send the message_id with it.
- Do not log the raw token into MEMORY.md or any file under /root; reference where it lives instead.

## Context
Used by the live manicure booking pair on n8n (see MEMORY.md for workflow ids): the master-side workflow publishes + pins the slot list in group `-79638499377264`, the client-side workflow handles digit replies. Verify the current workflow ids in memory before editing — they may have changed.