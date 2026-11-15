# nginx location blocks inside the container

nginx runs **inside a Docker container** here, so location blocks are edited in the
container, not on the host. Get the container name with `docker ps` (on this host:
`nginx-nginx-1`) and work through `docker exec` / `docker cp`.

## The exact-match / prefix-match pair

```nginx
location = /beef/ {
    root /usr/share/nginx/html;
    try_files /beef/index.html =404;
}
location = /beef {
    return 301 https://$host/beef/;
}

location ^~ /beef/ {
    root /usr/share/nginx/html;
    try_files $uri $uri/ =404;
}
```

- `location = /path/` matches the exact URL and serves the directory's `index.html`.
- `location = /path` (no trailing slash) 301-redirects to the slashed form.
- `location ^~ /path/` matches the whole prefix and serves files with
  `try_files $uri $uri/ =404`.
- **`alias` + `try_files` does not compose** — use `root` with the full path inside
  `try_files`.

## Hosts that redirect 80 → 443

When the port-80 `server` block only contains `return 301 https://...`, a location
added there **never matches**. Requests go to HTTPS, so the new path falls through to
the catch-all `location /` (usually a proxy to an unrelated app) and answers **502**.

Add the location to the block containing `listen 443 ssl;`, then
`nginx -t` and `nginx -s reload` inside the container.

## Permissions after `docker cp`

`docker cp` preserves the source owner (root) while nginx runs as `www-data`, so a
freshly published file returns **403 Forbidden** until:

```bash
docker exec nginx-nginx-1 chmod 644 /usr/share/nginx/html/<path>/<file>
```

Put the `chmod` inside the publish function, not as a manual afterthought — a page
that 403s looks published from the filesystem and is dead from the browser.

## Editing a container's nginx config

```bash
docker exec nginx-nginx-1 cat /etc/nginx/conf.d/<site>.conf > /tmp/site.conf
# edit /tmp/site.conf
docker cp /tmp/site.conf nginx-nginx-1:/etc/nginx/conf.d/<site>.conf
docker exec nginx-nginx-1 nginx -t && docker exec nginx-nginx-1 nginx -s reload
```

`nginx -t` before `reload`: a broken config that is not reloaded is harmless, but a
broken config that reloads takes the site down.

## Publishing one static file

```bash
docker cp ./page.html nginx-nginx-1:/usr/share/nginx/html/app/page.html
docker exec nginx-nginx-1 chmod 644 /usr/share/nginx/html/app/page.html
curl -sS -o /dev/null -w '%{http_code}' https://<host>/app/page.html   # 200
```

A `200` plus the matching `chmod` is the whole verification.
