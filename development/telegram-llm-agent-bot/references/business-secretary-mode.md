# Telegram Business bot (Secretary Mode)

A bot that answers the owner's **personal** chats on his behalf, through the official
Bot API — not a userbot, no `api_id`, no MTProto session on the account.

## When to use

- «Отвечай вместо меня в личке», secretary/auto-answer for a business account.
- When a userbot is undesirable or blocked (`my.telegram.org` flood, ban risk) and the
  traffic is private one-to-one chats.

Not for: group/channel traffic, writing first to a stranger, history before the bot
was connected — none of that is possible (see limits).

## Enabling (three places)

1. `@BotFather` → `/newbot` (separate bot — the gateway bot is already long-polling).
2. `@BotFather` → `/mybots` → bot → `Bot Settings` → **Business Mode** → Enable.
   Verify from the API, not by eye: `getMe` must return
   `can_connect_to_business: true`.
3. Client: Настройки → **Telegram Business → Чат-боты** → add the bot → grant
   «читать сообщения» and «отвечать на сообщения». Requires an active Telegram
   Business subscription on the account.

## Limits (platform, not configuration)

| Possible | Impossible |
|---|---|
| Reply in a private chat with an incoming message in the last 24 h | Write first / open a dialog |
| Read those messages (if `can_read_messages`) | Groups, channels |
| Send, edit, delete per granted rights | See history from before the connection |

The only send permission is `can_reply`, documented as *send and edit messages in
private chats that had incoming messages in the last 24 hours*. There is no
»initiate» right at all, so cold outreach is off the table — say that before the
user plans a campaign around it.

## Updates and sending

`getUpdates(allowed_updates=["business_connection","business_message","edited_business_message"])`

- `business_connection` — connected / rights changed / disconnected. Carries
  `id`, `user`, `can_reply`, `is_enabled`.
- `business_message` — a message in a managed chat, including the owner's own
  (`out: true`). Carries `business_connection_id` and `chat.id`.
- Send with the same field:
  `sendMessage(business_connection_id=..., chat_id=..., text=...)`.

## Bridge shape (stdlib, no framework)

Single long-poll loop + a reply thread:

1. Store `business_connection` rows and messages in SQLite (`uid = chat_id:message_id`
   as the primary key gives free dedupe).
2. On an incoming message, mark the chat pending; after `reply_delay_sec` (15 s is
   enough for the human to answer himself) generate a reply from the last ~15
   messages of that chat.
3. If the owner replied manually (`out: true`), mark all pending rows of the chat
   answered — never talk over him.
4. `draft` mode sends the draft to the **owner** via a separate bot; `auto` mode sends
   it to the contact. Start in `draft` — the owner sees the wording before it matters.
5. LLM returns `SKIP` for spam/cold contacts; the loop then sends nothing.

## Pitfalls

- **`business_connection` arrives once.** If the update is lost (service restart, first
  poll race), every following message still carries `business_connection_id` — infer
  the connection row from it (`can_reply` assumed true) instead of dropping traffic.
  Symptoms: `skip chat=...: no connection record` every few seconds.
- **Never name a keyword `timeout` twice.** A helper `tg(token, method, timeout=45, **params)`
  collides with the long-poll `timeout` param → `TypeError: got multiple values for
  keyword argument 'timeout'` and a systemd restart loop. Name the HTTP one `http_timeout`.
- **A skipped chat must be marked answered**, otherwise the reply loop retries it every
  tick and floods the journal.
- **Cloudflare-fronted LLM gateways reject the default Python-urllib User-Agent** with
  `403`; set an explicit `User-Agent` header.
- **A token pasted into chat is exposed.** Work from a `600` secrets file and tell the
  user to `/revoke` once the bridge is proven.

## Verification

- `getMe` → `can_connect_to_business: true`; log line `bot @… connect_to_business=True`.
- `selftest.py`: temp SQLite, canned dialog, real LLM call, assert the draft is produced
  and pending rows are marked — runs without Telegram.
- Live: an incoming message appears as `incoming chat=… from=…`, then `draft for chat=…`
  (or `sent to chat=… msg=…`), and the owner receives the draft.
