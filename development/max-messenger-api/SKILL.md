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
Base URL: `https://platform-api2.max.ru`. The MAX bot token is the SAME token as the Telegram bot token for the bot in question — do not hunt for a separate secret.

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

## Pitfalls
- Message ids are strings in the pin body, ints elsewhere; send the pin body exactly as `{"message_id":"..."}`.
- `notify=false` on pin matters: without it MAX sends an extra system notification to the group.
- Unpin (`DELETE /chats/{chatId}/pin`) takes no body — do not send the message_id with it.
- Do not log the raw token into MEMORY.md or any file under /root; reference where it lives instead.

## Context
Used by the live manicure booking pair on n8n (see MEMORY.md for workflow ids): the master-side workflow publishes + pins the slot list in group `-79638499377264`, the client-side workflow handles digit replies. Verify the current workflow ids in memory before editing — they may have changed.