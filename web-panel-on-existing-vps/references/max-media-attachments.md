# Sending photos/media through the MAX bot API

Text is one call; media is a three-call chain on `platform-api2.max.ru`. All
steps carry the **raw token with no `Bearer` prefix** in `Authorization`.

## The chain

1. **`POST /uploads?type=image`** — multipart, **field name `data`** (not
   `file`), body = the file bytes. Returns `{url}`. The URL is **one-shot**:
   request a fresh one for every file, reusing it answers 400.
2. **`POST <url>`** — multipart again, **same field name `data`**. Returns
   `{photos: {"0": {"token": …}}}` for an image; that token is the attachment
   handle.
3. **`POST /messages?user_id=<id>`** with:
   ```json
   {"text": "…", "attachments": [{"type": "image", "payload": {"token": "…"}}]}
   ```
   Recipient in the query string, never in the body.

## Traps (each one reads like an auth or token problem)

- **Raw bytes to the upload URL fail.** Posting the file body directly answers
  `{"error_code":"4","error_data":"BAD_REQUEST"}` even though the URL came back
  200. The upload step is multipart with the `data` field, full stop.
- **Pause ~1s between upload and send.** The attachment is still processing;
  sending immediately answers `attachment.not.ready`.
- **`type` is `image`, never `photo`.** The old `photo` value was removed and
  answers `File extension is forbidden`.
- **A bot cannot delete its own message in a personal dialog** — `DELETE
  /messages?message_id=…` returns 403 (it is not a chat admin of a 1:1 chat).
  Test in a group where the bot is admin; in a DM, ask the user to remove it.
- **Image limits:** ≤ 50 MB and ≤ 7680×7680 px, both must hold.
- **Tiny synthetic images are fine for proving the chain** — a small
  programmatically generated JPEG/PNG exercises upload → token → send without
  touching real assets.

## Probing a token without sending anything

`POST /messages?user_id=<id>` with an empty body answers
`400 proto.payload "Empty request body"` — authorization passed, nothing
delivered. Cheapest validity check for a freshly supplied bot token, before
wiring it into a service.

## One bot per product

A product that messages users gets **its own bot token**, stored as its own
variable in the secrets file (e.g. `MAX_TOKEN_<PRODUCT>`, with a fallback to the
shared token). Two products sharing one bot means one token rotation breaks
both, and the product's KB entry cannot say which bot it sends with. The
recipient must have an existing dialog with *that specific* bot — a dialog with
the old bot does not transfer to the new one. After switching tokens, prove the
path end-to-end (record written, photo in storage, message delivered) before
reporting.

## Sending a generated table/report as an image

When the notification is a *report* (stock/leftovers, a summary table), render it
to a PNG server-side and send it through the same three-call chain — the user
reads a picture in the messenger without opening anything.

- **Render with headless Chromium, not PIL.** Write the HTML (a real `<table>`
  with the column headers the user named), then screenshot it with Playwright:
  `p.chromium.launch()`, `new_page(viewport=…, device_scale_factor=2)`,
  `goto("file:///tmp/report.html")`, `wait_for_timeout(400)`, `screenshot(path=…,
  full_page=True)`. `device_scale_factor=2` keeps small table text legible in the
  chat. The render script is a short subprocess call into the same venv that has
  playwright installed.
- **The column header is part of the spec.** When the user says 'the header is
  «Туша» and under it the leftovers', that is the layout: the entity label is the
  header, its rows sit under it. Build exactly that shape — a header row plus one
  cell per entity holding its list — and render the same markup the in-app table
  uses, so the app and the chat image agree.
- **Wrap the render in try/except and report `max_sent`.** A render or upload
  failure must not break the data write; surface it in the API response so the UI
  can say the table was saved but the image did not send.
- A stock/leftover figure is only correct if it accounts for **both** issues and
  returns: remaining = not-issued OR returned. Compute it on the server from the
  event tables, not from a UI-side subtraction.

## The use case this usually serves

A form whose "submit" is really "notify the owner": the submit handler writes
the row, uploads the photo, and sends it to the owner with a text caption
composed from the row's fields (entity id, recipient, selected items). Report
the MAX delivery result (`max_sent` + the returned message id) in the API
response so the UI can tell the truth when the send fails — a form that says
"saved" while the notification silently never arrived is the failure mode to
avoid.