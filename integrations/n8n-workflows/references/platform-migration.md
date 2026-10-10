---
name: platform-migration
description: "Adapting n8n workflows between messaging platforms (Telegram → MAX, etc.)"
---

# Migrating n8n workflows between messaging platforms

When a workflow built for one platform (Telegram) needs to run on another (MAX), the n8n node graph must be restructured. The domain logic (business rules, Sheets/DB writes, AI agent) usually stays the same — only the I/O layer changes.

## Step 1 — identify all I/O nodes

Every Telegram node falls into one of four categories:

| Category | Telegram node type | What changes |
|---|---|---|
| **Trigger** | `n8n-nodes-base.telegramTrigger` | MAX has no polling trigger node. Replace with HTTP Request (`GET /messages?chat_id=…&to=…`) + cron every 5–10s. |
| **Send** | `n8n-nodes-base.telegram` (resource: "message") | Replace with HTTP Request. Recipient goes in query params (`?user_id=…` or `?chat_id=…`), message body in JSON body. |
| **File download** | `n8n-nodes-base.telegram` (resource: "file") | MAX returns file URL in `GET /messages/{id}` JSON. Two-step: GET message → extract `file_url` → HTTP GET download. |
| **Callback / inline buttons** | Telegram `callback_query` in trigger output | MAX does not support `callback_query`. Replace with reply buttons (arrive as `message.text`) or plain text input. |

## Step 2 — replace the trigger

Telegram's `telegramTrigger` node uses long-polling built into the platform. MAX has no equivalent node.

**Pattern:**
1. Create a cron node (every 5–10 seconds).
2. HTTP Request: `GET https://platform-api2.max.ru/messages?chat_id=<id>&to=<last_timestamp>`.
3. Auth header: raw token, NO `Bearer` prefix.
4. Parse response → pass to the routing code node.

**Critical:** The `to` parameter must track the last processed message timestamp. Store it in a dataTable or static data so each poll picks up only new messages. Without this, every poll re-reads the entire history.

## Step 3 — replace send nodes

Telegram node parameters:
```json
{"chatId": "...", "text": "...", "replyMarkup": "replyKeyboard", ...}
```

MAX HTTP Request:
```
POST https://platform-api2.max.ru/messages?chat_id=<id>
Body: {"text": "..."}
```

**Rules:**
- Recipient (`chat_id` or `user_id`) is a **query parameter**, never in the body. Body carries message content only.
- ReplyKeyboard works the same way — pass it in the body as `replyMarkup`.
- `replyKeyboardRemove` also works.
- For DMs: if `user_id` has no dialog, MAX returns `404 {"code":"dialog.not.found"}`. Fallback: post into the group.

## Step 4 — replace inline buttons (callback_query)

This is the biggest structural change. Telegram inline buttons trigger `callback_query` events with `callback_data`. MAX inline buttons exist but work differently (webhook-based).

**Recommended approach:** replace inline buttons with reply keyboards (text buttons). When the user taps a button, it arrives as `message.text` — the routing code node already handles text matching.

**If inline buttons are required** (e.g., complex multi-select with checkboxes): use MAX's inline button webhook URL. This requires:
1. Setting up a webhook on the MAX bot for button presses.
2. A separate HTTP webhook node in n8n to receive button callbacks.
3. Mapping `button_data` to the same routing logic.

**Simplest path:** reply keyboards + text input. Users tap "Приход" or type "1" — same UX, no webhook complexity.

## Step 5 — replace file download

Telegram: node with `resource: "file"`, `fileId: "..."` → n8n downloads automatically.

MAX: two-step HTTP:
1. `GET https://platform-api2.max.ru/messages/{messageId}` → JSON with `file_url` field.
2. `GET <file_url>` → binary file.

**Code node to extract file URL:**
```javascript
const msg = $('Telegram Trigger').item.json.message;
if (msg.photo) return { fileId: msg.photo[msg.photo.length - 1].file_id };
if (msg.document) return { fileId: msg.document.file_id };
return [];
```

Becomes:
```javascript
// After HTTP: Get Message node
if ($json.message.photo) return { file_url: $json.message.photo[$json.message.photo.length - 1].file_url };
if ($json.message.document) return { file_url: $json.message.document.file_url };
return [];
```

## Step 6 — adapt the routing code node

The router (Маршрутизатор) needs to handle `message.text` instead of `callback_query`:

| Before (Telegram) | After (MAX) |
|---|---|
| `msg.callback_query.data` | `msg.message.text` |
| `msg.callback_query.message.chat.id` | `msg.message.chat.id` |
| `msg.message.chat.id` | `msg.message.chat.id` (same) |
| `msg.message.entities` (commands) | `msg.message.text` (full text) |
| `msg.message.reply_to_message` | `msg.message.reply_to_message` (same) |

## Step 7 — test the full loop

1. Activate the cron trigger.
2. Send a test message from the MAX client.
3. Verify it reaches the router (check dataTable or a debug HTTP node).
4. Test every branch: send, receive, file upload, inline buttons (now reply buttons).
5. Verify file download works end-to-end (photo arrives → URL extracted → Drive upload).

## Platform comparison: Telegram vs MAX

| Feature | Telegram | MAX |
|---|---|---|
| Trigger | `telegramTrigger` (polling) | HTTP `GET /messages` + cron |
| Send | `telegram` node | HTTP `POST /messages?chat_id=…` |
| Inline buttons | `callback_query` events | Webhook-based (complex) or reply buttons |
| Reply buttons | `replyKeyboard` → `message.text` | `replyMarkup` → `message.text` (same) |
| File download | `telegram` node (auto) | HTTP GET message → extract URL → HTTP GET |
| Auth header | Bot token (no prefix needed) | Raw token, NO `Bearer` prefix |
| Rate limit | ~30 msg/sec | 30 rps on platform-api2.max.ru |
| DM to new user | Works | `404 dialog.not.found` — fallback to group |
| Message edit | `editMessageText` node | HTTP `PUT /messages?message_id=…` |
| Message delete | `deleteMessage` node | HTTP `DELETE /messages?message_id=…` |
| Pin | `pinChatMessage` node | HTTP `PUT /chats/{id}/pin?notify=false` |

## Pitfalls

- **Never put recipient in the body.** MAX returns `400 proto.payload "Unknown recipient"` — the error looks like a bad ID but the fix is moving it to query params.
- **No `Bearer` prefix on MAX auth.** `Authorization: Bearer <token>` returns `401 verify.token "Malformed access token"`. Raw token only.
- **Reply buttons ≠ callback_query.** Button taps arrive as plain text. The routing code must match text, not `callback_data`.
- **File URLs expire.** MAX file URLs are temporary. Download immediately after receiving the message, don't store the URL for later.
- **Cron too fast = rate limit.** Don't poll faster than every 5 seconds. 30 rps is the limit and you'll hit it with multiple concurrent polls.
- **Dialog not found on DM.** MAX bots cannot open a dialog with a user who never wrote to them. Always have a group fallback for DMs.
