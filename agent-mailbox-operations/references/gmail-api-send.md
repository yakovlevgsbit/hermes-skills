# Sending mail over HTTPS (Gmail API)

Use when IMAP works but SMTP ports are filtered by the host. Same mailbox, same Sent
folder; only the transport changes.

## Setup

1. **OAuth client.** Reuse an existing Google Cloud project's OAuth client if there is
   one (the redirect URI is already registered). Desktop clients accept any
   `http://localhost` redirect, web clients only what is registered — check before
   designing the flow.
2. **Enable the API in the project.** Without it every call returns
   `403 Gmail API has not been used in project <id> before or it is disabled`, with the
   console URL inside the message. Send that URL to the user; nothing else changes.
3. **Consent URL:**
   `https://accounts.google.com/o/oauth2/v2/auth?client_id=…&redirect_uri=…&response_type=code&scope=https://www.googleapis.com/auth/gmail.modify&access_type=offline&prompt=consent&state=…`
   `gmail.modify` covers read, send, labels and trash in one grant. `prompt=consent` is
   what makes Google return a refresh token on repeat authorisations.
4. **Exchange the code** at `https://oauth2.googleapis.com/token` with the same
   `redirect_uri`; store `refresh_token` in a `600` JSON file.
5. **Refresh per call:** `grant_type=refresh_token` → `access_token` (1 h).

## Sending

```
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
Authorization: Bearer <access_token>
{"raw": "<base64url(MIME)>"}
```

- `raw` is the whole MIME message, base64url **without** padding (`=` stripped).
- Reply: read the source message `format=metadata` for `Subject`, `From`,
  `Message-ID`, set `In-Reply-To` + `References`, and pass `threadId` in the body — the
  thread stays intact.
- Gmail files the sent copy itself; do not also append via IMAP.
- Attachments go inside the MIME (`msg.add_attachment`), not as a separate field.

## Error matrix

| Response | Meaning | Action |
|---|---|---|
| `403 … has not been used in project` | API disabled | send the console enable URL, keep the token |
| `403 insufficientPermissions` | scope too narrow | re-consent with `gmail.modify` |
| `400 invalid_grant` on refresh | refresh token revoked/expired | re-run consent |
| `invalid_client` on any token call | wrong client secret | check the env file |
| `401` on `messages/send` | access token stale | refresh, retry once |

## Host traps

- `smtp.gmail.com` on 465/587 closed, IPv6 route absent on the VPS → the API is the
  only path; do not try to tunnel SMTP.
- Default `Python-urllib/x.y` User-Agent gets `403` from Cloudflare-fronted gateways;
  set an explicit UA on every request.

## Verification

`GET /users/me/profile` → real address and message counts; then send to yourself and
confirm the row in `[Gmail]/Отправленные` **through IMAP** — that is what proves the
whole loop rather than the API's `200`.
