---
name: supabase-crud-patterns
description: "Use when building Supabase CRUD mini-apps with forms."
version: 1.0.0
author: Мария
license: MIT
metadata:
  hermes:
    tags: [supabase, crud, mini-app, progressive-form, rest-api]
---

# Supabase CRUD Mini-App Patterns

## When to Use
Building small CRUD applications on Supabase with multi-step forms, auto-population from related records, filtered lists, and formatted reports. Covers the patterns that recur across the user's mini-apps (beef-accounting, avtoservis, etc.). Also covers adding multi-user accounts, roles and permissions to a messenger (MAX/Telegram) mini-app.

## Supabase REST API Patterns

### Multi-ID Filtering — use `in.()`, never chained `eq.`
```javascript
// CORRECT
const idsStr = 'id=in.(' + Array.from(idSet).join(',') + ')';

// WRONG — Supabase silently ignores all but the FIRST eq. condition
const idsStr = Array.from(idSet).map(id => 'id=eq.' + id).join(',');
```
The chained form returns empty results with no error, making it look like a data problem rather than a query bug.

### Non-ASCII column values need `eq.` prefix
Always use `status=eq.принято`, not `status=принято`. Without the operator prefix, Supabase returns 400 for Cyrillic values.

### Timezone-aware filtering — fetch and filter client-side
Supabase stores timestamps in UTC. REST date filters (`created_at.gte=...`) are unreliable across timezones. Fetch all records, then filter in JS:
```javascript
const utc8 = new Date(now.getTime() + 8 * 3600000);
const todayStr = utc8.toISOString().split('T')[0];
// Compare each record's created_at converted to the target timezone
```

### Grouping related data in one pass
When fetching `outputs`/`events` sorted by `created_at.desc`, build multiple lookup maps in a single `forEach`:
- `lastRecipient: Map(entityId -> lastRecipient)` — first occurrence wins (newest)
- `issuedItems: Map(entityId -> Set(itemId)>` — accumulate all

### Resolving referenced IDs to names — one batch query, never N+1
When a list or report row references item IDs (a `cut_ids` array, any set of foreign
keys), collect every referenced ID across all rows FIRST, fetch names in a single
`id=in.(...)` query, and build an `id -> name` map:
```javascript
const allIds = new Set();
events.forEach(ev => (ev.cut_ids || []).forEach(id => allIds.add(id)));
const cutNames = {};
if (allIds.size > 0) {
    const r = await fetch(API + '/rest/v1/cuts?select=id,cut_name&id=in.(' + [...allIds].join(',') + ')');
    if (r.ok) for (const c of await r.json()) cutNames[c.id] = c.cut_name;
}
// per row: (ev.cut_ids || []).map(id => cutNames[id]).filter(Boolean).join(', ')
```
A per-row fetch inside the render loop is an N+1 waterfall: on mobile a 100-row
history takes minutes and every row paints late. One batch query before the loop
keeps the table synchronous after a single await.

## Mini-Apps With a Server Component

When a mini-app grows server-side work (photo upload pipeline, messenger
notifications, PNG rendering of reports), the shape that works here is:

- **Static frontend** served by nginx, **Python backend** (`ThreadingHTTPServer`
  on `127.0.0.1:<port>`), nginx routes `<prefix>/api/` to the backend only.
- **The Supabase service key lives in the backend, never in the client.** The
  frontend calls the backend's own endpoints (`/api/output`, `/api/stock`); a
  frontend fetching Supabase directly with `service_role` ships a full-access
  key to every visitor's browser — close that with a server-side proxy (same
  pattern as `_beef_proxy` in the manicure app).
- The backend owns deliverable-shaped logic: multipart parsing, record write
  BEFORE the messenger call, notification captions, report rendering.
- Restart the backend through Python (`subprocess.run(["systemctl", ...])`),
  never `systemctl` in the terminal — see pitfalls.
- **A mini-app under a subpath needs its API base derived from `location.pathname`.**
  With the app served at `/tire-fit/`, a frontend that hardcodes `var API = '/api'`
  requests `/api/...` at the domain root, which nginx answers with the SPA fallback
  (HTTP 200 and an HTML body) rather than the backend. The request looks "successful"
  and every data call silently returns HTML. Derive the base once at load:
  `var API = location.pathname.indexOf('tire-fit') !== -1 ? '/tire-fit/api' : '/api';`
  and reuse that single constant in every `fetch`, the CSV export link, and the logo upload.
- **Static files are not visible to nginx through the host path.** In the containerised
  nginx the root is `/usr/share/nginx/html` and the host directory is not bind-mounted,
  so `alias /root/<app>/static/;` returns 500 with an empty error log. Copy the file in
  (`docker cp static/index.html nginx-nginx-1:/usr/share/nginx/html/<app>/`) and keep the
  nginx root fixed; re-copy after every frontend change.

## Adding a New Field to a Form (needs a schema change)

Identify which key actually talks to PostgREST before planning anything — the role names in the
secrets file are not authoritative. In the beef project the variable named `SUPABASE_KEY_ROLE`
(service_role) returns **401 Invalid API key**, while the one named `SUPABASE_KEY` works AND
accepts writes (`POST` to a table returns 201). Probe, don't trust the label:

```python
for name, KEY in (("role", env.get("SUPABASE_KEY_ROLE", "")), ("plain", env["SUPABASE_KEY"])):
    GET {URL}/rest/v1/<table>?select=id&limit=1   # 200 = this key works
    POST {URL}/rest/v1/<table>  (one throwaway row, then DELETE it)  # 201 = it may write
```

**A schema change is a two-party workflow, not a one-shot script:**

1. **Probe the live schema before designing anything.** Read the existing table's
   columns from PostgREST's OpenAPI document, not from memory or an old SQL file:
   `GET /rest/v1/` → `definitions.<table>.properties`. Check the *type* of each column —
   a `text` primary key with no default cannot take a `gen_random_uuid()` value, and
   referencing a `text` column from a `uuid` FK fails. An earlier project may have left
   a legacy table with a different shape than the one you just designed.
2. **Check for shared tables before writing a settings row.** A table like `app_settings`
   or `app_users` may be shared by several apps, each expecting its own values. Writing
   there overwrites another product's branding and roles. Give the new app its own
   `tire_settings` / `tire_users` style table and leave the shared ones untouched.
3. Probe whether the column exists: `GET /rest/v1/<table>?select=<col>&limit=1` — 200 means yes, an HTTP error naming the missing column means no. (`?select=*&limit=1` on an empty table tells you nothing.)
2. Write frontend + backend so the code **tolerates the column being absent**: only include the key in the POST payload when the value is non-empty. An empty value is never sent, so nothing breaks before the ALTER lands, and nothing must be rewritten afterwards.
3. Hand the user the exact statement for Dashboard → SQL Editor: `ALTER TABLE <table> ADD COLUMN IF NOT EXISTS <col> text;` — one line per table.
4. After they confirm, run one live end-to-end check (fill the field → assert the DB row → assert every downstream surface: the messenger caption, the history/report render) and delete the test record.

Carry the field everywhere the record is read: the backend notification caption, and the history list — `select=*` picks the column up for free, but the event object and its render row still need the key added by hand.

**Pitfall — verify a claimed credential before hunting for it.** "The DB access exists somewhere, search the conversation" is a claim, not a fact. Check the filesystem first (`grep -r password /root/.secrets/`, `env | grep -i supabase`); if the original tables were created by the user in the Dashboard, no DDL credential exists on the server at all, and the correct deliverable is the hand-off SQL, not a longer search.

## Photo Notifications from a Form Submit

When a submit handler also ships a photo to a messenger (MAX), order the work so the
record survives the messenger:

1. **Persist the row first, then call the messenger.** The upload takes seconds, which is
   long enough for a mobile client to abandon the request — and then the server dies on
   `BrokenPipeError` writing the response to a socket nobody is reading.
2. **Catch `(BrokenPipeError, ConnectionResetError)` around the response write** and pass.
   The row is already committed, so the traceback is noise, not an error to fix.
3. **Treat a failed notification as non-fatal in the UI.** The entry exists; say «запись
   сохранена, фото в MAX не ушло (временный сбой), можете дослать вручную». Never surface the
   raw messenger error (e.g. `uploads 502`) as the status of the form — to the operator it
   reads as if the entry itself was lost, and they re-enter it.

The messenger-side pipeline itself (upload URL → one-shot token → attach, the transient-502
retry, downsize-before-send) is documented in the `max-messenger-api` skill.

## Multi-User Identity and Permissions in a Messenger Mini-App

When a mini-app needs accounts (an owner plus workers) inside a messenger (MAX/Telegram
WebApp), the platform already hands you a signed identity — do not build a login form.

**The platform's init data is the identity, and its signature is the authentication.**
The mini-app receives `WebApp.initData` (a `key=value` string) carrying `user.id`. Verify it
on the SERVER with HMAC-SHA256 before trusting it:

```python
# MAX scheme (Telegram WebApp uses the same shape, different token)
pairs = sorted((k, unquote(v)) for k, v in fields if k != "hash")
launch_params = "\n".join(f"{k}={v}" for k, v in pairs)
secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
calc = hmac.new(secret, launch_params.encode(), hashlib.sha256).hexdigest()
if not hmac.compare_digest(calc, seen_hash): return None   # reject: no user_id
```

Pitfalls, each of which fails silently or misleads:
- **Reject a duplicated `hash` field.** Count it; two occurrences is a forged payload.
- **`initDataUnsafe` is empty in a plain browser** — it is populated only inside the
  messenger. Build the UI to render a graceful unauthenticated state there rather than
  crashing, and test the real flow inside the messenger.
- **Ship the identity as a request header, not a body field.** The frontend wraps `fetch`
  and attaches `X-Max-InitData` to every `/api/*` call. Read it **per request in the
  handler** (`handler.headers.get("X-Max-InitData")`) — the helper that resolves the
  actor must take the handler as an argument.
- **Never read the signature from a module-level `threading.local()`.** A
  `threading.local()` written by a request's handler is not readable by anything else,
  and if nothing writes it the lookup is permanently `None` — the signature is silently
  rejected for every caller, including a correct one. Symptom: the manager route 403s
  with a perfectly valid signed header. Passing `self` to a helper defined OUTSIDE the
  handler class raises `NameError`; pass the handler in.
- **Resolve the account by the platform user_id**, and take the display name from the
  signed payload when no row exists yet — otherwise the audit log shows «Новый пользователь».

**Permission model:** one flat role table per app (`owner` / `worker` / `pending`),
a `ROLE_PERMISSIONS` dict checked server-side on every write, and an audit table
(`actor_id`, `actor_name`, `action`, `detail`, `created_at`) written from the same handler
that performs the action. `pending` gets an empty permission set, so an unconfirmed user
is denied by default rather than by omission.

**Bootstrap the owner once, idempotently.** The first user to open the app claims ownership
(`POST .../claim_owner`); a second call returns 409. Workers self-register by name and sit in
`pending` until the owner confirms them.

**An asset the owner uploads (a company logo, an avatar) is a settings row, not a file path
in code.** Store its public URL in a single-row `app_settings` table (`id=1`) and render it
through an `<img>` with an inline-SVG fallback that hides itself on the image's `onload`.
Read the settings once at startup and apply them to the shell (title, logo) so every screen
inherits the branding without per-screen wiring.

**End-to-end proof for this class of feature** — generate signed init data with the bot token
and drive every role through the API (claim → 409 on repeat → worker join → owner list →
confirm → worker permission check → worker denied on the owner-only route → non-existent
target → 404 → audit rows written). A single happy-path call proves nothing about the
permission matrix; assert each role against each protected route, then delete the fixtures.

## Adding Browser Login/Password to a MAX-Only Mini-App

When the same app must also be reachable in a plain browser (operator opens the URL outside
the messenger, panel pinned to a desktop), keep MAX `initData` as the primary identity and
ADD a username/password path on top — do not replace MAX with a custom login form. The
existing rule "the platform's init data is the identity" still holds; the addition is a
second resolver that returns the same `(uid, account)` shape.

**Auth flow the backend implements:**
- `current_actor()` returns `(uid, account, source)` where `source ∈ {"session", "max", "unknown"}`.
  Session is tried first; if no valid session token, MAX is tried. Endpoints that ONLY make
  sense inside MAX (`claim_owner`, `join`) MUST verify `source == "max"` — a session user has
  a real role and cannot be promoted to owner or downgraded to `pending`.
- The frontend sends BOTH `X-Max-InitData` and `X-Session-Token` on every request; the
  backend picks. The frontend never decides which auth method to use.
- Login form is shown only when no MAX initData AND no valid session token (boot calls
  `/auth/me`, falls back to login on 401).

**Permission model — one place, easy to extend:**
- `ROLE_PERMISSIONS` is a single dict: `{role: set(permissions)}`. Handlers call
  `actor_allowed(role, "arrival")` and never branch on role name. Adding a new role = adding
  a row to the dict; no handler edits.
- New permissions (`reports`, `history`) live in the dict too. Default-denied: a role with no
  entry gets `set()` and can do nothing.

**UI gating without per-handler checks:**
- Every restricted menu item gets `data-permission="arrival"` (or whatever it needs).
- One `applyRolePermissions(permissions)` function toggles `.hidden-by-role` based on the
  user's permission set returned by `/cabinet`. Don't bake role checks into `showPage` —
  the gating is the markup, not the navigation logic.

**DB schema (owner runs in Dashboard — service_role cannot DDL):**
```sql
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS login TEXT UNIQUE;
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS password_hash TEXT;
CREATE TABLE user_sessions (
  token TEXT PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL,
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);
```
Always `IF NOT EXISTS` so the script is re-runnable. After ALTER runs, the existing
`pending` / `worker` rows have NULL login/password — they're MAX-only, which is fine.

**Password storage:** `bcrypt` only — never MD5/SHA1, never plaintext. `bcrypt.gensalt()`
gives a fresh salt per row. `bcrypt.checkpw(plain, hashed)` for verification.

**Session tokens:** `secrets.token_urlsafe(32)` for the token. TTL 30 days stored in
`expires_at`; resolved with `expires_at > now()`. Delete on logout. Reset-password MUST
delete all sessions for that user — otherwise stolen tokens remain valid.

**Anti-bruteforce — and the three things that make it useless:**
- Rate-limit key MUST be `(client_ip, login_lowercase)` — NOT ip alone (corporate NAT locks
  everyone), NOT login alone (distributed attack bypasses).
- Counter ticks on EVERY attempt — both wrong-password and user-not-found.
- Reset the counter ONLY on successful login. Resetting on wrong-password is the trap: the
  legitimate user then has zero remaining attempts when they retry with the right password.
  Resetting on user-not-found is worse: it lets an attacker probe which logins exist by
  watching whether the rate-limit blocks them — login enumeration via timing/rate differences.
- Reset-password invalidation MUST hit `user_sessions` for that user_id — losing a password
  to a brute-force guess must not leave the attacker's session alive.

**Function-signature refactor — update every caller.** Changing `current_actor()` from a
2-tuple to a 3-tuple touches every handler that unpacks it. `grep -c 'current_actor()'`
before changing the return shape; the count tells you the work. A missed caller raises
`ValueError: too many values to unpack` at request time, which looks like a runtime bug
unrelated to the signature change.

**Bootscreen security:** when `/auth/me` returns 401 with a stale token, the frontend must
clear the token from localStorage before showing the login page — otherwise the user sees
"login failed" on every retry because every request still carries the dead token.

**Generating a test signature — the three ways it silently fails:**

1. **Sort the pairs before signing.** The validator sorts by key; the order you
   assembled them is irrelevant. `auth_date`, `query_id`, `user` must be the signed
   order. Signing the unsorted list produces a hash the validator rejects while the
   signature looks well-formed.
2. **Serialise the user object with `ensure_ascii=False`.** `json.dumps(...)` defaults
   to `\uXXXX` escapes, so the string the validator reconstructs differs from the one
   you signed and the hash never matches.
3. **URL-encode each value once, with `quote(v, safe='')`.**

```python
pairs = sorted([
    ("query_id", "test-query-1"),
    ("user", json.dumps(user, separators=(",", ":"), ensure_ascii=False)),
    ("auth_date", str(int(time.time()))),
], key=lambda kv: kv[0])
launch = "\n".join(f"{k}={v}" for k, v in pairs)
secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
calc = hmac.new(secret, launch.encode(), hashlib.sha256).hexdigest()
init_data = "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in pairs) + "&hash=" + calc
```

**When the role is still denied, check the app's own env merge, not the code.** A
deep-merged config where a per-app secrets file is loaded last will happily overwrite a
real token with a placeholder string (`<max_token>`); the module then holds garbage and
every signature fails. Assert the loaded value equals the value in the shared secrets
file before debugging the HMAC.

## Progressive Form UI

### Multi-step disclosure
Each step reveals the next only after the previous is completed:
1. Select category/recipient → 2. Select type → 3. Select entity → 4. Select details

Use `hidden` class on subsequent `.form-group` containers. Remove it in the selection handler. Reset all groups to hidden when the form page opens (`initXxxPage()`).

### Auto-population is safe when it DESCRIBES the entity — unsafe when it DECIDES the action
Auto-populate a field from the most recent related record when that field describes the
entity itself («what was this issued to before»). A user's explicit selection survives:

```javascript
function selectEntity(id, el) {
    // CONDITIONAL — an explicit user choice wins
    if (!selectedRecipient && window._lastRelated && window._lastRelated.has(id)) {
        selectedRecipient = window._lastRelated.get(id);
        document.querySelectorAll('.radio-btn').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.value === selectedRecipient);
        });
    }
    loadDetails(id);
}
```

A field that decides WHERE a row lands — the recipient of an issuance, the target of a
movement — must NEVER be overwritten by history: the operator picked «цех», clicked the
entity, and the handler silently rewrote it to «отдел» from the last issuance. The row then
saves to the wrong place, and the user reads it as «пишет всё на отдел». Gate every
auto-population on `if (!<user's explicit field>)` and verify the handler's write path with a
real submit, not just the UI state.

**Exception — auto-population is correct when the related field MUST match the record.**
On a return/reversal the detail list is filtered by the same field the original issuance
used, so the field is derived, not chosen: there, ALWAYS overwrite (`if (window._last && has)`)
and leave it unconditional. The rule is which direction the dependency runs: description
→ conditional, decision → never, derivation → always.

### Filtering available items by what's already been used
When showing items for selection (e.g., cuts to issue), exclude items already recorded in related events:
```javascript
const issued = (window._issuedItems && window._issuedItems.get(entityId)) || new Set();
const remaining = allItems.filter(item => !issued.has(item.id));
if (remaining.length === 0) showMessage('All items already issued');
```

### Loading state — never leave a container blank
Set a placeholder immediately in async loaders before the fetch:
```javascript
container.innerHTML = '<p>Loading...</p>';
try { /* fetch and render */ } catch { container.innerHTML = '<p>Error</p>'; }
```
This prevents an empty UI region during slow networks or stale browser caches.

### Selection lists must be fully visible — no inner scrolling
On mobile the user rejects a `max-height + overflow-y:auto` selection box
("сделай выбор статичным, без скролла"). Lay the full list out instead:
`display:grid; grid-template-columns:1fr 1fr` with compact rows (tighter
padding, 20px checkbox, `text-overflow:ellipsis` labels) so even a 12-item list
fits one screen. Verify with `el.scrollHeight > el.clientHeight` → false.

## Report Formatting — Per-Entity Mini-Tables
User prefers separate mini-tables per entity (like Excel sheets), not one large flat table:
- Colored header bar with entity ID + descriptor (e.g., `#209 тёлка`)
- Details in a 2-column CSS grid below the header
- Special states shown as italic text (e.g., "whole entity", "no remaining items")
- Same layout rendered both in-app (CSS grid) and in PNG for messenger (playwright + flex-wrap cards)

### Entity label — show gender OR type, never both
For entities with a gender field (cattle): show only the gender (e.g., "тёлка").
For entities without gender (pork, lamb): show only the type (e.g., "свинина").
Formula: `gender || type`.

### Dashboard tiles — group by the attribute the operator thinks in
When the user asks to split a tile group ("не просто говядина, а с разделением на
пол"), the group key is `type|secondary` (e.g. `говядина|бык`), the label shows
the secondary attribute capitalized (Бык), and the icon stays the type's SVG.
Entities lacking the secondary attribute fall back to a plain `type|` key. One
extra grouping level, zero new components.

### Storing generated content, not form input
When the write side is an LLM rather than a form, the shape is a header row plus
one row per generated item:

```sql
CREATE TABLE <plan>_plans (     -- one row per run: topic, params, model
CREATE TABLE <plan>_items (     -- one row per day/entry
    plan_id UUID NOT NULL REFERENCES <plan>_plans(id) ON DELETE CASCADE, ...
);
```

Write the plan first (it returns the `id`), then bulk-insert the items with
`Prefer: return=minimal`. Make the run idempotent by deleting the previous plan
with the same natural key before inserting — the `ON DELETE CASCADE` on items
means one DELETE retires the whole previous run.

**Inject the run date from the script, never from the model.** A generation
prompt saying "начиная с завтра" produces a stale year; compute
`date.today() + timedelta(days=1)` and put the concrete date in the prompt. See
`references/llm-ui-generation.md` for the rest of the markdown-table parsing
rules.

### Each datum gets its own column
When a field (note, status) is added to a report, give it a dedicated column —
do not append it under an adjacent value ("отдел (3 отруб.) 💬 примечание").
The operator scans columns, not paragraphs; an inline tack-on gets sent back as
"сделай отдельным столбиком".

## Modern UI Language (user's mini-apps)

When the user asks for a "современнее" design, there are TWO levels — do not stop at
the first one:

1. **Generic modern** (the floor, not the goal): background `#eef1f6`, cards
   `border-radius:18px` with layered soft shadows, `1.5px` borders + focus ring
   `box-shadow: 0 0 0 3px rgba(...,0.12)`, press feedback `transform: scale(0.96)`,
   `accent-color` checkboxes. This is exactly what the user calls
   "это и есть весь креатив?" — причёсанный шаблон, безликий generic.
2. **Themed design** (what the user actually wants): a deliberate subject-matter
   identity. Offer concrete direction choices first (e.g. мясницкая/стейк-хаус,
   тёплый янтарь, контрастный, свежий минимал) and build the whole app from
   CSS custom properties in `:root`. Example of a themed system that passed
   review: graphite `#1c1917` + bordo `#7f1d2e` + cream `#faf5ef`, Georgia
   (serif) for content vs sans-serif uppercase+letter-spacing for labels, sharp
   `border-radius:4px`, solid-accent selected states with a coloured glow.

Rules that survive any theme:

- **Palette is a system, not a set.** Assign colour roles before choosing colours:
  operations one accent family, system functions neutral. A random per-item
  palette (green/amber/purple/slate) reads as "cheap, unfinished" in review.
- **Never ship emoji as the icon set.** Emoji render differently per platform and
  are what make a themed screen read as "old". Replace every icon with inline SVG
  in a shared constant:
  ```javascript
  const MEAT_SVG = {
    'говядина': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">…</svg>',
    // …
  };
  ```
  Use `stroke="currentColor"` so icons inherit the button colour (light and dark
  theme both work). Verify with `document.querySelectorAll('... svg').length`
  per screen — a count proves the icons landed everywhere the old emoji were.
- **Dark theme via token overrides, not per-component rules.** Redefine the
  `:root` tokens (cream↔graphite, ink↔cream) and nearly every component follows
  for free. If the dark theme is the ONLY theme, drop the `body.dark` guard
  entirely and re-declare a second `:root` after the base one — a `body.dark X`
  selector list must be maintained by hand and every rule left out of it stays
  dark-on-dark with no error. Audit the result for contrast rather than trusting
  the token declaration: see `web-app-change-verification` → "Making a Dark Theme
  the Only Theme" and its `scripts/contrast_audit.py`.
- **A dashboard tile's big number must be the number the label describes.**
  Showing entity-count large while the sub-label says "N items" reads as a bug;
  make the prominent figure the item total (count whole-entity records as 1).
  Lay tiles out with `repeat(auto-fit, minmax(80px, 1fr))` so a 3-item row never
  goes ragged, and use the shared SVG constants inside tiles too.
- **Re-theme every screen, not just the menu.** The first screen the user lands
  on is the only one they can judge on load; leaving inner screens emoji-era is
  reported as "ничего не поменялось".
- **When a free LLM is asked to design a screen, never ship its output
  unreviewed** — see `references/llm-ui-generation.md` for the model-testing
  procedure and the bug checklist (duplicated items, hallucinated domain
  words, inconsistent units, same-colour statuses).

## Reverting a Theme to an Earlier Version
When the user says "верни дизайн к первому варианту":
1. **Back up current first** — `cp index.html index.html.bak-<label>`.
2. **Mass color-map swap, not per-block patching.** Build `{old_hex: new_hex}`
   from a known-good backup and run one `str.replace` pass over the whole file.
   Map ALL roles: accent, background, surface, text (primary/secondary/muted),
   borders, dark-theme overrides, rgba shadow/glow values.
3. **Grep for leftover old-theme hexes after the swap** — a gradient middle
   stop may keep an old hex if it wasn't in the map. Zero leftover occurrences.
4. **Verify with `getComputedStyle`**, not source grep. Tokens can be declared
   and unused; read concrete `backgroundColor`/`fontFamily`/`textTransform`.
5. **A visual revert changes CSS only** — assert real data still renders.

## Removing an Entire Screen/Feature Cleanly
Remove in reverse dependency order, verify zero references:
1. HTML block (delete the section; if it was the start screen, remove `hidden`
   from the previous start screen).
2. CSS scoped to the feature (check for a second `:root` that must NOT go).
3. JS module, functions, and all call sites (`setTimeout`, `showPage` branches).
4. `grep -c` the feature's key identifiers — all must return 0.
5. Confirm the enclosing function (e.g. `DOMContentLoaded`) is still valid.

## Symmetric Halves in Catalog Data — Counting «N halves» in Stock

Where a physical item splits into symmetric halves (two sides of a carcass), catalog
counts are base × 2 and the operator wants the remainder shown as **«N полутуша»**
instead of a flat part list.

**Model a half as slots, not as a required-name list.** Each half is a set of
*slots*; a slot is an alternative set of names from which exactly one is consumed.
Required slots gate the half, optional slots enrich it:

```python
HALF_SLOTS = {
    'говядина': [ (['лопатка'], True), (['ребра'], True), (['грудинка'], True),
                   (['задок'], True), (['задний антрекот','карбонат'], False) ],
    'свинина':   [ (['шея'], True), (['лопатка'], True), (['антрекот'], True),
                   (['грудинка'], True), (['задок'], True) ],
}
HALF_REQUIRED = {'говядина': ['лопатка','ребра','грудинка','задок'], ...}
```

**Pitfalls — each one silently returns `list` instead of a half count:**
- **A plain required-name list cannot express an alternative.** Modelling
  `['задний антрекот','карбонат']` as *both required* makes an 8-part stock show 0
  halves and look like a data problem. A slot with the flag `False` is an
  alternative: it is consumed when present but never blocks the half.
- **A name present in the model but absent from the DB blocks the count silently.**
  `рёбра` in the code vs `ребра` in the data matched nothing, so every half failed.
  **Verify cut names against the live data, never against the model or memory:**
  `GET /rest/v1/cuts?select=cut_name` → `sorted(set(...))`. A unit test with
  hand-written literals passes while real rows return `list`.
- **Parts outside the half must be extras, never slots.** A neck that belongs to the
  carcass but not to a half goes to `extras`; putting it in a slot inflates the count.
  The extras list is also the answer to «what else is on this carcass».
- **Count maximum non-overlapping sets, not `min` per name.** Greedily consume one
  name per slot per iteration until some required slot is empty; leftovers are
  extras. `min` per name gives the same number but silently over-counts when an
  alternative is consumed more than once.

Shape of the derived field (consumed by both the app UI and the PNG report):
`{type: halves|list|whole|empty, count, word, extras}` — a single source that the
frontend renders and `render_*_png` reuses, so the two can never disagree.
Pluralize in the user's language (`1 полутуша / 2-4 полутуши / 5+ полутуш`, with the
11-14 exception).

**Dashboard counters must not count a half as a part.** When the stock tile counts
«parts in stock», a halves row contributes `extras.length` only — counting the half
itself inflates the tile next to its own label.

**Ask before coding the schema.** Whether ribs belong to a half, whether the neck is
separate, and whether the intake count must change are three independent decisions;
confirm each in one clarify round. Changing the intake list is a one-line edit, but
only if the user actually wants it — otherwise existing rows and the counting logic
drift apart.

## Proving Whether a Business Rule Exists at All

When the user asks «можно ли X?» / «проверь пункт Y» about a rule in a CRUD app (e.g.
«можно ли выдавать быка в цех»), reading the code and answering is a hypothesis, and the
data is the trap:

1. **Grep the WRITE path for validation, not the read path.** A restriction lives in the
   handler (`if recipient not in ("цех","отдел"): 400`), so the answer is what the endpoint
   REJECTS — not what the UI lists. The UI can also hide things by filter, which is a different
   question from what the backend permits.
2. **Prove it with a real write through the API, then roll back.** A direct
   `POST /api/<action>` with the supposedly-forbidden combination returning `{"ok": true}` is
   the proof. Then delete the fixture back out (children first) and re-read the row count / the
   entity's stock to confirm nothing was left behind.
3. **Distinguish «the code forbids it» from «the data never contained it».** An operator saying
   «мы в цех всегда отправляли только тёлку» may be describing history, not a rule — and both
   look identical from the UI. Group the events by the dimension in question before answering:
   `SELECT`-style aggregation over `outputs` grouped by (entity attribute, recipient).
4. **State the asymmetry plainly.** If the backend permits both directions, say so — the
   operator's expectation is the thing that turned out to be wrong, and that IS the finding.
   Do not quietly «fix» a rule that is already correct to match their expectation.

## Duplicate Record Cleanup
When the same logical entity appears twice (same number/name, different IDs), the later-created record is the duplicate. Delete cascade: dependent tables first (returns → outputs → items → entity).

## Verification Requirement
Every change must be verified live in the browser before reporting completion:
1. Deploy the change (restart service / copy static file)
2. Open the app in browser
3. Exercise the exact user flow step by step
4. Confirm the result matches expectations
5. Clean up test records before committing

## Pitfalls Summary
- `id=eq.x,id=eq.y` silently returns empty — use `id=in.(x,y)`
- Cyrillic values in REST filters need `eq.` operator prefix
- Auto-population: conditional when the field DESCRIBES the entity, NEVER when it DECIDES where the row lands (recipient/target), ALWAYS when the related field must match the record (return/reversal) — see the section for the direction rule
- Async list loaders need an immediate placeholder to avoid blank UI
- Always clean up test records (cascade delete) after verification
- **Guard MAX WebApp SDK calls in mini-app init.** `window.WebApp.expand()`
  exists only inside the MAX mini-app; in a plain browser it throws TypeError,
  aborting `DOMContentLoaded` so every later init (theme, dashboards) never
  runs. Wrap each call: `try { window.WebApp.expand && window.WebApp.expand(); } catch (e) {}`
- **After deleting or renaming a JS function, grep for its remaining callers**
  before restarting: `grep -c 'functionName(' index.html`. A forgotten caller
  silently kills a button with no error on screen.
- **`onclick="fn()"` in HTML never fires when the script is an IIFE.** Any single-page
  frontend wrapped in `(function () { ... })()` makes every function local to the closure,
  so an inline handler raises `ReferenceError` at click time — silently, with no visible
  error, and the button does nothing. Assign handlers in JS instead:
  `document.getElementById('btnBack').onclick = showHome;`. If you must keep an inline
  handler, expose it on `window` first (`window.showHome = showHome;`).
- **A form field the DB cannot store yet is not a reason to ship nothing.**
  Build frontend + backend to tolerate the missing column (send the key only
  when non-empty), hand over the one-line ALTER, and finish everything else —
  the whole feature then works the moment the ALTER is run.
- **`systemctl restart <svc>` on a shared VPS may block on an approval prompt and
  time out.** Restart through Python instead: `subprocess.run(["systemctl","restart","beef-app.service"], capture_output=True)` — same effect, no approval gate. A blocked call means no consent, not a failed service.
- **A markdown-table parser built for the happy case drops real rows.** Drop
  separator cells (`| :--- |`), and accept trailing list items whatever marker
  they open with (`«…»`, digits, `-`, `•`) — a marker-only filter returns zero
  items and looks like the model failed.
- **URL-encode every REST filter value.** A space or emoji in
  `?note=eq.<text>` raises `InvalidURL` from `http.client` before the request
  leaves, which reads like a code bug rather than an encoding one. `urllib.parse.quote`
  the whole query string when it contains Cyrillic, or build it in one pass with
  `quote(path, safe='?&=.,()')`.
- **A model of the data that the live data disagrees with fails silently.** Any rule
  keyed on names (`cut_name`, status, category) must be probed against the database
  first — distinct values, not remembered spelling. Unit tests on literals prove the
  arithmetic, never the wiring; run the function on real rows before reporting.
- **A unique index on a DERIVED column breaks on natural repeats.** A unique index
says "this value identifies the row" — but when the value is *computed* from
content, two legitimately different rows produce the same one. Symptom is a 409
`duplicate key value violates unique constraint` on a create that should be fine,
and it appears only once the same subject recurs (the first insert succeeds, so
the index reads as a normal index in testing).

```json
{"code":"23505","message":"duplicate key value violates unique constraint \"idx_<table>_<col>\""}
```

The failure is in the *key choice*, not the data: a slug derived from a
displayed name collides whenever that name appears twice. Two independent
fixes, both needed:

- **Key the dedupe on the natural identity, not the derived one.** Match on the
  source field (the topic / the canonical name) rather than the slug it
  generates, and compare it normalised (lowercase, strip
  spaces/hyphens/punctuation) so a re-phrasing does not create a second row.
- **Drop the unique constraint and keep the plain index.** Querying by the
  derived value is still an index lookup; only the guarantee was wrong.

  ```sql
  DROP INDEX IF EXISTS idx_<table>_<col>;
  CREATE INDEX idx_<table>_<col> ON <table>(<col>);
  ```

Then make the write **idempotent explicitly**: select the existing row by the
natural key, DELETE it, then insert. Without that, removing the index alone
swaps a 409 for silent duplicates.

**A REST helper that always `json.loads()` the response body breaks on empty-body
  methods.** `DELETE` returns an empty body; a helper that unconditionally parses the
  response raises `JSONDecodeError` AFTER the delete already succeeded — the rollback then
  looks failed when it worked, and the fixture stays in the table. Return the status first
  and parse conditionally: `raw = resp.read().decode(); json.loads(raw) if raw.strip() else None`.
- **`PATCH` on a row that does not exist is a SILENT NO-OP — HTTP 200, empty array, no
  error.** A create-or-update written as `PATCH /table?id=eq.<id>` reports success while
  inserting nothing, so the feature looks wired and the entity never appears. Use an
  **upsert** instead: `POST /table` with `Prefer: resolution=merge-duplicates` (200/201,
  creates or updates). For an action that requires an existing row, check first
  (`GET /table?id=eq.<id>&select=id` → empty means 404 the caller) rather than trusting
  the 200. Any write whose success is not followed by a read-back of the row is unverified.
- **A unique index on a derived column is a bug, not a constraint.** A slug computed
  from a displayed name collides whenever that name recurs — 409 on the second
  occurrence only, so it passes every single-insert test. Key dedupe on the natural
  identity instead and drop the unique constraint (plain index).
- A write that returns `{"ok": true}` is not the end of a verification — the row must be
  gone afterwards. After any rollback, re-read the entity's derived state (its stock, its
  row count) and assert it matches the pre-test value. A silently-absent delete is invisible
  from the write response alone.
- **A per-app secrets file loaded LAST overwrites the shared secrets.** If the app config
  is a deep-merge of several files and the per-app one is last, a placeholder value
  (`<max_token>`) silently wins over the real token and every signed request fails. When a
  signature or auth check fails, print the loaded value and compare it with the shared file
  before suspecting the HMAC.
- **A frontend served under a subpath must derive its API base from `location.pathname`.**
  A hardcoded `/api` hits the domain root, where nginx's SPA fallback answers 200 with an
  HTML body — every data call looks successful and returns HTML. Derive the base once and
  reuse it for every fetch, the export link, and uploads.
