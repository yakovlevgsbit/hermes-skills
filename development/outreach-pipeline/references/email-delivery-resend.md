# Email delivery via REST API (Resend) — when SMTP ports are blocked

Use when outbound SMTP (25/465/587) is filtered by the hosting provider and only
80/443 are reachable. Sending through a mail service's HTTPS API bypasses the
block entirely. Mirrors the copy in the `org-contact-base-collection` skill.

## Why this works

Mail providers' REST APIs serve everything over 443, which is almost never
filtered. SMTP is a separate port range that many hosts block by default. So the
fix is not "configure SMTP better" — it is "stop using SMTP".

Providers reachable over 443 (verified): Resend, SendGrid, Brevo, Postmark.
Resend is the fastest to start: sign up → API key → send.

## Procedure

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
- **Verify the whole chain end-to-end** on the account's own address first:
  send WITH the attachment, confirm the file opens, then unlock the real list.
  A send that returns 200 proves delivery to the provider, not to the inbox.

## Legal line

A verified domain, a real unsubscribe path, and accurate sender identity are
required for commercial mail. The recipient base must be open organizational
contacts; the advertising-law compliance of the campaign is the client's side.
