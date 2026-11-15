# openclaw70846.hostkey.in route map

Static (inside container /usr/share/nginx/html):
- /portfolio/      → index.html (+ prototypes/<id>.html)
- /manicure-demo/ → standalone demo (localStorage only)
- /kp/            → static files; check current deployed contents
- /demos/         → static files; check current deployed contents
- /web-assistant/ → static files; check current deployed contents
- /reels/         → finished reels (alias)
- /videotest/     → source frames for image-to-video

Proxied backends:
- /avto/     → 127.0.0.1:5198 (React PWA; /s/demo front, /s/demo/admin owner)
- /avto-pub/ → :8097, /avto-api/ → :8096 (Python)
- /beef/     → :8101 (accounting, static+api), /beef-issue/ → :8100
- /manicure/ → :8099 (master panel, HTTP basic)
- /smm/      → :8765 (FastAPI), OAuth callback at /smm/oauth/
- /n8n/     → :5678
- /tire-fit/api/ → :8102
- /max-webhook, /lava-webhook → :8088
- / (root catch-all) → :9119 (Hermes dashboard)

Treat this map as a lookup aid, not a health report. Re-read the current vhost
and check deployed files before using a route. Distinguish exact document
locations from asset prefixes; a working index does not establish that its
sibling CSS, images or sitemap are served. Inspect the matched location and
error log before attributing a static-route failure to an upstream process.
