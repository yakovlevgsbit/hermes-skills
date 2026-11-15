# FastAPI Routing & Deployment Pitfalls

## Catch-all SPA route swallows GET /api/*

`@app.get("/{path:path}")` placed above API routes will match `GET /api/content-plans/5` and return index.html instead of the API handler. POST routes still work because the catch-all is GET-only, which makes the bug confusing: POST succeeds, GET fails with HTML.

**Fix:** either register API routes before the catch-all, or add `if path.startswith("api/"): raise HTTPException(404)` inside the catch-all.

**Verify:** after fixing, test with a direct curl to the backend port (bypassing nginx). If it still returns HTML, the running process has a stale .pyc cache — `rm -rf __pycache__` and restart.

## Double prefix in frontend API calls

When a frontend helper like `api()` already prepends a base prefix (e.g. `const API_BASE = '/smm/api'`), never add the prefix again in the call site. `api('/api/content-plans')` will produce `/smm/api/api/content-plans`.

**Symptom:** POST requests may still work if they use a different code path, making the bug seem intermittent. Grep the JS for `/api/` after the base prefix has been added.

## StaticFiles mounts require the directory to exist

`app.mount("/images", StaticFiles(directory="/data/images"))` crashes the entire app with `RuntimeError: Directory does not exist` if the directory hasn't been created yet.

**Fix:** add `os.makedirs(..., exist_ok=True)` before the mount call, or handle the case where the directory is created later.

## systemd service picks up stale __pycache__

After editing main.py, `systemctl restart` may not pick up changes if `__pycache__` contains stale .pyc files. The process continues running the old code.

**Fix:** always `rm -rf __pycache__` before restarting the service. Or use `systemctl stop && rm -rf __pycache__ && systemctl start` to be safe.
