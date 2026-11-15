---
name: web-panel-on-existing-vps
description: "Ship a web panel onto a busy VPS without downtime."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [web, panel, vps, nginx, systemd, auth, deployment, pwa, multi-tenant]
---

# web-panel-on-existing-vps

Ship a small authenticated web panel (master dashboard, admin tool, mini-app) onto a VPS that is **already running other production things**, without taking them down.

## When to Use

- The user wants a web page / dashboard / mini-app, it will live on a server they already have, and something else on that server is in production (a bot platform, an existing site, an automation host, a gateway).
- There is already a domain with TLS in front of the host, and the question is whether a new app can share it.
- The panel needs its own login, or must stay private without asking anyone to install anything.

## Procedure

1. **Static files → inside the nginx container; proxy → separate server.** If the panel is pure HTML/CSS/JS with no server-side logic, copy the files into the nginx container (`docker cp`) and serve with `root` + `try_files` in a `location` block. No separate process, no port, no proxy. If the panel needs a backend (API, auth, DB), run a separate server bound to `127.0.0.1` and proxy to it.

   A `location = /beef/` with `root /usr/share/nginx/html; try_files /beef/index.html =404;` handles the exact path; a `location ^~ /beef/` with `root /usr/share/nginx/html; try_files $uri $uri/ =404;` handles everything under it.

   **`alias` + `try_files` does not work together** — use `root` instead. Exact-match `location =` takes priority over `^~` prefix match, so order matters when you have both.

2. **Reuse the existing proxy and domain; never claim a port or a cert.** A host with an existing HTTPS vhost needs no new certificate — add a `location` block. Check first:
   ```bash
   docker inspect <proxy-container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
   ```
   Editing a config inside the container is lost on recreate. Find the **bind-mounted host path** and edit there. A `cp` into the container works for a test but silently evaporates — if the container also exposes a real bind mount, use it instead, and be honest about which one is durable.

3. **Bind the app to `127.0.0.1`, not `0.0.0.0`.** Only the reverse proxy should reach it. One `location` block, `proxy_pass` to the loopback port, and the app's own auth stays the only thing between the internet and the data.

   **`proxy_pass` with vs. without a trailing slash decides whether the location prefix is stripped.** `location ^~ /tire/ { proxy_pass http://127.0.0.1:8098/; }` (trailing slash) forwards `/tire/x` as `/x`; without the slash it forwards `/tire/x` verbatim. If the app routes on `/` and `/api/*` (not `/tire/...`), the no-slash form makes every request miss and the app answers its own `404 {"error":"not found"}` — which looks like an app bug, not a proxy config bug. Match the form to what the app's router expects, and confirm with `curl` on the exact path right after `nginx -s reload`.

   **The app side has the mirror-image rule.** Once the prefix is stripped, every asset and API reference inside the app's HTML/JS must be **relative** (`src="app.js"`, `fetch('api/slots')`) or carry the prefix explicitly (`/tire/app.js`). A bare `src="/app.js"` resolves from the site root, lands in the catch-all `location /` that proxies to whatever else runs on the host, and answers **502** — the page shell paints while the script never loads and every container stays empty. The fix is in the app's references, not the proxy.

   **Serve every asset path the app asks for, and grep the HTML for the forms.** A missing `app.css` route makes `curl` report 200 for the page while the browser paints unstyled; a stale route list makes a static route fall through to the catch-all proxy. After the reload, curl the page *and each asset path with a real GET* (`curl -sD - -o /dev/null`), not only the index.

   **Move project files to a permanent directory, never scratch.** A project that lives under a cache/scratch path is deleted on the host's cleanup timer together with the service that runs from it. Copy the tree to `/root/<project>/` and repoint the unit's `WorkingDirectory`/`ExecStart` before testing anything long-running.

3. **Run it under systemd with `Restart=always`** and a resolved interpreter path. `ExecStart` takes an absolute path: `$(readlink -f $(which python3))`, never the bare name. A wrong path fails as `203/EXEC`, which the unit retries in a loop and logs about three times before you read the journal. Check `systemctl status`, not just `is-active`, right after enabling — `is-active` returns `activating` on a crash-looping unit.
   - **Point every service at a stable venv interpreter, not a tool-managed one.** When several services share one app server, the interpreter path can change under them (a tool rebuilds its bundled Python and the old binary is deleted); running processes keep working only because they were started before the rebuild, and the next restart fails `203/EXEC`. Move all of them to the venv at `…/venv/bin/python3.14` in one pass, install each app's deps into that venv, and confirm with `systemctl show <svc> -p ExecStart` that the path contains `/installs/` and not `tools/`.
   - **A venv may have no `pip`** — run `python -m ensurepip` first, then `pip install -r requirements.txt`. And a package installed only in the old interpreter (a browser driver, an HTTP client) must be re-installed in the venv or the service silently loses that capability.
   On Debian/Ubuntu VPS, `pip3 install` fails without `--break-system-packages` — the system Python is externally managed. Use `pip3 install --break-system-packages <pkg>` or create a venv.

   **SSH key management on hostkey.ru VPS.** The hostkey panel periodically rewrites `~/.ssh/authorized_keys`, dropping manually added keys — the symptom is `Permission denied (publickey,password)` on a key that worked an hour ago, and it recurs on every panel update or reboot. Re-adding the key works but only until the next rewrite; the durable fix is to make the file immutable:
   ```bash
   # one-time, after the key is confirmed working
   chattr +i ~/.ssh/authorized_keys
   lsattr ~/.ssh/authorized_keys      # expect the 'i' flag: ----i---------e-------
   ```
   **Confirm the key is present and SSH works BEFORE locking it** — an immutable file with no working key locks you out (the password path remains, but say so). To add another key later, the file must be unlocked first: `chattr -i ~/.ssh/authorized_keys`, append, then `chattr +i` again. Leave a stray blank line alone rather than unlocking the file to tidy it — `sshd` ignores blank lines, and any edit is a chance to lose access.
   - **Google Auth + FastAPI: alias the conflicting `Request` import.** `from google.auth.transport.requests import Request` conflicts with FastAPI's `Request` — FastAPI tries to parse it as a response model and crashes with `FastAPIError: Invalid args for response field`. Import it as `from google.auth.transport.requests import Request as GoogleAuthRequest`.
   - **When deploying to a VPS, verify the app's internal path resolution.** If `BASE_DIR` is derived from `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (assuming the project root is one level up from the script), but on the VPS the script sits directly in the project root, the path resolves to `/root/frontend/assets` instead of `/root/smm-panel/frontend/assets` — the service crashes with `RuntimeError: Directory does not exist`. Use `os.path.dirname(os.path.abspath(__file__))` for scripts that live at the project root.
   - **When restarting a service on a VPS, the old process may still hold the port.** `systemctl restart` fails with `address already in use` because the previous process hasn't fully exited. Find the listener with `lsof -ti:<port>` and `kill -9` it before restarting. Check `journalctl -u <svc> -n 30` to confirm the port conflict, not a code crash.
   Useful hardening for a panel: `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=full`, `ReadWritePaths=<app dir>`.

   **A panel with scheduled work needs a SECOND unit, not a thread in the app.** When the product's core promise is "publish at time T", run the poller as its own systemd service alongside the web app (both `Restart=always`, `After=`/`Wants=` linking them). A background thread inside the web process dies with the process and cannot be restarted independently; two units can be restarted, logged and debugged separately. When both share one SQLite file, the schema migration must live in the shared module and run from BOTH entry points — starting the worker first must not crash on a missing column. Full shape, including the atomic claim that makes it safe to run twice: `references/scheduled-worker-queue.md`.

**FastAPI route ordering: a query-string path and a path-param path collide.** `@app.get("/api/content-plans")` with `account_id: Optional[int] = None` and `@app.get("/api/content-plans/{plan_id}")` — FastAPI registers them in order, so the first one matches every call including `/api/content-plans/5` (parsing `"5"` as `account_id`). The symptom is a 500 or wrong result on the single-item endpoint while the list endpoint looks fine. Register the more specific path first (`/{plan_id}`), or use a different prefix (`/api/content-plans/id/{plan_id}`), and verify both endpoints in the same test pass.

4. **Reload, don't restart, the proxy — and verify the neighbours.** `nginx -t` in the container, then `nginx -s reload`. Then curl the panel *and* every pre-existing route on that host. Editing a shared vhost is the highest-risk edit in this procedure; the sibling routes returning their normal status is the evidence that nothing else moved.

**Adding a new OAuth callback route for a provider.** When integrating a new OAuth provider (YouTube, VK, TikTok, etc.), add a `location ^~ /smm/oauth/callback/<provider>/` block *before* the general panel proxy block. The callback proxy_pass must point to the exact API path (`/api/oauth/callback/<provider>/`). Insert it in the nginx config file on the host bind-mount, run `nginx -t`, then reload. Verify with `curl -s https://domain/smm/oauth/callback/<provider>/` — it should return JSON (401 without auth), not HTML.

**Order of location blocks matters.** Nginx picks the longest prefix match. Put specific callback routes (`^~ /smm/oauth/callback/.../`) *before* the general panel proxy (`^~ /smm/`). If the general block comes first, callbacks fall through to the SPA and return HTML instead of JSON.

**Verify each callback endpoint after reload.** Curl the callback URL directly — it must return JSON (`{"detail":"Unauthorized"}` without auth). If it returns the SPA index.html, the location order is wrong or the prefix isn't stripped correctly.

   **Repointing an existing app to a new backend means removing the old `location` in the same edit.** Two `location = /prefix/` blocks (or two `^~ /prefix/`) are a hard config error — `nginx -t` answers `duplicate location "/prefix/"` and the reload is refused, so the old route keeps serving while your new one is dead. Before adding the replacement, grep the vhost for every block whose path matches the prefix (`location = /prefix/`, `location ^~ /prefix/`, the bare redirect) and delete them all in one pass; then `nginx -t` must pass before `reload`.

   **`curl -I` reports a false `Content-Type` for a `BaseHTTPRequestHandler` app.** The class answers any verb with no `do_<VERB>` hook — HEAD included — with `501` and its default `text/html` body, so `curl -I` shows a JS file as `text/html` with a bogus length while the same path is served correctly on GET. Read headers with `curl -sD - -o /dev/null` (a real GET) before concluding there is a MIME problem.

5. **Auth: prefer a login form over HTTP Basic.** Basic auth only prompts the browser when the `401` carries a `WWW-Authenticate` header. Without it the browser renders the response body — so a JSON API answering `401 {"error":"unauthorized"}` shows the user a raw JSON page and no password field. Either add the header or, for a human-facing panel, do the form:
   - `GET /panel/` unauthenticated → **HTML** login page, not a JSON 401. JS calling `/api/*` should still get JSON — the two audiences differ.
   - `POST /panel/login` with the password → `302` + `Set-Cookie: sid=…; HttpOnly; SameSite=Strict; Max-Age=…`.
   - In-memory sessions with a TTL are fine for a single-operator panel; say plainly that a service restart logs everyone out.
   - Sleep briefly on a wrong password. It is the cheapest brute-force brake there is.
   - Keep Basic and Bearer working *alongside* the session cookie so your own curl probes and inbound hooks keep functioning.
   - **In FastAPI, `response.set_cookie()` on an injected `Response` param can silently fail** — the cookie header may not reach the client. The reliable pattern is to construct a `JSONResponse` directly and call `.set_cookie()` on it before returning.

**Multiple OAuth providers on one panel.** When the panel integrates with several social APIs (YouTube, VK, TikTok, Instagram), each gets its own `/api/oauth/<provider>/start` and `/api/oauth/<provider>/callback` endpoints. Store tokens per provider in separate tables (`youtube_tokens`, `vk_tokens`, etc.) linked by `account_id`. Frontend polls `/api/accounts/<id>/<provider>/status` after opening the OAuth window to detect connection completion.

**VK: split it by target — "the API is closed" is too blunt and will make you refuse work that succeeds.** Video upload is closed (`video.save` needs the `video` scope, which VK ID does not issue; `oauth.vk.com` and the old app types are gone, and VK ID scopes are login-only). But a **community token posts to a community wall with no OAuth and no business verification at all** — verified end to end with a real post — so build that first and treat video as the closed half. Photos on that post need a second, user token (see below). Never promise the photo half before a real post lands: implicit-flow user tokens are IP-bound and `offline` is a per-app grant, so a token minted on the operator's machine can be rejected by a VPS publisher. Full breakdown, the community-token scope mask, and the app-classification ladder: `references/social-publishing-api-viability.md`.

**A provider's authorize endpoint classifies the app for you — read `error_description`, not the docs.** VK answers `application is disabled` (typically a **Mini App**, which can never mint an API token — recreate as Standalone), `invalid scope` (that app is not permitted that scope), `application was deleted` (stale client_id), or a login page (app live, flow available). Probe **one scope per request with a pause** — a burst gets rate-limited into a bot wall that reads as a different failure — and compare against a known-live public app id in the same probe to separate "this app is broken" from "the endpoint is broken". The same shape applies to any provider whose token issuance is gated: the failure text names the class or state, so a wrong app TYPE is diagnosed in one call instead of after a rebuild.

**A user token unlocks VK's read and delete paths that a community token is refused.** With a user token the full wall lifecycle works — verified live: `photos.getWallUploadServer` → upload → `photos.saveWallPhoto` → `wall.post` with `attachments=photo{owner}_{id}` published a photo post, and `wall.get` / `wall.delete` then read and removed posts (`deleted: 3`, wall dropped 4 → 1). A community token answers error 27 for every one of those. So the honest split is: community token for publishing, user token for photos, reading and cleanup — and if the user wants post cleanup (a common requirement), the user token is mandatory, not optional.

**Verify a candidate OAuth app in a BROWSER, not with curl — a server-side probe lies about the consent screen.** Kate Mobile (`2685278`) accepted every scope in a server-side request yet rendered `Access denied [15]` on the real consent page, so the user could never press Allow. `VK Me` (`6287487`) rendered a clean consent page for the same scopes. A probe that only reads the HTTP status and body cannot tell the two apart.

**VK ID (id.vk.ru) does NOT issue API scopes — it is login-only.** VK ID issues `vkid.personal_info`, `email`, `phone` only. It cannot mint a token with `wall`, `photos`, or `video` scope, regardless of the app type configured. The only working path for community-wall posting is the legacy Standalone flow via `oauth.vk.com/authorize?scope=photos,wall` — a standalone app with `offline` scope in 2026 yields `expires_in=86400` (24 hours), not `0` (unlimited). Community tokens (created in group → Управление → Работа с API) remain unlimited. Treat the 24-hour expiry as a design constraint, not a bug to fix.

**`offline` in the scope no longer yields a permanent VK token.** A request with `scope=photos,wall,offline` came back `expires_in=86400` — 24 hours, not 0. Treat a VK user token as a daily-renewal cost in the design, not a one-time setup, and say so before building a flow that depends on it. The IP-binding worry is smaller than it looks: VK ID docs state confidential apps' tokens are NOT bound to an IP by default.

**A role column is not access control — scoping needs two axes and server-side checks.** A panel with `role: admin|manager` in the DB and a `require_auth` on every endpoint still lets any manager read and mutate everything; the role only hides a nav item. Model the real boundary as (1) WHICH containers the user owns (a `user_folders` join table) and (2) WHICH functions they may call (per-user boolean flags), then enforce both in the API: `require_perm(request, "delete")` for the verb, `require_account_scope(conn, user, id)` / `assert_folder_allowed(conn, user, folder_id)` for the object. The UI hiding a button is cosmetic — say that out loud in the code comment so nobody later "optimises" the server check away.

**Scope the LIST queries, not just the single-row ones — and make an out-of-scope filter return empty, not everything.** A manager's `/api/accounts` must be filtered by their folder set at the SQL level, and an explicit `?folder_id=<someone else's>` must yield zero rows rather than falling through to the unfiltered branch. The same applies to the dashboard counters: counting all accounts leaks the size of folders the user cannot see, so every number on the page has to be computed through the same scope. Verify by asking for the foreign id and asserting the row count is 0, not by checking the UI looks right.

**Prove isolation with the negative cases, not the positive one.** The test that matters is what a restricted user CANNOT do: delete a foreign account (403), create inside a foreign folder (403), list users (403), delete a video without the flag (403), and — the subtle one — request a foreign `folder_id` and receive an empty list rather than the whole table. Also confirm the admin path still returns `None`/all (an over-eager scope check that breaks the admin is the usual regression here), and that a disabled user (`is_active=0`) is refused at LOGIN and on existing sessions, not merely at session expiry.

**Guard against lockout when the same screen can demote the last admin.** Refuse self-deletion, refuse demoting the last admin, refuse deleting the last admin — each as a `400` with a reason. These are one-liners that only matter the day someone clicks the wrong row, and by then the panel is unreachable without a DB edit.

**FastAPI route order is load-bearing when the app also serves an SPA.** A catch-all `GET /{path:path}` placed before `GET /api/content-plans/{plan_id}` silently intercepts the API call and returns `text/html` (the SPA's index.html) — POST routes still work, making the bug look like a Content-Type problem. When a GET on an API path answers HTML, list the registered routes on the live process and check for a catch-all declared earlier in the file. Move the catch-all AFTER all API routes.

**A VK Mini App cannot mint an API token at all — the app TYPE decides, and one probe tells you which you have.** `oauth.vk.com/authorize?client_id=<ID>...` answers `application is disabled` for a Mini App, `application is blocked` for a banned one, `incorrect app. Unavailable for apps with direct auth.` for the mobile clients, `invalid scope` when it rejects `offline`, and a normal login page only for a usable Standalone app. Probe before writing any flow: the failure surfaces as a bare error string with no hint that the type is wrong, and users routinely hand over their **user_id** (shown as "ID: …" next to their name in the developer panel) believing it is an app id. Confirmed live: `2685278` accepts `photos,wall,groups,manage,offline`; `6121396` is blocked; `6146827` and `2274003` refuse direct auth.

**An implicit-flow user token is IP-bound, so a token minted on the operator's laptop can fail on the server.** The working combination for a community wall is: community token publishes (`wall.post`), user token uploads photos (`photos.getWallUploadServer`, which the community token cannot call). Getting a non-IP-bound user token means Authorization Code Flow, which needs extended app verification (ИП/самозанятость/юрлицо). Say this trade-off out loud before building — a daily-expiring, IP-bound token is a support burden, not a feature.

**A community token can ONLY `wall.post` — map the boundaries before promising delete/read features.** Verified against a live community: with `wall, photos, manage` granted, `wall.post` succeeds while `wall.get`, `wall.getById`, `wall.delete`, `wall.edit` and `photos.getWallUploadServer` ALL answer error 27 ("method is unavailable with group auth"). `groups.getById` and `groups.getTokenPermissions` work. So a panel driven by a community token can publish but cannot verify what it published, cannot delete a bad post, and cannot upload a photo — say this to the user up front rather than discovering it at the delete feature.

**To read a VK community wall with no token at all, use the public widget.** `https://vk.com/widget_community.php?app=0&width=300&_ver=1&gid=<ID>&mode=2` renders posts server-side for embedding and needs no auth. Two traps: it serves **cp1251** (decode accordingly or the text arrives as mojibake), and VK rate-limits it — frequent requests return a JS shell or the "У вас большие запросы" page, so send one request with `Referer: https://vk.com/club<ID>`, save the body to disk, and parse the saved copy instead of re-fetching. Direct page fetches (`vk.com/wall-…`) hit a bot captcha from datacentre IPs even with a browser User-Agent.

**Accept a community reference in every form the operator might paste, and store the numeric id.** `204149473`, `-204149473`, `public204149473` and `club204149473` all resolve through `groups.getById`, and VK normalises `public…` to `club…` — so the screen name is NOT a stable key. Resolve once at connect time, keep the numeric id, and never require the user to convert the link themselves.

**A community wall post needs TWO VK tokens, and that is VK's doing, not a design choice.** A community token CANNOT upload photos: `photos.getWallUploadServer` and `photos.saveWallPhoto` answer error 27 / code 15 ("no access to call this method") while the same calls with a USER token succeed. `wall.post` works with either. VK tracks this as an open bug (`VKCOM/vk-api-schema#242`, open since Apr 2026) and the accepted workaround — photos via user token, post via community token — is used inside VK's own schema repo. So: **community token** (group → Управление → Работа с API → создать ключ; no OAuth at all) publishes, **user token** with scope `photos` uploads. Build the flow as four calls — `photos.getWallUploadServer` (user) → POST the file with the multipart field named exactly `photo` → `photos.saveWallPhoto` (user) → `wall.post` with `attachments=photo{owner_id}_{id}` and `owner_id=-group_id` (community).

**Probe the ONE call that separates the two token types instead of discovering it after the build.** `photos.getWallUploadServer` is cheap and is precisely what a community token cannot do, so it is the honest test of whether photo posting will work. The stored flag (`can_photo`) should come from that probe, not from the token merely existing — a token that authenticates is not a token that can do the work.

**VK answers HTTP 200 with the error in the body, so a status-code check reports success on every rejection.** Read `payload["error"]["error_code"]` and translate the ones an operator will actually hit: 15 (missing scope — name which token needs which scope), 27 (method unavailable for a community token — photos need a user token), 5/6 (dead token), 214 (no admin rights on that community), 100 (bad params).

**A `DELETE` on a parent row fails with `FOREIGN KEY constraint failed` once any child table references it — clean the children first.** With `PRAGMA foreign_keys=ON`, an account that has ever been connected (tokens row) or scheduled (posts row) becomes undeletable, and the panel answers 500 on the operator's most ordinary action. Delete from every child table (`vk_tokens`, `youtube_tokens`, `scheduled_posts`, `profile_applications`) before the parent, and guard each with a table-exists try/except for older databases.

**A status the panel reports must come from the platform, and "cannot check" is a status.** A simulated verdict (`random.choice(["active","active","banned"])`) is worse than no feature: it marks healthy accounts banned and vice versa, and the operator deletes real accounts on its word. When a check is genuinely impossible (no token, network not wired up, API closed), return a distinct `unknown` carrying the reason — never a guess.

**An indeterminate result must NEVER overwrite a known one.** "I could not check" is not evidence that the account is fine, so writing `unknown` over a manual `banned` mark silently destroys what the operator entered by hand — and it happens on every bulk run. Record `last_checked` and the reason always; write the status column only when the check actually determined something. Same rule for any derived field: partial information must not clobber complete information.

**Before promising a profile/bio/avatar feature, verify what the platform's API actually allows — the answer differs per network.** Telegram's Bot API does all of it (`setChatTitle`, `setChatDescription`, `setChatPhoto`, bot must be admin with `can_change_info`). YouTube edits the channel description only with the `youtube`/`youtube.force-ssl` scope and cannot set an avatar at all. An aggregator that publishes content (Upload-Post) exposes NO profile-write endpoint — changing bio there needs browser automation. Probe with a real write and read the error (`403 insufficientPermissions` names the missing scope) instead of assuming; then report per-field what worked and what did not, with the reason. A silent no-op that reports success leaves the operator believing 50 accounts were filled when none were.

**A write that returns 4xx because the value is already correct is a SUCCESS, and it may arrive as an exception.** Telegram answers `400 chat description is not modified` / `CHAT_NOT_MODIFIED` when the profile already matches; the HTTP helper raises on any non-2xx, so the handler must catch it and map it to success or every repeat run reports a healthy account as broken. Same class as `409 already exists` on an idempotent create.

**Reordering the arguments of a POST body is not the only bytes trap: an HTTP helper that passes `data` straight to `urllib.request.Request` needs `bytes`, not `str`.** Passing `json.dumps(...)` raises `TypeError: POST data should be bytes` — and the traceback points at the helper, not at the call site that got it wrong.

**Two writers on one SQLite file need `busy_timeout`, or writes fail the moment the other one is active.** A bare `sqlite3.connect()` fails instantly with `database is locked`; the symptom is a 500 on an unrelated endpoint (a DELETE, a create) that works fine whenever the scheduler is idle. Set `timeout=30` plus `PRAGMA busy_timeout=30000` and `PRAGMA synchronous=NORMAL` alongside WAL, in EVERY module that opens the DB — the web app, the worker and any helper each have their own `get_db()`.

**A token that authenticates is not a token that can do the work — refresh it, do not trust a stored one.** `google-auth`'s `Credentials` with no `expiry` treats the stored access token as valid forever, so it is used long after it died and every call 401s; the operator reads that as "reconnect the account" although the refresh_token is fine. Always call `creds.refresh()` when a refresh_token exists, and check the granted `scopes` (via `tokeninfo` when the token predates scope storage) before claiming a write will work.

**When a paid platform's onboarding is blocked, ship a free transport instead of stalling.** Telegram's Bot API is the cheapest working publish path in this class — a bot token costs nothing, needs no review, and posts to any channel the bot is a member of — so it proves the whole path (panel button AND scheduler worker) while the blocked argument is still open. The destination is the account's own field (`@channel`, or the numeric `-100…` id when the channel is private), one row per destination. Mechanics, the three-call capability probe and the 50 MB video cap: `references/social-publishing-api-viability.md`.

**Probe the credential's capability before writing the transport — a token that authenticates is not the question.** Whatever the transport (bot token, OAuth token, aggregator key), run the cheap read calls first and confirm the *destination itself* will accept a post: is the bot an admin carrying `can_post_messages`, does the aggregator's accounts object list the platform at all. Validity and reachability are different facts, and an upload to an unreachable destination is the failure found at the end of the build instead of the start.

**Never leave a token the user pasted into a chat in place.** A bot token sent over the conversation is compromised the moment it lands; store the value in the secrets dir and tell the user to revoke and reissue it, then swap the replacement in. Say it plainly rather than silently keeping a burnt credential in production.

**Async OAuth callbacks with httpx.** Providers that require a server-side token POST (VK ID, other OAuth 2.1 providers) need the callback handler to be `async def` with `httpx.AsyncClient()`. FastAPI handles async route handlers natively.

6. **Bounded validation on every write endpoint.** Reject non-`YYYY-MM-DD` dates and out-of-range times before touching the database, with a `400` naming the field. Assume nothing about the input being well-formed because the UI produced it.

7. **Model the real domain status values, not the ones that sound right.** Read what the writer actually writes and what the reader filters on. A booking stored as `locked` while the UI greys out `booked` produces a permanently empty panel and an error-free-looking system — the most expensive kind of quiet bug. When a value is written in exactly one place, treat that place as the schema and grep every reader for it, including ones that look unrelated (a grid, a list, a summary).

8. **In a UI picker, block by time INTERVAL OVERLAP, not by exact start-time match.** A booked 60-minute slot must grey out every 30-minute button inside it, or changing the duration setting silently creates double-bookings. Test the real render function against real rows at every offered duration rather than reading the code:
   ```
   occupied 13:30–14:30, 14:30–15:30
   30-min buttons busy: 13:30 14:00 14:30 15:00            (4)
   60-min buttons busy: 13:00 13:30 14:00 14:30 15:00     (5)
   ```
   Also surface bookings that fall outside the grid entirely, or they become invisible.

   With several parallel resources (boxes, rooms, masters), a start time is
   bookable only while the *required number* of resources stays free across the
   whole interval **including the buffer** — count occupied resources at every
   breakpoint inside the window, not just at the start, and let the server pick
   the specific resource at booking time so the UI list is advisory and the DB
   constraint is the real guard. Read the venue's per-weekday hours from config
   instead of hardcoding one grid: an empty array for a weekday means closed,
   and the last start is bounded by `start + duration + buffer ≤ closing`.

9. **Verify in the artifact the user will look at.** For a browser panel, execute the actual client logic outside the browser and print its output — Node plus a small DOM shim is enough for a pure render function. Eight harness iterations is still cheaper than shipping an unverified grid.

   **When a JS panel renders an empty shell, bisect delivery before logic.** The signature: HTML paints, containers stay empty, no console error. `node --check` the served file and run it under Node with a DOM shim — if it executes cleanly there, the script is fine and the fault is delivery, so stop reading app code and check the URL the browser actually resolved for the script and for the first fetch (status + content-type through the proxy). The decisive probe is whether the app's top-level functions exist after load; read that off `document` state (a container's child count, an input's value), never through a helper that wraps your expression in an IIFE — the wrapper cannot see globals and reports `undefined` for code that did load.

10. **Any state change must repaint what the outside world already saw, and you must exercise the empty path.** A panel that mutates a row but leaves the published/shared artifact stale is the classic half-done feature: the DB is right, the client's view lies. Give every mutating endpoint the same repaint call — publish, cancel, withdraw, unpublish — and let it report repaint success as part of its response so the UI can say so. Two traps specific to repainting:
   - **Resolve the shared artifact's id across ALL rows of the entity, not the rows still in the live state.** Withdrawing the last free item leaves no live rows, so a lookup restricted to them fails exactly when the repaint is most needed. Fall back to any row carrying the id.
   - **Test the state where the collection is EMPTY, not just the happy path.** An empty result is where truthiness bugs live: `len(rows or 0)` raises `TypeError` where `len(rows)` returns 0, and the crash lands on the destructive operation the user actually performs. Run publish → mutate-to-empty → repaint as one scenario and read the shared artifact back.

11. **Withdrawn rows are history, not schedule — hide them.** A terminal status left in the list reads as live state ("снято" next to real slots) and forces the user to mentally filter. Filter terminal statuses out of the schedule view entirely; they belong in an audit view, if anywhere.

12. **Closing a leaked privileged key means a server-side proxy, and the proxy has to cover every verb the page used.** Fetch the live page, decode the JWT, then add a forwarding route on the app that already talks to that service server-side: the page keeps its `fetch` calls, only the base constant changes, and the key moves to `/root/.secrets` where it never leaves the box. Three traps, each of which costs a broken prod:
   - **`BaseHTTPRequestHandler` answers 501 for any method without a `do_<VERB>` hook, and it answers *before* your code runs** — a proxy that implements only GET/POST turns a `DELETE` into an nginx 502 and a traceback in the journal. Enumerate the verbs the frontend actually sends (`grep -n "method: '" <file>` plus every storage/upload path) and write a hook for each.
   - **A proxy `location` that nests inside a static prefix must be listed first.** `^~ /app/api/supabase/` and `^~ /app/` both match `/app/api/...`; nginx picks the longest prefix, but when you insert the proxy block *after* the static block in a file you are re-reading by eye it is easy to misjudge — verify by curling the new route immediately after `nginx -s reload`, not by reading the config.
   - **Deploy the file the way the container actually stores it, and prove it.** Files under `/usr/share/nginx/html` live inside the container: a host-side `cp` to that path fails outright, while `docker cp` lands. After any deploy, `md5sum` both the source and the copy in the container and require them to match before declaring it live.

   **Regression-test the service you added the route to.** Adding a proxy endpoint to a process that already serves a working panel is an edit to that panel's prod: re-run its login, its main API and its health route after the restart, and say so in the report. "I fixed X without breaking Y" is only a claim once Y answered with its normal status.

   **Write the fix's own comments so they do not trip the leak grep.** A comment containing `service_role` or `apikey` makes the clean page match the exposure pattern you will run next time. Describe the mechanism ("the DB key stays on the server") without naming the credential type.

12. **Leave no test residue in the user's real systems.** Publish only into a far-future date, delete the rows, delete the messages, unpin, and read each back. Then state plainly what is left: rows count, messages count, pin state.

13. **A per-user notification channel is not always open, so give it a fallback.** Messaging platforms commonly refuse a bot-initiated first message to a user who never wrote to it — MAX answers `404 dialog.not.found`, which looks like a bad id and silently drops every notification on a fresh audience. Put the chat the user actually reads first, and fall back to it when the direct channel is closed: detect the specific not-open error, then re-send there. Report which route was used in the response body so the UI can tell the user the truth. A cancellation notice that reports "sent" while nothing was delivered is worse than one that reports the failure.

14. **When the panel shares one published artifact with an automation, decide who owns its text — and say which.** Once both the panel and a workflow write the same shared message, every mutation path must repaint it, and each writer will format it its own way until the two texts disagree in the same chat. Either route all repaints through one code path, or pin one owner explicitly and have the other request a repaint. The numbering/ordering rule inside that message has to be identical in every writer, or digits point at different rows depending on which surface produced them.

15. **Front-end controls must send the verb the server actually routes, not the verb that reads naturally.** A logout button wired as `location.href = '/panel/logout'` issues a GET; a handler registered only under POST answers `404 {"error":"not found"}` and the user sees raw JSON where the app should be. Either the button submits a real POST form, or the server accepts both verbs. When the user reports an action landing on an error page, compare the JS verb with the route table before debugging anything else.

   Two defects hide behind the same visible symptom, and both are worth fixing in the same pass:
   - **The cookie is not cleared on logout.** Invalidating the session server-side while leaving `Set-Cookie` alive means the browser keeps presenting a dead id. With in-memory sessions a restart papers over this; with file- or DB-backed sessions the user stays "logged in" with no way out. Always send `Max-Age=0` on the way out.
   - **Logout does not require a valid session.** Anyone holding the cookie can destroy that session. Make the handler idempotent and harmless without one (still redirect, still clear the cookie) so a double-click cannot error.

16. **Ship light and dark as tokens, or the second theme is a rewrite.** Hardcoded hex inside rules (`background: #212a33`) cannot be re-themed — adding light mode then means re-editing every rule and hunting for misses. Put every colour in one block per theme and let all rules reference `var(--*)`. The shape to hold: `data-theme="dark"` on `:root` plus one `[data-theme="light"]` override, the choice persisted in `localStorage`, and an inline script in `<head>` that applies it **before first paint** — otherwise a light-theme user gets a dark flash on every load. The login page needs the same script and the same key, or the theme resets when they sign in.

   Verify both themes by computing contrast from the served CSS rather than eyeballing: parse the token blocks and run the WCAG relative-luminance formula against every text/background pair. The first draft of a light theme reliably fails two pairs — secondary text on the background, and text on the accent-coloured primary button — so compute first and darken those two tokens until they clear 4.5:1 rather than shipping them.

## Business-scoping decisions: ask before building

When a product could be built as a quick one-off or as a scalable multi-tenant
service and the user has not said which, ask before writing code — the two
shapes have different data models, and re-doing the model after the first build
is the expensive part. Cover, in one round:

1. **Platform** — which messenger(s), or a web surface. This fixes the whole
   client layer.
2. **Scale** — one instance now with a `service_id` parameter, or multi-tenant
   from the start. Recommend the first: it validates faster, and the parameter
   is what makes the later fork cheap.
3. **Where state lives** — a separate database project for the new product or a
   new table in an existing one. Recommend separate when the existing project is
   someone else's production data: two products' rows in one schema mix
   ownership, and one bad query crosses the boundary.

Also: when a parser/scraper has already produced the market list (a niche in a
city), say out loud that those rows are the product's first customers — the
sellable unit is the service, not just the build.

**Once multi-tenant is chosen, the tenant is a generator, not a hand edit.** One
command or API call creates the whole row-set (tenant + its services + boxes +
owner with a PBKDF2 password), returns the owner credentials exactly once, and
the shared app serves the new tenant at `/s/<slug>` with zero code changes.
Check slug uniqueness before inserting; and when the schema holds a global
UNIQUE on the owner login, derive it from the slug (`<slug>_admin`) — a shared
`admin` login collides on the second tenant. The correct schema is
`unique (tenant_id, login)`, but that DDL needs a direct database connection
string: Supabase REST has no `exec_sql` and the secrets hold only URL + anon +
service keys — ask the user for the connection string before promising the
migration. Prove isolation by reading both tenants' rows and confirming the id
sets are disjoint.

## Telegram Mini App: the client-facing booking surface

A Mini App is the opposite shape from the panels above: **no password login**
— the auth is the Telegram `initData` signature. The layout is static
HTML/CSS/JS plus a small API bound to `127.0.0.1` and proxied under its own
`location`, exactly like any other app on a busy host.

- **Auth: validate `initData` with HMAC-SHA256.** The key is
  `HMAC_SHA256("WebAppData", bot_token)`, and the signed string is every
  `key=value` pair sorted, minus `hash`. When no token is configured yet
  (early build), parsing `user` out of `initData` without verifying is
  acceptable — but gate that branch on an explicit flag and say so, because an
  unverified `client` field is attacker-controlled.
- **Enforce the booking guard in the API, not the UI.** The client only ever
  moves a slot `free → locked`; a second request for the same slot returns
  `409 {"error":"taken"}`. The UI disables the tapped button immediately, but
  the race is only actually closed server-side.
- **Notify the owner from the API on a successful booking, and never let the
  notify break the booking.** Read the owner's chat id from the secrets dir
  (empty = notifications off), convert the stored UTC timestamp to the venue's
  fixed offset for the message text, and wrap the send in try/except so a failed
  notification cannot turn a `200` booking into an error. The `409 taken` guard
  stays the only thing the client's request depends on.
- **Owner writes get their own token-gated endpoint.** `POST /api/admin/slots`
  with `X-Admin-Token` read from the secrets dir; when the token file is absent
  on a mock stage, accept anything and log that it is unguarded.
- **One flag switches the store, not two code paths.** A `USE_MOCK_DB`
  constant picks between an in-RAM mock and the real provider client; the API
  handlers never branch on it. When the real client lands, the change is one
  boolean plus a secrets file.
- **A Supabase-backed public app needs a deliberate RLS posture, not just a table.** The `anon` (public) key is what the browser holds, so RLS is the only thing between a stranger and the data. For a booking surface the correct shape is narrow: `select` on the rows the client must see, `update` restricted to the one transition a client may perform (`free → locked`), and **no `insert`/`delete` for `anon`** — those belong to the owner path. An all-open policy "works" on day one and is the hole you patch under load later.
  - **When you split one `do_POST` into per-route handlers, move the `Content-Length` read into every handler.** The old code read `length` once at the top of `do_POST`; after routing to `_handle_book()` the variable no longer exists, and every request on that route answers `400 bad json` while the curl command looks perfectly correct. The tell: one route on the same server works and another doesn't — they were refactored at different times.
- **A missing `delete` policy makes `DELETE` return HTTP 204 without deleting.** Supabase answers a no-policy delete with a success code and an empty body, so a cleanup curl "succeeds" while the row stays. Correct behavior (strangers must not delete), but it means test rows cannot be removed with the `anon` key — clear them through the SQL editor or a `service_role` path. Verify a delete took effect by re-reading the row, not by trusting the status code.
  - **Read only `anon` (public) keys into the client path; never `service_role`.** The `service_role` key bypasses RLS and must live server-side only. Decode the JWT's `role` claim to confirm which one you were handed before wiring it in.
- **A mock store lives in the server process's RAM.** Restarting the server to
  load new code empties it, so a test cycle always fails on the first booking
  attempt after a restart. Seed fixtures through the admin endpoint *in the new
  process* before testing.
- **`server.py` at the app root must import its own `scripts/` explicitly**
  (`sys.path.insert(0, …/scripts)`) — run it from anywhere, it will still work.
- **Never render a stored `timestamptz` by slicing the ISO string.** `dt.slice(11,16)`
  on a value the database returned as `2026-10-12T02:00:00+00:00` shows `02:00`
  when the master published `10:00`, so the panel disagrees with the client app
  and every published time is wrong. Convert once, in one helper the whole UI
  calls: `new Date(dt)` → shift by the venue's fixed offset → read
  `getUTCHours()/getUTCMinutes()` against that shifted date (the browser's own
  `toLocale*` is acceptable only when the reader is in that zone, which a remote
  operator is not). Publish-side code that builds `dt` as `YYYY-MM-DDTHH:MM+08:00`
  is correct — verify the display half by asserting a known slot renders as the
  time it was published with.
- **A mobile photo field needs an explicit Camera/Gallery choice, and the file
  must be stored per-input.** `capture="environment"` on `<input type=file
  accept=image/*>` opens the camera directly and removes gallery access entirely;
  users who want to pick an existing photo are stuck. Offer two buttons and
  set/remove the attribute **immediately before `.click()`** — the OS reads
  `capture` at click time, so toggling it earlier does nothing:
  ```js
  function pickPhoto(inputId, source) {
    const input = document.getElementById(inputId);
    if (source === 'camera') input.setAttribute('capture', 'environment');
    else input.removeAttribute('capture');
    input.value = '';      // so re-picking the same file still fires change
    input.click();
  }
  ```
  Keep the chosen `File` on the input itself (`input._file`), never in one
  shared global — with several forms on one page (arrival/output/return) a
  global leaks the photo chosen in form A into form B's submit. Add a "remove
  photo" link in the preview that clears both `input.value` and `input._file`.
- **Give every app its own loopback port** on a shared host, and note which
  port belongs to which app in the project KB so the next session does not
  proxy the wrong one.
- **Kill the old server by exact PID, from execute_code.** `ss -tlnp | grep
  <port>` names the listener; `pkill -f <pattern>` from the terminal tool also
  matches the tool's own shell wrapper and SIGTERMs the session. A background
  `server.py` that fails to bind keeps the *old* process silently serving stale
  code — confirm the PID changed after every restart.

## Shipping a Vite/React SPA under a path prefix

A built SPA (Vite + react-router) behind an existing vhost is a different shape from a
hand-written static page: the build emits **absolute** asset paths and the router owns the
URL space. Three settings must agree, and the failure of each looks different:

1. **`base: "/prefix/"` in `vite.config.ts`** — otherwise the built `index.html` references
   `/index-*.js`, the browser resolves them from the site root, they land in the
   catch-all `location /` that proxies to whatever else runs on the host, and answer **502**.
   The tell: `curl` of the page returns 200 while
   `performance.getEntriesByType('resource')` in the browser is **empty** — the shell paints,
   no bundle ever loaded. Confirm by grepping the built `index.html` for the asset prefix.
2. **`basename: "/prefix"` on the router** (second arg to `createBrowserRouter`, or a
   `<BrowserRouter basename>`). Without it every in-app link (`/s/demo`) drops the prefix
   and the first click leaves the app's URL space.
   - **`basename` only routes what goes through the router — a plain `<a href="/s/demo">`
     bypasses it and 502s.** An anchor is resolved by the browser from the site root, so
     it drops the prefix, lands in the catch-all `location /` that proxies to whatever else
     runs on the host, and answers 502 — every nav item, "back to storefront" link and
     breadcrumb written as `<a href>` is a latent 502. Internal navigation is
     `<Link to="…">` / `useNavigate` only; `<a>` is for external schemes (`tel:`,
     `https:`, `mailto:`) that basename does not touch.
   - **A hash goes inside `to`, not as a separate prop** — react-router 7's `Link` has no
     `hash` prop and rejects it as a TS error; write `to={`/s/${slug}#services`}.
   - After any change to nav links, assert the rendered `href` values carry the prefix
     (`document.querySelectorAll('nav a')` → `getAttribute('href')`) before calling it fixed.
3. **A static server with SPA fallback, not `vite preview`.** `vite preview` validates the
   `Host` header and answers **403** to a request arriving through the shared domain — the
   page is "down" for exactly the route you just wired. Serve `dist/` from a small Python
   server instead: serve the file when it exists, otherwise fall back to `index.html` so
   every client-side route renders. Normalize the path, strip a leading `..`, and remember
   the nginx prefix may already be stripped by `proxy_pass` (handle both forms). A ready-made
   server is in `scripts/spa-static-server.py`.

**Order of verification, cheapest first:** `npm run build` green → curl the page through nginx
→ curl one asset path → then the browser (`performance.getEntriesByType('resource').length` > 0)
→ then the app's own first fetch. Only the browser proves the bundle loaded; everything before
it can look fine.

## Making the served app installable (PWA)

`vite-plugin-pwa` over the same `dist/` server; every failure in this class is
one of three prefix/caching/data agreements breaking:

- Manifest `start_url`/`scope`/icons and the static server must carry the
  `base` prefix; map `.webmanifest` → `application/manifest+json`; build the
  icons from one SVG with `sharp` (an `.mjs` script — the project is
  `"type": "module"`).
- **Cache policy decides whether updates ever arrive:** SW/manifest/workbox →
  `no-store`, hashed `assets/*` → `immutable`, `index.html` → `no-store`.
- **Offline data is a data-layer concern:** cache the public reads in
  `localStorage` with a TTL and check `navigator.onLine` *before* the request —
  `supabase-js` hangs pending offline instead of rejecting, so a `catch`
  fallback never fires; a `Promise.race` timeout is the second guard.
- **Never set TanStack `networkMode: 'offlineFirst'` for this** — it skips the
  `queryFn` while offline and the cache fallback cannot run.
- Offline test in headless: `emulateNetworkConditions` does not change
  `navigator.onLine`; define it false via `Page.addScriptToEvaluateOnNewDocument`
  before navigating, then assert cached content + banner render.

Full recipe: `references/pwa-offline.md`.

**When React state must be set from an automation, the DOM value is not enough.** Assigning
`input.value = 'x'` does not trigger React's synthetic `onChange`; the field stays empty in
state and the submit button stays disabled. Use the native setter, then dispatch:
```js
const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
set.call(input, 'demo1234');
input.dispatchEvent(new Event('input', { bubbles: true }));
```
And never address React controls by position (`buttons[0]`) — React re-creates nodes on every
render and the index shifts mid-session; select by the text or role the user sees.

**Run a whole browser interaction inside ONE `browser_exec` call.** The browser tab can reset
to `about:blank` between calls (the CDP session drops), so a sequence split across calls fails
with "element not found" / null `getElementById` on the second call while the code itself is
correct — open, fill, click and assert in a single code block and return the state you need.
Inside `js()`, the native-setter trick can throw `Illegal invocation` (the expression runs in
its own context); when it does, fall back to plain `input.value = …` plus a dispatched `input`
event — sufficient on a vanilla page — or the `fill_input` helper.

**Backend for an owner cabinet follows the same loopback+proxy rule as any other app**
(`server` bound to `127.0.0.1`, `location ^~ /prefix-api/ { proxy_pass …/; }`), but its auth is
a short-lived signed session instead of a page password: PBKDF2-hash the password, mint an
HMAC token over `{owner_id, tenant_id, exp}` with a secret from `/root/.secrets`, verify the
signature **and** the expiry on every request, and answer `401` without a token. The hash
never leaves the server; the client holds only the session token.
- **An AI assistant inside a cabinet answers from fetched rows only.** Build the
  DB context (today / tomorrow / this week, statuses, revenue) into the prompt
  and write the system prompt to forbid inventing rows, amounts or dates; on an
  empty period it must say the period is empty, not guess. Verify with questions
  about empty periods and about exact figures — a hallucinated booking in a
  client-facing tool is worse than no assistant at all.

## Serving a demo or landing page for prospects

When the goal is showing work to a potential client (a portfolio page, a
demo of a paid tool), the demo is a public static page with **no backend, no
API calls, no credentials**. This is a different shape from the production
panel:

- **A self-contained demo page** (pure client-side JS with fake data in
  `localStorage`) is safe to link publicly. It never touches the production
  database, never authenticates, and cannot be used to write real state.
- **The production panel stays password-gated and is never linked publicly.**
  A prospect with a live admin URL can publish, cancel, and reschedule real
  business operations. Show the sandbox, offer live access on request only.
- Verify the demo page with `curl` from outside before adding it to any reply
  or outreach: a 200 with the expected `<title>` is the minimum bar.
- The nginx `location` block follows the same pattern as any static route:
  `location = /demo/ { root /usr/share/nginx/html; try_files /demo/index.html =404; }`.
  Add it to the same bind-mounted vhost file as the other routes.
- If the demo simulates an action (a "publish" button that sends nothing),
  label it in the page: «данные никуда не уходят — это демо». A prospect who
  clicks "publish" and nothing happens is confused; a label prevents that.

**A portfolio page is a living artifact — update it when a new strong project ships.**
A demo worth adding to the portfolio goes in three places, and stopping at one
of them is a half-done job: the demo card (with the link and any demo
credentials) and the matching service card in the page itself, the marketplace
profile note in the KB (`clients/<marketplace>-profile.md` — demo links table
plus the new niche it opens), and the project KB entry recording which demo
URLs prove the new capability.

- **Verify every demo link returns 200 publicly before adding it to the page**
  — the portfolio is the face a prospect judges the work by, and one dead link
  in it costs more trust than the missing project does.
- **Never put a production panel URL in a public portfolio** — link the
  sandbox/demo, and offer live access on request only (the rule above still
  holds; the portfolio is the most public place it applies to).
- **After editing the page, prove the served bytes changed**: grep the served
  response through the proxy for the new project's name and match the byte
  count against the edited file. A `no-store` header does not help when the
  container is serving a different file than the one you edited — see the
  nginx-container deploy rule for how that happens.

## Deploying into the nginx container

Static files in the nginx container (`/usr/share/nginx/html/`) are not on the
host filesystem. A host-side `cp` to that path fails; `docker cp` is the
correct deploy:

```bash
docker exec <nginx-container> mkdir -p /usr/share/nginx/html/<name>
docker cp /host/path/index.html <nginx-container>:/usr/share/nginx/html/<name>/index.html
```

Verify with `md5sum` on both sides after the copy. The source file lives on the
host — save it in the project directory before or after `docker cp` so the next
session can find it. Never assume the host path `/usr/share/nginx/html` is the
same file system as the container's path of the same name; they are different
mount namespaces.

**The host keeps its own stale copy of that path, and editing it changes nothing.**
When `/usr/share/nginx/html` is not bind-mounted, the host still has a directory
of the same name holding an older snapshot of every file, so the file you edit
and the file the container serves look identical by path and differ by content.
The symptom is a page that returns 200 while searching the served response for
your new text comes back empty and the byte count matches the old version.
Diagnose by comparing three sizes — `wc -c` on your edited file, `wc -c` on the host copy, and
`docker exec <ctr> wc -c /usr/share/nginx/html/<path>` on the served file — then
`docker inspect <ctr> --format '{{range .Mounts}}...{{end}}'` to confirm the
path is absent from the mount list. Only `docker cp` (or the bind-mounted path,
if one exists for the config) is durable; a host-side `cp` into an unmounted
`/usr/share/nginx/html` is a no-op for the prod page. Always finish with a
`curl` grep for the signature text and a byte-count match before calling a
static deploy live.

## Hosting client-facing documents (КП, audits, reports)

A document the client must download — a proposal, an audit, a report — needs a
URL you can paste into a chat, not only a chat attachment. Reuse the existing
vhost and one static prefix for all of them, so every future document is one
`docker cp` and no config edit.

```nginx
# ── client documents (public PDFs) ──
location ^~ /kp/ {
    root /usr/share/nginx/html;
    try_files $uri $uri/ =404;
    add_header Cache-Control "no-store" always;
}
location = /kp { return 301 https://$host/kp/; }
```

```bash
docker exec <nginx-container> mkdir -p /usr/share/nginx/html/kp
docker cp /root/<project>/proposal.pdf <nginx-container>:/usr/share/nginx/html/kp/proposal.pdf
docker exec <nginx-container> nginx -t && docker exec <nginx-container> nginx -s reload
```

Publishing a later document is only the `docker cp` line — the route already
exists. Adding the route is a production write to a shared vhost: back up the
vhost file first and `nginx -t` before the reload.

- **The prefix route is what makes documents durable; the source file is not.**
  A generator script left under a cache/scratch path is pruned on a timer while
  the copy inside the container survives. Move the generator and the source PDF
  into the project directory (`/root/<project>/`) in the same session you first
  publish one, or the next session cannot regenerate it.
- **Use the prefix form (`^~ /kp/` + `try_files $uri $uri/`) for a document
  collection**, not the exact-match `location = /demo/` form that serves one
  file. The prefix form serves every file under it with no further config.
- **Verify from outside, and verify the neighbours.** `curl` the new URL (expect
  `200` and `content-type: application/pdf`) and `curl` every other route on the
  vhost in the same pass — adding a block to a shared vhost carries the same
  risk as any other edit to it.
- **Match the bytes, not just the status.** `md5sum` the host source and
  `docker exec <ctr> md5sum <served path>` must agree; a 200 proves a file is
  there, not that it is the file you just built.
- **Say the link is public.** Anyone with the URL can fetch it. Fine for a
  proposal with no confidential content; when the document carries pricing or
  client data, say so and offer a password before publishing.

## Serving static content that a bot or agent references

When a systemd cron job delivers output to a Telegram topic (chat_id + thread_id),
the topic must be in the format `telegram:<chat_id>:<thread_id>`. The chat_id
comes from the gateway log; thread_ids come from session store entries
(`telegram:group:<chat_id>:<thread_id>`). After editing a cron target, always
run the job manually and check `delivery_outcome: delivered` in
`/root/.hermes/cron/executions.db` before calling it done.

## Telegram bot in a group with topics

To restrict a bot to respond only when mentioned in a group with topics:

```
hermes config set platforms.telegram.extra.allowed_chats '["-100XXXXXXXX","-100XXXXXXXX:11","-100XXXXXXXX:13"]'
hermes config set platforms.telegram.extra.group_allowed_chats '["-100XXXXXXXX","-100XXXXXXXX:11","-100XXXXXXXX:13"]'
hermes config set platforms.telegram.extra.require_mention true
hermes config set platforms.telegram.extra.observe_unmentioned_group_messages true
```

The list must include both the bare chat_id and each `chat_id:thread_id` pair.
After editing, `hermes gateway restart` (not reload) is required. Verify by
sending a message without `@` (must be observed, not answered) and with `@`
(must be answered).

## Long-polling Telegram bot: getting an id, and proving it works

A standalone long-polling bot (`getUpdates` loop, no webhook) has two failure
modes that both look like "the bot is dead" while the service is `active`:

- **A long-polling consumer makes `getUpdates` return an empty queue.** The bot
  acks every update with `offset = update_id + 1`, so a second reader — even one
  started after the fact — sees nothing. To harvest an id or a message that the
  bot already consumed: stop the unit, then read `getUpdates` with
  `offset=-20`; the offsets are already advanced past the message, so it is
  gone. The reliable route is to make the bot report it: add a `/myid` command
  that answers `chat_id` in a `<code>` block, restart the unit, and have the
  user send it. Ask for the id in chat only after the bot has been taught to
  print it.
- **`systemd` swallows the bot's own `print`, and stdout proves nothing.**
  `journalctl` showing only start/stop lines means the loop never logged a
  received update, not that the request failed. Diagnose by running the same
  script outside systemd with stdout redirected to a file — that shows whether
  the loop receives the update at all, which is the fact you need before
  touching handler code.

Keep `systemctl is-active` and `getMe` in the same probe: together they
distinguish "process alive" from "token alive", and the pair is the whole
first diagnostic for this class of bot.

**A bot running under webhook answers `getUpdates` with `409 Conflict` — you
cannot harvest ids from it.** The webhook owns the update stream, so there is
no queue to read and no personal `chat_id` to recover after the fact. When the
user asks for a report "in Telegram" and their personal id is unknown, deliver
to the group/topic they demonstrably read and say so; capture a personal id by
having them message the bot (a `/myid` command that echoes `chat_id`) or from
the gateway's inbound message records, then offer to route there next time.
A MAX user_id is **not** the Telegram user_id — never assume the two ids match
across platforms.

## Live-status / control panel (agents + projects + n8n in one page)

A status dashboard that reports the real health of services, pages and workflows on every load is the highest-value small panel to build — it turns "is it down?" into a page you refresh. Two parts: a JSON status endpoint and a public page that polls it.

- **Backend = one `_control_api` method on an app that already runs** (the same server that proxies other routes). Probe liveness with `systemctl is-active <svc>` via `subprocess` (timeout 5s, return False on any exception), probe pages with `curl -s -o /dev/null -w %{http_code} --max-time 6`, and pull automation-workflow state from the platform's REST API. Never embed secret values — read the API key from the secrets dir into a local var only.
- **The page is public; the API is gated.** Serve `control.html` with no auth, and gate `/control/api` with the same `master_ok()` used by the rest of the app. A status page that 401s on load teaches nothing; a page that renders a password form and calls the API with an `Authorization` header keeps the secret out of the HTML entirely — the password lives only in tab memory.
- **Do NOT send the master password in a cookie for this.** The existing session cookie is minted with `Path=/manicure`; the browser will not send it to `/control/api`, so a `fetch('/control/api', {credentials:'include'})` returns 401 even while the page that set it is open. Either mint a separate `Path=/` cookie after a Basic check, or — simpler and with no cookie at all — have the page send `Authorization: Basic <b64>` from a form. Pick one and verify with the browser, not curl.
- **Read the password from the same helper the server uses.** A secret file that holds the password on line 0 and an API secret on line 1 must be read with the server's own `_read_line(name, 0)`; `$(cat file)` in a shell grabs the whole file (newline and all) and produces a value that passes curl but fails a real form login. When a probe and a browser disagree on the same credential, suspect the reader before the auth code.
- **Verify by driving the real page in headless Chromium and counting rendered cards** (`document.querySelectorAll('.card').length` > 0), not by curling the endpoint. Curl proves the API; only the browser proves the page's fetch actually authenticated and rendered. Fill the password field with the page's own form, then screenshot full-page.
- **`http_credentials` / URL-embedded creds in Playwright apply only to top-level navigation, never to a page's own `fetch`** — a fetch to the same origin returns 401. Drive the page's form instead. Over CDP the equivalent fix is `cdp('Network.setExtraHTTPHeaders', headers={'Authorization': 'Basic …'})` before navigating; URL-embedded creds break the page's own fetch with "Request cannot be constructed from a URL that includes credentials", which reads like a server fault and is not one.

### When the user supplies a reference screenshot

The image is the specification, and the **metaphor is the part you must not
substitute**. A status table, a card grid, and an isometric office of the same
services all answer "show me the agents and projects" — only the one matching
the screenshot satisfies the request. Building the right data in the wrong form
is a failed build, not a style preference; state the extracted vocabulary back
in one line before coding ("this is an office with people at desks, not a
status table") so a mismatch is caught before it costs a rebuild.

Re-skin an existing verified panel rather than writing a new app — keep the
status endpoint, auth gate, nginx route and systemd unit; replace only the
rendering layer. Use **deterministic isometric SVG, not CSS `preserve-3d`**, and
place per-item labels in a fixed legend strip instead of under each shape.

**When the user names the panel to copy ("make it look like panel X"), that
panel's CSS is the specification — copy its token block verbatim** (token
names, accent hex, body max-width, card radius and section padding) and change
only the class names, instead of approximating the vibe with a new palette.
**Copy the reference's component rules too, not only its token block.** A panel
rebuilt with the right palette but no rules for the new components renders at
browser defaults — a time grid arrives as a column of unstyled default buttons
and the user calls it ugly again. Diff the reference stylesheet for every class
the reference's HTML uses (`.grid`, `.slot`, …) and port each one, then scale.
**Matching a named reference means matching its interaction model too, not only
its palette.** Read the reference panel's sections and controls (what the master
actually does on it) and rebuild those; a list-shaped rebuild of a grid-shaped
panel is the same class of miss as a wrong accent colour, and the user will say
"ugly" either way. Copy the CSS first to stop the bleeding, then read the
reference's *flow* and rebuild that before declaring it done.

**Size a time-grid picker for a phone.** Minimum column ~150px, button height
~72px, font ~20px — the operator taps it between jobs, not at a desk. When the
user calls the buttons too small, scale the grid tokens; do not redesign the page.
Two failure modes to avoid: inventing a fresh palette when a reference exists
(the user reads it as "ugly" and asks for a redo), and declaring the restyle
live without proving the served bytes changed — grep the *served* CSS through
the proxy for the signature accent hex, because a browser cache otherwise keeps
rendering the old file and the user sees no difference at all.
Finally, **look at what you rendered**: drive the real page in headless
Chromium, fill the password form, screenshot, then run a *critical* vision check
("any overlaps? are labels readable?"), not a confirming one. Two or three
render-inspect-adjust rounds is normal for a first visual scene. **Use a plain
viewport capture, not full-page, on a long or dynamic page** — full-page
rendering has to composite the entire scroll height and times out (60s) on a
heavy SPA, while the same page captures instantly at viewport size. A timed-out
capture is a tool timeout, not a page bug; retry smaller before debugging the
app.
Full recipe, projection math and verification loop: `references/visual-dashboard-reference-matching.md`.

**Furniture must share the floor's projection.** Flat diamonds or rectangles
placed over a diamond-tiled floor read as stickers floating above it — a collage,
not a scene. An isometric desk is a cube: a diamond top face plus two side faces
clipped from the same 2:1 projection, so its edges line up with the tile grid.
When a user says the scene "looks broken / like a collage / things don't sit on
the floor", the geometry of the props is the first suspect, not the layout.

**CSS `preserve-3d` yields non-deterministic geometry** — rooms drift, walls face
the wrong way, and hover transforms fight the scene transform. For a scene that
must survive review, compute the projection yourself (see the reference file) and
render as one deterministic markup string.

## Removing a panel the user has rejected

A panel the user decides against is a full teardown, not a disabled route. A
half-removed panel leaves a 502 in front of visitors and dead handlers in the app.

1. **Back up before touching prod, and make the backup the removal's undo.** Copy the app tree, its systemd units and the nginx vhost into `/root/_archive/<project>-<timestamp>/` — not the live project directory, which this procedure deletes — and name the archive path in the report so it is findable without a search. An `rm -rf` of the only copy is irreversible, and users routinely ask for a rejected thing back.
2. **Remove in dependency order**: the app's route branch and its handler methods, then the static file, then the nginx `location` blocks, then the KB pages (move them into the KB repo's `_archive/` so the project note survives without polluting the live index). Grep the app for the route name after the code edit — a leftover reference in a comment is enough to trip the next leak-grep. Decommission the services in the same pass: stop *and* disable each unit, delete the unit files, `daemon-reload`, and remove the app's entries from `/root/.secrets/` — a dead bot's token still opens that bot.

   **Archive, do not destroy.** `rm -rf` of the project tree is irreversible and the user routinely asks for the thing back. Copy the app, its systemd units and the nginx vhost to `/root/_archive/<project>-<timestamp>/` first, then remove the live paths. State both paths in the report so the archive is discoverable without a search.
3. **Every path form needs an explicit answer, including the ones that used to redirect.** Once `location ^~ /panel/` is gone, requests to `/panel/` and `/panel/api` fall through to the catch-all `location /`, which proxies to whatever else runs on the host (the agent gateway, another app) — and that service answers **502** for paths it does not know, not 404. A removal is only clean when each form returns 404:
   ```nginx
   location = /panel      { return 404; }
   location = /panel/     { return 404; }
   location = /panel/api  { return 404; }
   ```
   Write all forms before reloading, then curl each one. `nginx -t` passing says nothing about which `location` a request lands in.
4. **Verify the neighbours, not just the removal.** Curl every remaining route on the shared vhost — each static page, the production panel, and one authenticated API call — and report their real status codes. Removing a block from a shared vhost is the same risk as adding one.

**Cloud-hosted state usually outlives the keys the agent holds — say so plainly.** A Supabase project cannot be dropped with the `anon` key the app used; only the dashboard can delete it. Report the leftover cloud project by name, hand the user the dashboard action, and offer to leave it in place as the archive of record.

## Reporting shape

Lead with the URL and the login. Then a table of checks with real values — status codes, row states, message text — not "works". Name every bug found and its mechanism, including the ones you introduced and fixed in the same session; a silent mid-session reversal the user still remembers as outstanding will misdirect their next decision. Close with what the panel does NOT do yet, and offer one concrete next step.

## Process lifecycle on a shared host

Restarting one of several apps on the same box is where sibling services get
clobbered, and where stale code keeps serving.

- **Find the listener before killing anything**: `ss -tlnp | grep <port>` names
  the exact PID. `pgrep -af <pattern>` can list more than the listener (a shell
  wrapper plus the interpreter).
- **Kill by exact PID from execute_code** (`os.kill(pid, signal.SIGKILL)`), never
  `pkill -f <pattern>` from the terminal tool — the pattern matches the tool's
  own shell wrapper, and the session gets SIGTERMed instead of the target.
- **A restart that cannot bind leaves the old process serving.** The new
  background job starts and dies silently; curl keeps hitting stale code. After
  every restart, confirm the serving PID is the one you just started, and
  probe one endpoint that only the new code has.
- **A systemd unit stuck in `activating (auto-restart)` with a working curl
  means the port is held by a manual test process.** The unit's own start fails
  with exit 1 every time; the curl success proves the *manual* process is
  alive, not the service. Kill the manual process by exact PID, let
  `is-active` settle on `active`, and only then probe.
- **Read keys from the secrets file programmatically every run; never retype one
  from an earlier message.** A key belonging to another project, or a truncated
  JWT, answers 401/403 and reads like an auth bug — the auth code is fine.

## Editing a live client form (selects, filters, derived fields)

A form the user works in every day is production UI, and the edits look trivial while
carrying the most regression risk of any change in this skill. The pattern that fails:
restructure the form, confirm the data still loads, declare it done — and a handler that
used to fire no longer does.

- **A modal's dropdowns must load their own options, not inherit another page's state.** The bug shape: `loadAccounts()` fills the shared `accounts` array and calls `updateAccountSelects()`, while `loadSchedule()` only fetches schedule rows. Open the Schedule page directly (never visiting Accounts first) and the account `<select>` is empty — the user reports "невозможно выбрать аккаунт" and the code looks correct because it *is* correct on the other path. Every page that renders a modal with a foreign-entity dropdown must fetch that entity itself (one `Promise.all` of the page's own data plus each dependency), not rely on a sibling page having run. The tell: the dropdown works after clicking through the app in order, and is empty on a fresh load straight into the deep page — always test the deep page as the entry point.
  - **Render an explicit empty-state option, not a blank select.** When the dependency list really is empty, `<select>` with no options renders as a silent blank box. Insert a disabled-looking option naming the fix (`— нет аккаунтов, добавьте на странице «Аккаунты» —`) so the user knows it is data, not a broken control.
  - **Validate the select's value on submit and say which field is missing.** `parseInt('')` is `NaN`, which posts as `null`/garbage and fails server-side with an unhelpful message. Check each select for a non-empty value first and toast the field name; wrap the create call in try/catch so a rejection surfaces instead of silently closing the modal.
- **After reordering or restructuring form fields, re-verify every dependent handler live,
  not just the data load.** Selecting an entity drives derived state (auto-filled
  recipient, filtered child list, enabled submit); when the field that set it moves or its
  `onchange` is dropped, the data still arrives from the database and the page looks
  correct — but the derived field silently stays empty or stale. Drive the full user
  scenario in the browser (open section → pick entity → read the derived field and the
  filtered list) before calling the edit finished.
- **State derived from a selection is recomputed on EVERY change of that selection, never
  only when empty.** A guard like `if (!selected)` leaves the previous item's value in
  place after the user switches entities: the nested filter then shows the previous
  entity's children, or an empty list that reads as "nothing matches". Assign from the
  selected entity's own data unconditionally.
  - **The same trap fires on a reworked flow where a value used to be filled
  automatically.** Restructuring a form (making one field the first control, moving a
  block) is exactly when the handler that auto-filled a related field stops firing — the
  data still loads from the DB so the page looks correct, and the derived field silently
  stays empty or keeps the previous entity's value. After ANY form restructure, re-drive
  the scenario where selecting the entity must fill the dependent field, and where
  switching from entity A to entity B must overwrite A's value — the switch case is the
  one the `if (!selected)` guard breaks.
- **A progressively revealed form reveals each group from the control that gates it.**
  When the flow is "pick X → then Y appears", the group for Y starts `hidden`, the
  selector for X makes Y's group visible, and opening the section re-runs the whole
  reset (every group hidden, every placeholder back to its prompt text, every derived
  value cleared). Two groups can stay in sync when the same selector drives them from
  two different sections — drive the reveal from one `selectRecipient`-style handler
  that checks which section is visible, not from two independent copies. A parent
  selector that triggers a data load must be `async`; calling an un-awaited loader
  leaves the child group empty and looks like a broken query.
- **Filter by multiple ids with `in.(...)`, not repeated `eq.`** (Supabase REST). Concatenated
  `id=eq.a,id=eq.b` silently drops every condition after the first and returns an empty
  list, so the UI renders a generic "load error" with no clue that the query was malformed.
  `eq.` is for exactly one value; for a set always build `id=in.(a,b)`.
- **When the user says "nothing changed" but the server serves the new code, hunt the
  behavioural regression — the cache check is the cheap first step, not the answer.**
  Confirm the served bytes actually changed (grep the served response for the new
  signature text, check `Cache-Control`/`no-store`); when they have, stop suspecting the
  cache and re-drive the exact scenario, looking for a handler that stopped firing.
  "Data comes from the DB, so it works" is precisely the assumption that hides this bug.
- **`no-store` on the asset is not a fix for a stale browser; version the asset URL.**
  A browser can keep serving its own cached copy of `app.js` across a navigation no
  matter what header the server now sends, so the user reports the SAME missing feature
  after every deploy while `curl` shows correct code (the tell: `md5sum` of the source
  and the served file agree, and the feature still "doesn't work" only in their browser).
  The durable fix is to make the stale copy unreachable: serve `index.html` through a
  handler that appends a content hash to the script tag —
  `html.replace('src="app.js"', f'src="app.js?v={hashlib.md5(open(js,"rb").read()).hexdigest()[:10]}"')`
  — so the URL changes whenever the file does. Two traps: the hash must come from the
  file's **bytes**, not its mtime; and the handler must be registered on the path nginx
  **actually forwards**. An exact-match block `location = /prefix/ { proxy_pass …/index.html; }`
  reaches `/index.html`, NOT `/`, so an `@app.get("/")`-only handler never runs and the
  served page still carries the bare `app.js` — decorate both (`@app.get("/")` above
  `@app.get("/index.html")`). Verify by curling the page through the proxy and grepping
  the script tag for `?v=`, then confirm the version changes after an edit.
- **Prefer a button grid over a `<select>` for a small fixed set of entities an operator
  picks between jobs** (a handful of carcasses, boxes, masters): `#number` plus a small
  caption line, `.selected` cleared across the group via `el.closest(...)` rather than a
  page-wide query, and the list re-fetched after a write since the set shrinks.
- **One label rule for a value that appears in several surfaces.** A caption built as
  "gender, type" in one place and "type, gender" in another, or showing both fields where
  only one carries meaning, is a defect the user reads immediately — the app table, the
  button grid and the rendered image sent to chat must all derive the caption from the
  same expression (e.g. `gender || type`, so cattle shows only the gender).
- **An operator who creates records fast creates duplicates — filter by natural key at
  create time and surface the collision.** "Carcass #100" or "slot for master X" is a
  natural key, not a unique column, so nothing stops a second record a few minutes later;
  the UI then shows two identical rows and the user reads it as the app's bug. Check the
  natural key before insert and refuse with the existing record's id, and when cleaning up
  a duplicate found by the user, delete the newest copy and keep the original (the oldest
  one carries the history) — and grep the whole tree for the deleted function name before
  renaming a loader: `loadCarcasses()` calls left behind after a rewrite throw
  `ReferenceError` on every path that still references them.
- **A feature that hides a category from one view but the category is still creatable
  reads as "new records don't appear".** When a filter is added to a list (show only the
  primary category in issue/return lists), every creation path still accepts the other
  categories, so a newly created record of the hidden category exists in the database
  while the list shows nothing — the user's report is "the thing I just added isn't
  there". Either make the list show all categories the creation path accepts, or state
  the scope of the filter plainly; and before adding such a filter, check whether it
  contradicts an earlier request of the user's and say so out loud instead of guessing
  which request wins.

## references

- `references/shared-status-values.md` — the one-writer/many-readers audit for a status field, and why a mismatch fails silently.
- `references/oauth-callback-proxy.md` — wiring an OAuth callback under a path prefix: the nginx `proxy_pass` prefix trap, PKCE verifier persistence, the `invalid_client` probe ladder, credential transcription rules, and the per-account connection flag.
- `references/file-upload-panels.md` — real file uploads through a proxied panel: the three layers (nginx `client_max_body_size`, chunked app write, XHR progress), provider-side limits, and why a fake payload proves nothing.
- `references/scheduled-worker-queue.md` — the DB-as-queue publishing worker: atomic claim, retry/backoff/failed, per-network daily caps, one shared publish module for panel and worker, and the past-dated test that proves the loop.
- `references/visual-dashboard-reference-matching.md` — turning a reference screenshot into the artifact the user pictured, and the browser verification loop.
- `references/messenger-number-lookup.md` — verifying which phone numbers are registered on a messenger: gateway tiers, account risk, the demand-first ladder.
- `references/pwa-offline.md` — making a served SPA installable and offline-capable: manifest/prefix agreement, SW cache policy, offline data layer, honest offline verification.
- `references/max-media-attachments.md` — sending a photo, file, or a server-rendered table/report image through the MAX bot: the three-call upload chain, the `data`-field and one-shot-URL traps, per-product bot tokens, the HTML→PNG render step, and the "submit = notify the owner" form pattern.
- `references/social-publishing-api-viability.md` — which platforms still allow programmatic posting (and which closed their write APIs), VK split by target (video closed / community wall open, the community-token scope mask, the app-classification ladder read from `error_description`), why reposting fails the reach goal, the fallback ladder when the API is closed (aggregator account model, the false-positive onboarding badge, the silent Business/Creator prerequisite), and the one-publish-router shape for mixing a direct API with an aggregator.
- `references/ai-video-generation-apis.md` — Kling AI and Higgsfield AI for AI video generation: domains, auth, model names, pricing, async patterns, and the rule that no major provider offers a free API tier.
- `references/api-credential-onboarding.md` — receiving and verifying external API keys/tokens: storage pattern, verification steps, per-provider quirks, and reporting what the key can and cannot do.
- `scripts/spa-static-server.py` — a minimal `dist/` static server with SPA fallback, for serving a built Vite/React app under a path prefix without `vite preview`'s Host check.

## Delegating a deliverable to your coding sub-agent

When the user built a sub-agent to produce a class of artifact (a web page, a code
module), and the current request is an instance of that class, the sub-agent
produces it — you do not hand-write it "to save time". Writing it yourself
substitutes your output for the agent's, and the user reads that as ignoring the
architecture they built. This is the single correction this user has voiced most
sharply and more than once.

- **A stub sub-agent is a blocker to fix in-session, not a reason to self-serve.**
  If the agent only answers placeholders (`# TODO: интеграция с API`, "заглушка"),
  make it real before producing the deliverable: write the missing model-call
  engine as an importable module, reuse the provider list and token headroom from
  a sibling agent verified in production, validate the engine in isolation, then
  wire and restart.
- **A sub-agent that emits a broken artifact frame is still partial delegation.**
  If the agent returns working logic (sprite function, scene builder) inside a
  malformed HTML skeleton, take its working functions and integrate them into a
  verified frame rather than rewriting the logic yourself — then state plainly
  which part was hand-integrated.
- **If a sub-agent cannot yet ship the artifact unaided, say so in the report**
  instead of silently doing its job. The user's next decision depends on knowing
  whether the agent is real yet.
- **A named, persistent agent is an executable with a task-file contract — not
  a skill, and not a manual one-off run.** When the user says "make an agent,
  not a skill for yourself", build a standalone script with a fixed shape:
  input as `tasks/task-N.md` (`key: value` lines), artifact plus a `.output`
  report in `output/`, launched on demand and launched *by you* when the user
  names it by its trigger phrase. Recording the procedure in your own skill
  memory is precisely what they declined. This user has voiced the correction
  more than once, in almost those words.
  - The agent owns its engine as a vendored copy in a permanent directory
    (`/root/<agent>/parser/`), never a scratch clone — scratch is pruned on a
    timer and the production service would vanish with it.
  - Long jobs run backgrounded with `notify=true`; a 5-8 minute parse must not
    occupy the turn. Report the live endpoint, not a narration of the wait.
  - **A long-job waiter must also accept the engine's local artifact as proof of
    completion.** An engine that shuts its API down the moment it finishes
    leaves a poller looping against a dead endpoint until timeout, even though
    the result is already on disk. Check for the output file inside the same
    poll loop and treat it as the finished state.

### Designing a role team for a web build

When the user asks "which agents should this work go to", or when a build's
context is visibly filling with mechanics, design the roles before writing code
and record the design in the project KB (`/root/kb/agents/<project>/`) — the
deliverable of that request is the design, not the build.

**The trigger is a repeated execution-with-feedback loop:** build → read error →
fix → build; open browser → read DOM → adjust → reload; curl → auth → probe →
interpret. Generation and observation in one context is what burns it.
Architecture, acceptance and decisions stay with you; execution moves out.

**The role shape for web delivery** (order matters — each hands off a concrete
artifact, and the handoff is the contract):

| Role | Produces | Hands off as |
|---|---|---|
| designer | prototype HTML + design tokens + component states | `prototype_path` + `tokens_added` — the tokens ARE the contract |
| frontend-dev | React components + green `npm run build` | `dist_bundle` path |
| backend-dev | service file + live test | the real test output |
| qa-verifier | PASS/FAIL verdict | structured verdict with evidence |

Designer precedes frontend-dev so visual iteration happens outside the code
cycle (the "make the buttons bigger, look at panel X" rounds are the expensive
part); backend runs parallel because it is independent of the visual; and
**qa-verifier is never the agent that built the thing** — self-verification is
not verification. Prioritize roles by context relief, not by build order: the
role that removes the most expensive loop (usually live browser verification)
goes first.

**A `delegate_task` task is self-contained or it fails.** The child sees only the
`context` you pass — it cannot ask a clarifying question, read your memory, or
delegate further. Every task carries: absolute paths; credential *file paths*
(never values); the concrete steps; the PASS criterion; and the output schema
the verdict must match.

**Accept on evidence, never on the self-report.** A child claiming "works" or
"uploaded" may be wrong. Require a verifiable handle — real text read out of the
DOM, real build output, a real API response, an absolute path — and confirm
external side effects yourself before telling the user they happened. Templated
evidence ("всё работает", "done") is not a verdict; ask again.

**On FAIL, return it — do not absorb it.** Re-doing a failed child's task
yourself defeats the delegation and refills the context you were protecting.
Send the concrete failure back to the same role, or re-delegate the fix to the
role that owns it. Production writes (nginx, systemd, live bots, live databases)
stay with you under approval; children may install packages and make additive
reversible changes, never destructive ones.

### Running the chain: what a completed pass looks like

A designer → frontend-dev → qa-verifier pass on a live tree costs about three
minutes of wall time and leaves only verdicts in your context:

1. **designer (audit).** Context carries the requirement list, the project's
   current token block (read it yourself first from `src/index.css`), the file
   paths, and the criterion "read-only — change nothing". A design-audit
   verdict needs per finding: requirement, status (PASS/PARTIAL/FAIL),
   evidence as `file:line`, and a concrete recommendation, plus an overall
   verdict (COMPLIANT / MINOR_ISSUES / MAJOR_ISSUES) and a compliance
   percentage.
2. **Accept the designer by spot-checking three citations** with `read_file`
   / `search_files`. Accurate `file:line` quotes prove the read was real;
   templated findings ("styles look inconsistent") mean re-ask. Hand the
   findings — requirement, evidence, recommendation — verbatim into
   frontend-dev's context as the task spec.
3. **frontend-dev (one batch, not one finding per dispatch).** Context carries
   every finding as a single task, explicit boundaries ("styles only — do not
   touch structure or logic; leave card radii, gallery, chat bubbles alone"),
   the exact build command including the toolchain PATH export, and the
   required output: `build_ok`, real `build_output`, `changes_applied` per
   file, `dist_bundle` path.
4. **Accept frontend-dev by probing its claims yourself**: grep for the old
   pattern (must be gone), count the new token per file, read the one changed
   line, and confirm the claimed `dist_bundle` path exists on disk. "Build
   green" without a bundle on disk is not a verdict.
5. **Deploy yourself between frontend-dev and qa.** The static-server restart
   and the route curls are production writes and stay with you; only then does
   qa-verifier receive the live URLs. Never let one child deploy what another
   child built.
6. **qa-verifier (verdict, not proof-by-screenshot).** Context carries the
   URLs, credentials, DOM markers, and the browser pitfalls; state that a
   failed screenshot capture is non-fatal because the DOM markers are the
   evidence. A PASS on a dozen DOM markers with a dead capture is a PASS —
   do not re-screenshot to re-confirm it, and do not read your own hung CDP
   daemon as a page bug.

**`output_schema` must be valid JSON Schema or the dispatch is rejected before
the child starts.** `items: "string"` fails validation — every element schema
is an object (`items: {"type": "string"}`). The error names the offending
property; fix the schema and re-dispatch, nothing is lost.

**A verdict whose evidence is DOM markers is complete without a screenshot.**
Once a child returns PASS with per-marker evidence, taking your own capture to
"look again" re-enters the exact expensive loop the delegation removed — and
the CDP screenshot daemon hangs (60s timeout) on a heavy SPA, so the retry
costs context twice. Accept the DOM verdict; if you need an image for the user,
ask for it *after* accepting, and treat a capture timeout as a tool timeout,
never as a page bug.

For creating, searching, and installing Hermes skills as GitHub taps:

### Structure and install
```
repo/
├── <category>/<skill-name>/SKILL.md
├── README.md
└── .gitignore    # exclude .env, *.key, *.pem
```

```bash
hermes skills tap add owner/repo
hermes skills install owner/repo/<category>/<skill-name> --yes
```

### Pitfalls

- **A catch-all `GET /{path:path}` route placed before API routes silently swallows them.** FastAPI matches routes in registration order, so a SPA fallback that returns `index.html` for every unmatched GET will intercept `/api/...` paths and return HTML with `Content-Type: text/html` instead of JSON. POST routes still work (the catch-all is GET-only), which makes this especially confusing. Fix: add an early `raise HTTPException(status_code=404)` for paths starting with `api/` inside the catch-all, and register API routes before it. Verify with `curl -s -H "Accept: application/json" http://127.0.0.1:8765/api/endpoint | head -c 100` — if it starts with `<!DOCTYPE`, the catch-all is winning.

- **systemd does not clear `__pycache__`.** After editing `main.py`, running `systemctl restart` is not enough — Python will keep loading the stale `.pyc` from `__pycache__` if the mtime granularity causes a cache hit. Always `rm -rf __pycache__` before restarting a systemd Python service. Symptom: new routes appear in `/openapi.json` of a fresh import but the live process returns 404 or wrong content for them.
- `hermes skills install` fetches from GitHub API (60/hr unauthenticated). SSH keys do NOT help — set `GITHUB_TOKEN` in `~/.hermes/.env` to raise to 5,000/hr.
- Always pass `--yes` in scripted/automated contexts.
- After `tap add`, verify with `hermes skills inspect` rather than `search` — search returns community results first and will not surface your tap.
- The install identifier carries the category path (`owner/repo/<category>/<skill-name>`), and the category in the path need not match where the files physically live — the hub indexes by repo structure, so verify with `inspect` on the full path before assuming a file is missing.
- Community registries (clawhub, skills.sh) have ~100k entries with heavy noise. Filter by `Source: official` for verified skills.
- No secrets in SKILL.md — use paths only.