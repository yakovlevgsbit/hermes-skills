# MAX Messenger Bot API (platform-api2.max.ru)

Provider quirks for the MAX messenger, confirmed against a live bot token. Base path `https://platform-api2.max.ru` (never `platform-api.max.ru`).

## Auth: no `Bearer`

MAX wants the raw token in the `Authorization` header. `Authorization: Bearer <token>` fails with `401 {"code":"verify.token","message":"Malformed access token"}` even though the token is valid — the prefix itself is the bug.

```bash
# correct
curl -s -H "Authorization: $TOKEN" "$BASE/chats/$CHAT_ID"
# wrong -> 401 Malformed access token
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/chats/$CHAT_ID"
```

Passing the token via query parameters is no longer supported; use the header only.

**The MAX bot token is its own secret, not the Telegram bot's**, even for the same owner and even when both have the same `client_id:secret` shape. A Telegram token here returns `401 verify.token "Invalid access token"` — which reads like an expired credential rather than "wrong platform". Keep the two in separately named credential entries and never infer one from the other.

Rate limit: 30 rps.

## Sending: the recipient is a QUERY parameter, never a body field

The single biggest time sink on this API. `user_id`/`chat_id` in the JSON body returns `400 proto.payload "Unknown recipient"` even when the token and the id are both correct, so the error reads like a bad recipient and sends you chasing ids that were never wrong.

```
OK   POST /messages?user_id=121119600        body {"text": "..."}
OK   POST /messages?chat_id=-79638499377264  body {"text": "..."}
FAIL POST /messages   body {"user_id": ..., "text": "..."}
```

The body carries message content only. A send to a user returns a synthetic `recipient.chat_id` of `chat_type: "dialog"` — keep it, that is the id for reading that DM's history later.

## Editing a message, and the trap when verifying it

```
PUT /messages?message_id={mid}   body {"text": "..."}
```

Two traps:

1. **HTTP 200 does not mean it edited.** A deleted or foreign message returns `200 {"success": false, "message": "Error on message edit"}`. Branch on the `success` field, not the status code.
2. **`GET /chats/{chat_id}/pin` serves STALE text after an edit.** Verified live: after editing the pinned post, `GET /messages/{mid}` and `GET /messages?chat_id=…` both showed the new text while `GET /chats/{chat_id}/pin` still returned the pre-edit text — same `mid`, same `seq` in all three, so only the pin projection lags.

**Verify an edit through `GET /messages/{mid}` or the chat history, never through the pin endpoint.** Trusting the pin response makes a working edit look broken.

Editing in place (rather than re-posting) is what keeps a published list consistent with what its numbers resolve to; see the shared-state section of SKILL.md.

## Verify the token and chat with safe GETs

```
GET /chats/{chat_id}          -> chat metadata; 200 means the token works
GET /messages/{message_id}    -> full message (text, mid, sender); a 404 with code
                                "method.not.found" means the PATH is wrong, not that the
                                message is missing — message reads are at /messages/{id},
                                not /chats/{id}/messages/{id}
GET /chats/{chat_id}/members  -> real user_ids with is_bot/is_admin; the reliable way to
                                resolve a recipient before DMing. A bot's own user_id and a
                                chat_id are both invalid message recipients.
GET /messages?chat_id={id}&to={unix_ms} -> {"messages":[...]}; `to` bounds from a timestamp
```

## Pin / unpin

```
GET    /chats/{chat_id}/pin   -> {"message": {...}} when pinned, {} when not
PUT    /chats/{chat_id}/pin   -> pin; body {"message_id": "..."}, optional ?notify=false
DELETE /chats/{chat_id}/pin   -> {"success":true}
```

`GET .../pin` returning `{}` is the clean proof that an unpin worked. Omit `notify=false` and MAX emits an extra system notification into the group.

The bot must be a chat admin to pin or delete; a permission error there is not an auth failure.

## Delete a message

```
DELETE /messages?message_id={mid}   -> {"success":true}
```

Preconditions: the bot must be an admin of the chat with delete rights. In a group/channel it may delete any message; in a DM only its own. Rate limit: max 2 deletions per second per chat — insert a short sleep between deletes.

## Chat ids

Group chats have negative ids; they appear in workflow code as strings (`"-79638499377264"`) and in API paths verbatim. `GET /chats/{id}` returns `owner_id`, `participants_count`, `title`, `is_public` — useful for confirming you are pointed at the intended chat before any destructive call. Message ids in the pin body are strings; elsewhere they may be ints — send the pin body exactly as `{"message_id": "..."}`.

## n8n node note

The n8n `max-bot` community nodes and a raw `HTTP Request` node use different auth styles; a workflow HTTP node may be configured with `httpHeaderAuth` while the raw API needs the bare token. When a live run fails on auth, test the token with a plain `curl` GET first to separate "bad credential" from "wrong header shape".