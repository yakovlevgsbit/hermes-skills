# OAuth Callback Proxy Under a Path Prefix

When an OAuth provider (Google, Facebook, etc.) redirects back to your app, the callback URL must match exactly what's registered in the provider's console. If your app lives under a path prefix like `/smm/`, the callback URI is `https://domain/smm/oauth/callback/<provider>`.

## The Problem

nginx `proxy_pass` with a trailing slash strips the location prefix. So:

```nginx
location ^~ /smm/oauth/ {
    proxy_pass http://127.0.0.1:8765/oauth/;
}
```

This forwards `/smm/oauth/youtube/start` → `/oauth/youtube/start` on the backend. But if the backend routes are under `/api/oauth/...`, the request hits the SPA catch-all and returns HTML instead of JSON.

## The Fix

Point `proxy_pass` at the full backend path:

```nginx
location ^~ /smm/oauth/ {
    proxy_pass http://127.0.0.1:8765/api/oauth/;
}
```

Now `/smm/oauth/youtube/start` → `/api/oauth/youtube/start` on the backend, which matches the FastAPI route.

## Multiple Provider Callback Blocks

Each provider gets its own `location` block for precise matching and correct `proxy_pass`:

```nginx
# ── YouTube OAuth callback ──
location ^~ /smm/oauth/callback/youtube/ {
    proxy_pass http://127.0.0.1:8765/api/oauth/callback/youtube/;
    proxy_http_version 1.1;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 60s;
}

# ── VK OAuth callback ──
location ^~ /smm/oauth/callback/vk/ {
    proxy_pass http://127.0.0.1:8765/api/oauth/callback/vk/;
    proxy_http_version 1.1;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 60s;
}
```

## FastAPI callback endpoints

```python
# Google/YouTube (uses google-auth-oauthlib)
@app.get("/api/oauth/youtube/callback")
def youtube_oauth_callback(request: Request, code: str, state: str):
    require_auth(request)
    account_id = int(state)
    flow = Flow.from_client_config(...)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    # Store tokens...

# VK — DO NOT use oauth.vk.com for a new app.
# VK migrated to VK ID (id.vk.ru); the old authorization-code flow is gone and
# VK ID issues login-only tokens, so a video/wall write is unreachable anyway.
# See social-publishing-api-viability.md before wiring any VK write.
# A VK ID callback (if you need login only) is PKCE + POST id.vk.ru/oauth2/auth
# with grant_type=authorization_code, code, code_verifier, device_id, client_id.
```

## Frontend polling pattern

```javascript
async function connectYouTube(accountId) {
    const result = await api(`/oauth/youtube/start?account_id=${accountId}`);
    window.open(result.auth_url, '_blank', 'width=600,height=700');
    
    const interval = setInterval(async () => {
        try {
            const status = await api(`/accounts/${accountId}/youtube/status`);
            if (status.connected) {
                clearInterval(interval);
                showToast('YouTube подключён!', 'success');
                loadAccounts();
            }
        } catch(e) {}
    }, 2000);
}
```

## Google Cloud Console onboarding (Google / YouTube OAuth)

- **`invalid_client` has TWO causes — probe which one before touching the console.** It means either (a) the consent screen is unconfigured, or (b) the client id/secret you hold is simply wrong. Never assume (a): a mistyped or mis-transcribed id produces the identical error, and hours go into re-configuring a consent screen that was already fine.

  **The probe ladder — run it before editing anything.** Each step is one HTTP request and each answer is unambiguous:

  ```python
  # STEP 1 — is the client_id real? Land on signin/consent = VALID. Land on
  # signin/oauth/error = the id itself is wrong. No secret needed for this test.
  params = {"client_id": CID, "redirect_uri": REDIRECT, "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.upload", "state": "t"}
  url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
  # follow it (urlopen) and read resp.url + body for "invalid_client"

  # STEP 2 — is the secret real? Post a FAKE code with the real id+secret.
  # "invalid_client" = secret wrong. "invalid_grant" = id AND secret are both
  # correct and the fake code was rejected, which is the success case here.
  data = urllib.parse.urlencode({"code": "FAKE", "client_id": CID,
      "client_secret": SECRET, "redirect_uri": REDIRECT,
      "grant_type": "authorization_code"}).encode()
  # POST https://oauth2.googleapis.com/token  -> read the JSON `error` field
  ```

  Read the verdict off the error CODE, not the HTTP status: both steps answer 401, and only the code separates "wrong credential" from "expected rejection".

  **A Google client_id always begins with the project number**, so a prefix that does not match the project number in the console is proof of a bad transcription — check that before probing. Once both steps pass, THEN the remaining `invalid_client`-adjacent causes are the consent screen (Branding filled, Audience = External, **the exact Google account you will sign in with added to Test users**, app published; allow 5–10 minutes to propagate).

- **Never transcribe a credential by reading a screenshot — the copy button or Download JSON only.** Values read off a screenshot arrive with silent character errors (OCR substitutes and inserts digits), and the resulting `invalid_client` looks exactly like a misconfigured app. When a value has to come from a console page you cannot reach, ask the user to use the page's own copy button and paste it — a client_id is NOT a secret and is safe to paste in chat (it is public, it appears in the authorization URL). The client_secret is the one that must not travel through chat: have the user write it into the vault file over SSH, or download the JSON and hand over the file.
- **A password the user pastes into chat is compromised the moment it arrives — say so and tell them to rotate it.** It is now in the session log, the model context and any backup. Do not type it into anything (the browser tools refuse passwords from the agent by design — use the vault), do not store it, and close the loop by naming the concrete action: change the password, enable 2FA. Then get the value you actually need the safe way: the copy button for a public id, a vault save or an SSH-written file for a secret. Trying to log into the provider's console *as the user* to read the value is not a workaround — consumer providers actively block automated sign-in ("This browser or app may not be secure"), so it burns turns and reaches nothing.
- **`Authorized domain` in Branding wants the ROOT domain** (`example.com`), never a subdomain — a subdomain answers `Invalid domain: must be a top private domain`. The subdomain belongs in the client's **Authorized JavaScript origins** / **Authorized redirect URIs** instead.
- **The redirect URI must match the console entry exactly**, scheme and path included. For an app under a path prefix it is `https://domain/prefix/oauth/callback/<provider>`.
- **Unverified apps cap sign-ins** (a low per-app user limit) until the consent screen passes review — fine for testing with your own account, a blocker before handing the panel to clients.

## Token exchange: the two failures that survive a correct client_id

Getting `invalid_client` cleared is only half the job. Two more failures live in
the `/start` → `/callback` handoff, and each one has a distinctive provider error:

- **`(invalid_grant) Missing code verifier` — PKCE verifier was not persisted.**
  `google-auth-oauthlib` (and any PKCE provider) generates a `code_verifier` when
  you call `flow.authorization_url(...)`, sends its hash to the provider, and must
  present the ORIGINAL at token exchange. The callback builds a **brand-new**
  `Flow` object, which has no verifier — so the exchange is rejected even though
  `code` and `state` are perfect. Persist it at `/start` and restore it at
  `/callback`:
  ```python
  # /start — after flow.authorization_url(...)
  conn.execute("INSERT OR REPLACE INTO oauth_pkce (state, code_verifier, account_id) VALUES (?,?,?)",
               (state, flow.code_verifier, account_id))

  # /callback — before flow.fetch_token(code=code)
  flow.code_verifier = conn.execute(
      "SELECT code_verifier FROM oauth_pkce WHERE state = ?", (state,)).fetchone()["code_verifier"]
  ```
  Delete the row after a successful exchange. A `state`-keyed table is the right
  shape because `state` is the only value that survives the round trip; do not try
  to keep the verifier in a module-level global — the callback can land on a
  different worker or after a restart.

- **The callback path nginx produces is not the path the app routes.** A block
  `location ^~ /smm/oauth/ { proxy_pass http://127.0.0.1:8765/api/oauth/; }`
  turns the provider's `/smm/oauth/callback/youtube` into
  `/api/oauth/callback/youtube`, while a route written as
  `/api/oauth/youtube/callback` never matches — the request falls into the SPA
  catch-all and answers **200 with index.html**, which looks like success in a
  browser and writes no token. Diagnose by curling the provider's exact path with
  a fake code: a JSON error means the handler ran, HTML means it did not.
  Fix on whichever side is cheaper to change — an alias decorator is a one-line
  app change with no prod nginx edit and no reload:
  ```python
  @app.get("/api/oauth/callback/youtube")   # the path nginx actually forwards
  @app.get("/api/oauth/youtube/callback")   # the pretty one
  def youtube_oauth_callback(...): ...
  ```
  Curl BOTH forms after the change; only the one the provider hits matters, but a
  stray broken alias confuses the next reader.

**Surface the provider's own error, never a bare 500.** `flow.fetch_token(...)`
wrapped in `try/except` and re-raised as `HTTPException(400, f"Token exchange
failed: {type(e).__name__}: {e}")` turns an opaque failure into the exact string
above. Without it every OAuth problem looks identical in the log and each round
trip costs a full browser retry to learn nothing.

**Redirect the browser back to the panel, don't render JSON at the user.** The
callback runs in the user's tab, so returning `JSONResponse` leaves them staring
at raw JSON on what should be a seamless flow. `RedirectResponse(url="/prefix/?provider=connected&account_id=…", status_code=302)`
lands them back in the UI. Because that redirect is a cross-site navigation back
from the provider, a `SameSite=Strict` session cookie is **not** sent and the
panel renders logged-out — use `SameSite=Lax` (or `None` + `Secure`) on the
session cookie so the callback request still carries auth, and make the callback
route tolerate a missing session rather than 401-ing the whole flow.

**A per-account connection flag must be in the list response, or the UI never
updates.** The frontend polls `/status`, but the account table renders from
`/api/accounts`; if that query returns `SELECT * FROM accounts` with no join to
the token table, the row shows `○ Not connected` forever even after a successful
authorize. LEFT JOIN the token tables and expose `youtube_connected` /
`vk_connected` as 0/1 in the list payload.

## Key rules

1. **Order in nginx**: Specific callback routes (`^~ /smm/oauth/callback/.../`) BEFORE general panel proxy (`^~ /smm/`)
2. **State parameter — pass YOUR OWN state into both the URL and the flow object, and declare only the params the provider actually sends.** A callback declared as `def cb(code: str, state: str, account_id: int)` is a 422 in production: the provider echoes only `code` and `state`, never your custom query params. Pack the id into state instead (`state=f"{account_id}:{secrets.token_urlsafe(16)}"`) and unpack it in the callback (`int(state.split(":", 1)[0])`). With `google-auth-oauthlib` you must pass that same `state=` to **both** `flow.authorization_url(...)` and `Flow.from_client_config(..., state=state)` — otherwise the library generates its own state, the value that comes back is not yours, and `int(state)` raises. Verify the round trip by curling the callback with a hand-made `state`.
3. **Frontend polling**: Open OAuth window, poll `/status` endpoint every 2s
4. **Token storage**: Separate table per provider, linked by `account_id`
5. **Cookie vs Bearer**: Support both cookie auth and Authorization header for API calls
6. **When the backend API routes are under `/api/*`, ALL proxy_pass directives for that backend must target `http://127.0.0.1:<port>/api/...` — not just `/...`.
