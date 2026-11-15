---
name: beef-accounting
description: "Use when working with the beef accounting mini-app."
version: 1.1.0
author: Георгий
license: MIT
metadata:
  hermes:
    tags: [beef, accounting, mini-app, max, production]
---

# Beef — production meat accounting

## When to use

Inspecting, describing, testing or changing the meat accounting application at
`https://openclaw70846.hostkey.in/beef/`.

## Resolve the current source before acting

1. Read `/root/kb/projects/beef-accounting.md`, then inspect the actual service and
   nginx route. The KB contains historical designs and migrations, so later
   sections and deployed source take precedence over old descriptions.
2. The current frontend is `/root/beef-app/static/index.html`; backend is
   `/root/beef-app/server/app.py`, service `beef-app`, loopback port 8101.
   Nginx proxies `/beef/` and `/beef/api/` to that backend. The former
   `/usr/share/nginx/html/beef/index.html` container copy and
   `/root/beef-app/index.html` are not automatically the served version.
3. Compare the public HTML hash with the candidate source before modifying it.
   Do not deploy by copying into the legacy static container route.
4. Treat this as a live business application, not a public sandbox. Back up the
   affected files under `/root/n8n-backups/` and show the scoped production plan
   before writes. A portfolio update does not authorize changes to this backend.

## Architecture and secrets

- Browser HTML/CSS/JavaScript calls `/beef/api/`; Python talks to Supabase and MAX.
- Supabase project `nfccmklpycrkvaspcwvm`; tables include `carcasses`, `cuts`,
  `outputs`, `returns`, `app_settings`, `app_users`, `user_sessions`, `action_log`.
- Credentials are loaded server-side from `/root/.secrets/supabase.env`,
  `/root/.secrets/tokens.env` and `/root/.secrets/beef_issue.env`. Never embed
  keys, passwords, session tokens or signed MAX initData in HTML, reports or KB.
- MAX uses `MAX_TOKEN_BEEF_ISSUE` and the configured owner recipient. Do not send
  test operations casually: arrival/output/return may notify the real owner.
- Supabase `beef-photos` was public; verify its current policy before assuming
  photographs are private. A server-side key alone is not proof of access control.
- n8n workflow `AzPkOrJGdoOQ0PKw` is part of the project's history. Inspect active
  code before assuming an operation still goes through that workflow.

## Public demo (`/beef-demo/`) — static, no login

- Route: `https://openclaw70846.hostkey.in/beef-demo/`, served by nginx as plain files from
  `/usr/share/nginx/html/beef-demo/`. No backend, no Supabase key, no MAX.
- Source: `/root/beef-demo-static/` — `build.py` (derives the demo from the live production
  `static/index.html`), `demo-mock.js` (overrides `window.fetch` and answers `/beef-demo/api/*`
  from a localStorage dataset, sets a fake session token so `bootApp()` skips the login form),
  `deploy.sh` (docker cp + nginx block rewrite + reload). Rebuild after every production UI change.
- Never call something a demo if it runs the production `app.py`: that copy has auth-free
  `/api/stock` and can send real MAX messages. `/root/beef-demo`, `/root/beef-demo-app` and the
  stopped `beef-demo-app.service` were exactly that — do not resurrect them.

## Nginx and static-file pitfalls (verified)

- Nginx runs in the `nginx-nginx-1` docker container, host network, config in
  `/data/nginx/user_conf.d/openclaw70846.hostkey.in.conf`. Editing the file does nothing until
  `docker exec nginx-nginx-1 nginx -s reload` (run `nginx -t` first).
- `nginx -T` prints the file on disk, not the config in memory: after an edit that "does not work",
  compare the file's mtime with the master process start time before debugging anything else.
- `/usr/share/nginx/html` inside the container is **not** a volume: files uploaded with `docker cp`
  survive only until the container is recreated. Keep the source and a redeploy script on the host
  (`/root/portfolio`, `/root/beef-demo-static`), and check other static routes after a recreate —
  `/web-assistant/` was silently 404ing for this exact reason.

## Recovering a missing production frontend

- The backend serves the HTML file byte-for-byte, so any captured live page is a valid backup.
  Check `/tmp/beef-live.html`-style snapshots and the QA report sizes before hand-writing anything.
- Restore: back up `/root/beef-app/static` to `/root/n8n-backups/`, install the snapshot as
  `static/index.html`, then verify `curl /beef/` returns 200 with the expected size and that the
  login screen and menu render in a browser. Production is not under git — keep a copy after edits.

## Authentication and demo safety

- The current UI supports browser login/session and signed MAX launch data.
  Browser requests use `X-Session-Token`; MAX requests use `X-Max-InitData`.
  Public screenshots normally show the login page. Use the browser vault if an
  authorized login is actually needed; never type passwords from KB/chat.
- Test authorization per API route, not merely by whether the UI has a login.
  A read-only portfolio audit found `/api/auth/me` returning 401 and user-list
  routes returning 403 anonymously, while `/api/stock` returned 200 with stock.
  The source stock branch called `compute_stock()` without a permission gate.
  Recheck this finding before relying on it; it is not a claim about all routes.
- Never label `/beef/` an isolated demo or publish demo credentials without
  separately verified data isolation. A login screen does not prove isolation.
- Do not create production fixture records just for marketing screenshots.
  Use the real public login image and disclose its limitation, or arrange a
  genuinely separate demo environment. Do not fabricate a populated dashboard.

## Core operations

| Route | Purpose |
|---|---|
| `POST /api/arrival` | Register a carcass/cuts and photograph; may notify MAX |
| `POST /api/output` | Record an issue; may notify MAX |
| `POST /api/return` | Record a return; may notify MAX |
| `GET /api/stock` | Compute remaining stock |
| `POST /api/stock/send` | Render stock report and send to MAX |
| `/api/supabase/...` | Supabase proxy; inspect authorization and supported verbs |
| `/api/auth/...` | Login, current user, logout |
| `/api/cabinet/...` | Roles, settings, users and action history |

## Business-logic pitfalls

- Remaining stock means a cut is not issued **or has been returned**. Whole
  carcasses without cuts require a separate whole-item branch; zero cuts does
  not mean an error or zero inventory.
- Derive cut sets from `ARRIVAL_CUTS` in the current backend. Beef, pork and lamb
  differ; do not apply the beef cut count to every meat type.
- Preserve literal database identifiers. The stored cut name `ребра` differs
  from `рёбра`; normalizing it silently breaks half-carcass grouping.
- Issue and return use different recipient semantics. An issue must preserve
  the operator's explicit recipient selection when a carcass is chosen; a return
  may need the recipient from the last issue to select eligible cuts.
- Exercise the exact chain `recipient → meat type → carcass → cuts` after UI
  changes, reading state after every action. Single-screen tests miss resets.
- Day boundaries use UTC+8 for the business. Compare timestamps after explicit
  timezone conversion, not using the machine's timezone.
- Store photographs per input/operation, not in one shared global variable.
- URL-encode query values, particularly spaces and Cyrillic. Match the current
  PostgREST query syntax; do not reuse an old KB query untested.
- A successful Supabase response can contain an empty array without changing a
  row. Read the exact target back after writes; use appropriate upsert semantics
  when creation is intended. Never delete business records to make UI tests pass.
- DDL access is separate from REST keys. Do not guess a database password or
  treat service-role access as permission to perform arbitrary SQL migrations.

## Verification and delivery

1. Keep read-only inspection distinct from a production mutation test. Record
   the latter's approval, fixture IDs and safe cleanup before executing it.
2. Verify the served HTML, actual API responses, roles and changed UI sequence.
   Do not count code presence as proof of a successful live workflow.
3. Inspect each visible screen after shared CSS changes. Use computed token
   values and contrast measurements; intentional `.sr-only` clipping is not a
   visible layout defect. Theme history in KB is not the current theme contract.
4. Confirm the precise effect of external writes by reading back the target.
   Report separately what was tested, what remains unverified and what was not
   deployed. Update the project KB with source paths and evidence, never secrets.
