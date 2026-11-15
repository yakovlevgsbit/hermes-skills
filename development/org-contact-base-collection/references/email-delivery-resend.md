# Email delivery via REST API — when SMTP ports are blocked

Use when outbound SMTP (25/465/587) is filtered by the hosting provider and only
80/443 are reachable. Sending through a mail service's HTTPS API bypasses the
block entirely.

## Why this works

Mail providers' REST APIs serve everything over 443, which is almost never
filtered. SMTP is a separate port range that many hosts block by default. So the
fix is not "configure SMTP better" — it is "stop using SMTP".

## Choosing a provider — decide by domain, not by preference

The blocker is almost always **whether you have a verified domain**, so probe that
first and let it pick the provider:

| Provider | Needs a verified domain | Needs a card | Can email third parties |
|---|---|---|---|
| Resend | yes | no | no — testing mode only reaches the account's own address |
| Mailgun | yes | yes | no — without a card only ~5 "authorised" recipients, each must click a confirmation link |
| SendGrid / Brevo / Postmark | yes | varies | yes |
| **AgentMail** | **no** | **no** | **yes** |

**If there is no domain and no card, use AgentMail** (`agentmail.to`): an inbox at
`xxx@agentmail.to`, sends through `POST /v0/inboxes/{inbox}/messages/send`, attachments
as base64. Free tier: 10/day, 300/month.

If a domain IS available, Resend is the fastest start: sign up → API key → verify the
domain → send.

## Procedure (Resend)

1. **Confirm the block before choosing a provider.** Test ports with a python
   socket (not `bash /dev/tcp`, which reports false results):

   ```python
   import socket
   for host, port in [("smtp.gmail.com", 587), ("smtp.gmail.com", 465),
                      ("imap.gmail.com", 993), ("api.resend.com", 443)]:
       s = socket.socket(); s.settimeout(5)
       try:
           s.connect((host, port)); print(host, port, "OK")
       except Exception as e:
           print(host, port, type(e).__name__)
       finally:
           s.close()
   ```

   SMTP ports timing out while 443 connects = provider-level filter. Check
   `ufw status verbose` too — but a firewall showing `allow (outgoing)` does NOT
   mean the path is open end-to-end.

2. **Get a Resend API key** and store it at `/root/.secrets/resend.env` (mode 600):

   ```
   RESEND_API_KEY=re_...
   RESEND_API_URL=https://api.resend.com
   ```

3. **Send through the API** (Python, see the pitfall about TLS fingerprints):

   ```python
   from curl_cffi import requests as cr
   r = cr.post("https://api.resend.com/emails",
               json={"from": "Name <onboarding@resend.dev>",
                     "to": ["client@example.com"],
                     "subject": "...", "html": "<p>...</p>"},
               headers={"Authorization": "Bearer " + key},
               impersonate="chrome", timeout=30)
   ```

   Attachments go as base64 in the same JSON body — no separate upload step:

   ```python
   body["attachments"] = [{"filename": "kp.pdf",
                           "content": base64.b64encode(pdf_bytes).decode()}]
   ```

## Procedure (AgentMail)

1. **Store the key** at `/root/.secrets/agentmail.env` (mode 600):
   `AGENTMAIL_API_KEY=am_...`, `AGENTMAIL_INBOX=<name>@agentmail.to`.
2. **Send:** `POST /v0/inboxes/{inbox}/messages/send` with `{to, subject, html, text,
   attachments:[{filename, content:<base64>}]}`. Returns a `message_id`.
3. **Read the inbox** through `GET /v0/inboxes/{inbox}/messages?limit=100`, which
   returns `messages[]` with `preview`, `attachments[]`, `labels`, `from`, `to`.
4. **Read permission is not the same as inbox permission.** A key can hold
   `message_read` while lacking `inbox_read` — the messages list works and the
   inbox-details endpoint 403s. Probe each endpoint rather than inferring one from
   the other; when a permission you need is absent, keep the missing state locally
   (e.g. a seen-log) instead of labelling mail.

## Deliverability, regardless of provider

Sending without your own domain means mail leaves from a provider-shared address.
For **cold commercial mail that is a deliverability risk** (spam placement), and for
outbound volume above the sandbox tier. For an initial pilot or a warm list it is
the fastest path — state the tradeoff to the client rather than silently picking the
sandbox channel for a campaign that needs a domain.

## Pitfalls

- **Cloudflare blocks non-browser TLS fingerprints.** `urllib`/`requests` get
  `403 error code: 1010`, while `curl` returns 200 — the difference is the JA3
  TLS fingerprint, not auth. Fix: `pip install curl_cffi` and pass
  `impersonate="chrome"`. Do not conclude "the API is down" from a Python 403;
  retest with `curl` to separate the two causes.
- **Testing mode only allows sending to the account's own address.** Resend
  returns `403` with "You can only send testing emails to your own email
  address". Sending to any other recipient requires a **verified domain**
  (`resend.com/domains` → Add Domain → add the SPF/DKIM/DMARC DNS records it
  shows). Until then the channel works only as a self-test.
- **Restricted keys can only send.** A key created as "send-only" returns
  `401 restricted_api_key` on every read endpoint (`/domains`, `/api-keys`,
  `/emails/{id}`). Sending still works; you simply cannot read status or quotas.
  So verify delivery by asking the recipient, not by polling the API.
- **Batch endpoint needs a broader key.** `POST /batch` is refused by send-only
  keys — loop single sends with a ~1.2s pause instead of assuming batching.
- **A brand-new account has a per-recipient sandbox limit, not just a daily one.**
  Expect "at most N distinct recipients per hour (M per 24h), lifting at <timestamp>".
  Read the `message` field of the 429 and size the batch to it: spreading a campaign
  over the sandbox window means **10 recipients/day**, so a 135-recipient list is a
  ~14-day drip, not a one-off send. Send the message text and the lift time to the
  client before promising delivery dates. Note that replies from addresses that have
  already written to the organization do not count against the limit.
- **A free tier appends a provider signature to every message.** Accept it, or budget
  for the paid plan; do not try to strip it.
- **Verify the whole chain end-to-end** on the account's own address first:
  send WITH the attachment, confirm the file opens, then unlock the real list.
  A send that returns 200 proves delivery to the provider, not to the inbox.

## Legal line

A verified domain, a real unsubscribe path, and accurate sender identity are
required for commercial mail. The recipient base must be open organizational
contacts; the advertising-law compliance of the campaign is the client's side.
