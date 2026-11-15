# File Uploads Through a Proxied Panel

A panel that accepts real files (video for publishing, photos, documents) has a
failure chain that spans three layers — nginx, the app, and the frontend — and
each layer fails in a way that looks like the others. Wire all three in one pass,
then test with a real file of a realistic size.

## Layer 1 — nginx drops the body before the app sees it

The nginx default `client_max_body_size` is **1 MB**. Every upload larger than
that is rejected at the proxy with **413**, and the app never logs anything — so
it reads as "the upload endpoint is broken" while the endpoint is fine. Set it on
the API `location` block and stream instead of buffering:

```nginx
location ^~ /prefix/api/ {
    proxy_pass http://127.0.0.1:<port>/api/;
    client_max_body_size 2100m;        # match the app's own limit, plus headroom
    proxy_request_buffering off;       # stream to the app, don't spool to disk
    proxy_read_timeout 3600s;          # a large upload is a long request
    proxy_send_timeout 3600s;
    ...
}
```

Set the app's own limit to the provider's real ceiling (YouTube refuses >2 GB)
rather than to a round number you invented, and have the app answer **413** with
a message naming the limit so the two layers agree.

## Layer 2 — the app

- **FastAPI needs `python-multipart` installed** or a multipart route raises at
  import/definition time. `pip3 install --break-system-packages python-multipart`
  on a Debian/Ubuntu VPS.
- **Read the body in chunks, not `await file.read()` once.** A 2 GB read buffers
the whole file in RAM; read 1 MB at a time and count bytes as you go so the size
  limit is enforced *during* the write, and delete the partial file on overflow.
- **Never trust the client filename.** `os.path.basename()` it, validate the
extension against an allowlist, and generate the stored name yourself:
  `<UTC-timestamp>_<hex>_<sanitized-stem><ext>`. Two users uploading `video.mp4`
  must not collide, and a name like `../../etc/passwd` must not escape the dir.
- **Store a `stored_path` column separate from the original `filename`.** Downstream
  code (the publish step) must resolve the file by `stored_path`; resolving by
  `filename` works in testing and breaks the moment two uploads share a name.
  Resolve with a fallback list (`stored_path`, then `filename`) so rows created
  before the column existed still work.
- **Add the column with a lightweight migration, not a schema wipe.** After
  `CREATE TABLE IF NOT EXISTS`, read `PRAGMA table_info(<table>)` and
  `ALTER TABLE ... ADD COLUMN` for anything missing — an existing production DB
  will not gain a column from an edited `CREATE TABLE` statement.
- **Deleting a row must delete the file.** A DELETE that removes the DB row and
  leaves the blob on disk leaks storage silently; a few test uploads of real
  video add up. Remove both, and `os.path.basename()` the stored name before
  joining it to the upload dir.

## Layer 3 — the frontend needs XHR, not fetch

`fetch()` cannot report upload progress. Use `XMLHttpRequest` with
`xhr.upload.onprogress` — it is the only browser API that gives `loaded`/`total`
during the send:

```js
const xhr = new XMLHttpRequest();
xhr.open('POST', `${API_BASE}/videos/upload`);
xhr.withCredentials = true;                 // session cookie
aFormData.append('file', file);
xhr.upload.onprogress = (ev) => {
  if (ev.lengthComputable) bar.style.width = Math.round(ev.loaded/ev.total*100) + '%';
};
xhr.onload = () => { /* parse xhr.responseText; xhr.status is the real status */ };
xhr.send(formData);
```

Note `xhr.withCredentials = true` — a panel under a path prefix with cookie auth
silently uploads unauthenticated (and gets 401 JSON) without it.

## Verify with a real file, not a placeholder

- **A fake payload with a real extension does not prove the pipeline.** Bytes
  that begin with an `ftyp` box header and then random data are accepted by the
  upload endpoint, stored, and even accepted by a video provider's upload API —
  then the provider's transcoder rejects them and the item shows up as
  `Deleted video`. The upload "succeeded" at every layer you instrumented and the
  artifact is still gone. Generate a genuine file to test with:
  ```bash
  ffmpeg -y -f lavfi -i testsrc=duration=3:size=640x480:rate=24 \
         -f lavfi -i sine=frequency=440:duration=3 \
         -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest \
         /tmp/real_test.mp4
  file /tmp/real_test.mp4   # expect: ISO Media, MP4 Base Media
  ```
  `ffmpeg` is worth installing on the panel host anyway — post-roll/banner
  compositing needs it.
- **Test each layer at a size that crosses its threshold.** A 200 KB file passes
  even with the nginx default in place; a 6 MB file is the one that proves
  `client_max_body_size` took effect. Test the size that would have failed.
- **Test the rejection path too** — an `.exe` (or any disallowed extension) must
  answer 400 with the allowed list, and an oversized file must answer 413. A
  validation rule you never exercised is a rule you do not have.
- **Clean up after the test**: delete the rows through the API (which also
  exercises the file-removal path) and confirm the upload directory is empty,
  then delete any artifact the test created in the user's real external account.
  State what was left in the report.

## Provider-side limits to encode as constants

- Video platforms cap upload size and reject the file at the transcoder, not at
  the API call — a successful API response is not a live artifact. Confirm the
  artifact exists afterward (a read-back), then clean it up.
- Uploading with a restricted scope (`youtube.upload` + `readonly`) means the
  same token **cannot delete** the test video — `403 insufficient scopes`. Plan
  for a manual delete or a wider scope; do not promise cleanup you cannot perform.
- Publish state is usually the provider's default, not "public" — a video lands
  `private` unless you set it explicitly. Say which state it landed in.
