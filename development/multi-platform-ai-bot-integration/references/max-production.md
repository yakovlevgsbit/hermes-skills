# MAX production recipe

## Registration

1. Obtain the token for the specific MAX bot and store it in a dedicated secret file with mode `600`.
2. Generate a webhook secret allowed by MAX's character/length rules.
3. Expose a public HTTPS URL on port 443.
4. Register with `POST /subscriptions` for `bot_started`, `message_created`, `message_callback`, `bot_stopped`, and `dialog_removed`.
5. Read `GET /subscriptions` and compare URL and event set.

## Request rules

- `Authorization` is the raw bot token; do not add `Bearer`.
- `POST /messages?user_id=<id>` or `?chat_id=<id>`; never put recipient fields in JSON.
- Keyboard: `attachments[0].type = inline_keyboard`, `payload.buttons` is a two-dimensional array.
- `callback` button → `message_callback`; pressing user is `callback.user.user_id`.
- `message` button → ordinary `message_created`; route by the exact button label or a normalized command.
- `link` button is suitable for Lava checkout.
- Media: obtain `/uploads?type=...` URL, upload multipart data, find the returned token, then send a native attachment with `payload.token`.

## Webhook handler

1. Verify `X-Max-Bot-Api-Secret` using constant-time comparison.
2. Parse JSON and derive a stable event ID.
3. Claim the event with a durable unique key before processing.
4. Return HTTP 200 immediately.
5. Process state changes and provider calls in an async task/queue.
6. Mark the event done/failed and log the stable event ID without secrets.

## Verification

- `GET /max-health` returns 200 through the public proxy.
- Missing secret returns 401; correct secret returns 200.
- A real `message_created` and `message_callback` arrive in the durable event table.
- `GET /messages?chat_id=...` shows the expected attachment type and button labels.
- A real button press reaches the correct external user, not the bot sender.
- The subscription is read back from MAX after registration.
