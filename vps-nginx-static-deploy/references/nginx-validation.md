# Validate a scoped nginx change without touching production

Use this when a redesign needs new static paths on a shared nginx server but
production publication has not been approved.

## 1. Prepare the candidate locally

1. Inspect the running image and mounts with `terminal` using restricted fields:
   `docker inspect nginx-nginx-1 --format '{{.Config.Image}} {{json .Mounts}}'`.
2. Copy the backed-up vhost to a local validation directory. Apply the proposed
   change to that copy with `patch`, not to the host-mounted production file.
3. Generate a unified diff in Python. Assert that the original prefix and suffix
   outside the intended location block are byte-identical; this catches accidental
   rewrites of neighbouring applications.
4. Use `write_file` to create `validation.conf` in the same directory:

```nginx
worker_processes 1;
error_log stderr warn;
pid /var/run/nginx.pid;
events { worker_connections 64; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log off;
    include /validation/vhost.candidate.conf;
}
```

## 2. Check syntax in an isolated container

Run through `terminal`, substituting the inspected image and local directory:

```sh
docker run --rm --network none --read-only --memory 64m --cpus 0.5 \
  --tmpfs /var/cache/nginx:size=16m --tmpfs /var/run:size=1m \
  -v <validation-directory>:/validation:ro \
  -v nginx_secrets:/etc/letsencrypt:ro \
  --entrypoint nginx <running-nginx-image> \
  -t -c /validation/validation.conf
```

- Reuse the current image to validate the actual directive syntax, not a different
  nginx release. Override the certificate-management entrypoint so the check does
  not renew certificates or start the production service stack.
- Mount the inspected certificate volume read-only; the parser needs referenced
  certificate files but must not alter them. Never copy private keys into a report
  or release archive.
- Keep the test off the host network and publish no ports. `nginx -t` parses the
  configuration; it does not need the production listeners or upstream services.
- Retain stdout/stderr and the exit code. A zero result with `syntax is ok` and
  `test is successful` establishes syntax validity only.

## 3. Keep the gates distinct

A syntax pass does not prove asset routing, application behaviour, authorization
or deployment. Exercise the release through private HTTP, but identify what that
server actually reproduces: Python's basic file server can test paths and browser
behaviour; it does not establish nginx gzip, immutable caching or security-header
policy. Test those against the candidate nginx configuration or the approved
public deployment, not against assumed defaults.

Preserve the approval gate before copying into production. After an approved
reload, verify dependency URLs before switching the document; after switching,
verify the exact published document and unchanged sibling routes. Make the browser
runner's origin configurable so the same tested assertions can target private
preview and public HTTPS without constructing another QA harness.

## 4. Verify encoded responses against the release manifest

Request compression explicitly. Compare the manifest against decoded content;
comparing gzip wire bytes to an uncompressed build hash reports a false mismatch.
Keep wire and decoded byte counts separate when reporting compression or speed.

```python
import gzip
from hashlib import sha256
from urllib.request import Request, urlopen

# Resolve url and expected_sha256 from the approved release manifest.
request = Request(url, headers={"Accept-Encoding": "gzip"})
with urlopen(request, timeout=25) as response:
    assert response.status == 200
    wire = response.read()
    encoding = response.headers.get("Content-Encoding", "identity")
    content = gzip.decompress(wire) if encoding == "gzip" else wire
    assert sha256(content).hexdigest() == expected_sha256
    print({
        "mime": response.headers.get_content_type(),
        "encoding": encoding,
        "cache": response.headers.get("Cache-Control"),
        "wire_bytes": len(wire),
        "decoded_bytes": len(content),
    })
```

Check intended policy as well as the hash: non-stale HTML, immutable cache only
on fingerprinted resources, correct image/font/XML MIME types, and the actual
HSTS/nosniff/referrer headers. An identity response is not evidence that gzip is
active. Keep local Lighthouse measurements labelled as local; do not present
compression estimates from a basic preview server as production results.
