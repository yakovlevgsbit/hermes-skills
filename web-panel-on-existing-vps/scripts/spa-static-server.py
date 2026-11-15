#!/usr/bin/env python3
"""
Static server for a built SPA (Vite/React/etc.) with client-side-route fallback.

Why this exists:
- `vite preview` validates the `Host` header and answers 403 to requests arriving
  through a shared domain (nginx proxy), so the app looks broken for exactly the
  route you just wired.
- A plain static server 404s every client-side route (`/s/demo`) because the file
  does not exist on disk; a SPA router needs those paths served index.html.

Run under systemd (Restart=always, WorkingDirectory=<app>, ExecStart=<venv>/python3):

    systemd unit ExecStart: <venv>/python3.14 /path/to/server/static_server.py

Serve `dist/` from the parent directory of this script (i.e. this script lives at
`<app>/server/static_server.py` and serves `<app>/dist/`). Adjust DIST to taste.

Security: normalizes the path, rejects anything escaping the dist root, and only
serves regular files. The nginx `location ^~ /prefix/ { proxy_pass …/; }` (trailing
slash) strips the prefix before the request arrives, but handle both forms anyway.
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
PORT = int(os.environ.get("SPA_STATIC_PORT", "5198"))

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _serve(self, path, code=200):
        ext = os.path.splitext(path)[1].lower()
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            return False
        self.send_response(code)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def do_GET(self):
        from urllib.parse import unquote, urlparse
        p = unquote(urlparse(self.path).path).lstrip("/")
        # nginx may have already stripped the location prefix, but if it did not,
        # strip a leading known prefix here too (edit to match your vhost):
        if p.startswith("prefix/"):
            p = p[len("prefix/"):]
        # normalize and reject escapes
        p = os.path.normpath(p).lstrip("/\\")
        if p.startswith(".."):
            self.send_response(403)
            self.end_headers()
            return
        file_path = os.path.join(DIST, p)
        if os.path.isfile(file_path):
            return self._serve(file_path)
        # SPA fallback: every client-side route -> index.html
        index = os.path.join(DIST, "index.html")
        if os.path.isfile(index):
            return self._serve(index)
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"spa-static (dist) on http://127.0.0.1:{PORT}")
    srv.serve_forever()
