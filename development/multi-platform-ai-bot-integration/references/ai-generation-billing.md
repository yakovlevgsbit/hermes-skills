# AI generation and billing recipe

## State machine

```text
button → kind selected → prompt stored → prompt validated
       → provider balance preflight → user balance spend
       → provider task → polling → artifact download
       → platform upload → native media send → success
```

Any failure after spending must execute one idempotent refund. A failure before spending must not create a refund row.

## Preflight

- Query the live provider balance with the provider client.
- Compare against the model's required provider credits.
- Treat an unavailable balance check as unsafe: do not charge the user.
- Never use a stale note or catalog value as current capacity.

## MAX media delivery

1. Download the provider result with a bounded timeout.
2. Request a MAX upload URL for image/video/audio.
3. Upload multipart bytes to that URL.
4. Recursively extract the token from the documented response shape; image responses may nest it under `photos`.
5. Send the native attachment to the correct `user_id`/`chat_id`.
6. If any step fails, mark the generation failed and refund the exact user charge once.

## Provider-specific route checklist

For a gateway such as AnyModel:

1. Read `/api-docs.md` and query the live balance and kind-specific catalog immediately before implementation.
2. Use the exact catalog model ID; for video call `/v1/videos/generations`, not chat completions.
3. Set `duration`, `resolution`, and aspect ratio explicitly; compute the provider-token estimate from the live billing block.
4. Save `request_id` and `x-9router-connection-id`; poll until terminal; keep polling failed jobs long enough for documented refunds.
5. Download through `/v1/videos/{request_id}/content`, then upload to MAX and send the native attachment.
6. Use the provider's supported HTTP client/fingerprint when its WAF rejects generic clients; verify the live balance again after the route is ready.

## Test matrix

- Main menu emits the expected button type and labels.
- Button press maps to the correct external identity.
- Prompt state survives a DB-backed session.
- Insufficient provider balance leaves user balance unchanged.
- Provider exception refunds exactly once.
- Successful mock task produces the expected media type and upload/send calls.
- Failed media delivery refunds and marks the generation failed.
- Telegram and MAX share billing data but use separate transport adapters.
