---
name: service-credentials-vault
description: "Use when storing or loading service API keys."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [credentials, secrets, api-keys, environment, security]
---

# service-credentials-vault

Store every third-party API key in one durable, discoverable place and load it from there, so any new project can pick up credentials without asking the user to re-paste them.

## When to Use

- The user says where to keep API keys, or asks to set up credential storage.
- Any task needs a service key (n8n, Supabase, Google service account, OpenRouter, Telegram/MAX tokens, payment or hosting providers).
- A key currently lives somewhere ephemeral — a temp/scratch dir, a chat transcript, a stray file in the project tree.
- Auditing where secrets live before a production change.

## Canonical location

`/root/.secrets/` — directory mode `700`, every file `600`. Layout and per-service loading recipes: `references/vault-layout.md`. Run `scripts/verify-vault.sh` for a read-only perms/inventory/leftover-artifact audit — it prints key NAMES, never values. `/root` is already `700`, so non-root users on the box cannot traverse into the vault.

`/root/.hermes/.env` is for **Hermes' own** settings only (its own bot token, its search keys). Service credentials never go there — it is not project-scoped and it does not survive a Hermes reinstall. The vault is deliberately outside `$HERMES_HOME` so a profile wipe cannot take the keys with it.

## Procedure

1. **Survey before moving anything.** Find every candidate secret location and what is already there:
   ```bash
   ls -la /root/.secrets /root/.hermes/.env 2>/dev/null
   grep -o '^[A-Z_]*=' /root/.hermes/.env 2>/dev/null   # names only, never values
   stat -c '%a %n' /root /root/.secrets 2>/dev/null
   ```
   Report the inventory to the user before creating anything. If the layout already exists, extend it rather than inventing a second one.

2. **Move, do not copy.** A key left behind in the old location is still an exposure. `mv`, then confirm the old path is gone. `.env` files hold plain `KEY=VALUE`, no `export`, no quotes.

3. **Do not create placeholder secret files.** An empty `n8n.env` is a trap for a future session that assumes the credential exists. Declare not-yet-supplied keys in the README instead, and create the file when the value actually arrives.

4. **Verify with a live request, not a file read.** A valid JSON key file proves nothing about whether the credential works. Sign a token / call the API / list the resource and paste the real status. A 403 from a hand-rolled request may mean a missing auth header rather than a bad credential — check the header before blaming the key.

5. **Clean up transient artifacts.** Manual JWT signing leaves base64 key and signature files next to the vault; `shred -u` them, then confirm removal.

6. **Record locations, never values.** Memory and profile files store `/root/.secrets/<file>` and the service name. The vault README documents every file and how to load it, so the next session needs no hand-off.

## Auditing a suspected client-side exposure

Use when a page, mini-app or static bundle is served publicly and holds — or may hold — a service key. Verify from OUTSIDE, because the project source and the served bytes are different copies.

1. **Fetch the live route the way a visitor does:**
   ```bash
   curl -s -o /tmp/page.html -w "http=%{http_code} size=%{size_download}\n" https://<host>/<path>/
   ```
   HTTP 200 on the route that contains the constant is the confirmation; anything else ends the audit as clean.
2. **Extract and decode the token payload to learn the real privilege level — print the decoded claims, never the value.**
   ```python
   import base64, json, re, pathlib
   tok = re.search(r"['\"](eyJ[A-Za-z0-9._-]+)['\"]", pathlib.Path('/tmp/page.html').read_text()).group(1)
   pl = tok.split('.')[1]; pl += '=' * (-len(pl) % 4)
   print(json.loads(base64.urlsafe_b64decode(pl)))   # role, ref, exp
   ```
   Report `role`, project ref and `exp`. A `service_role` (or owner-equivalent) JWT in a served page is a full-access credential handed to every visitor; a JWT with no `exp` means the leak is not time-bounded and only revocation ends it.
3. **Compare it against the vault copy to learn which stored secret is burned.** A byte-identical match means the production key, not a spare — the blast radius covers every service that shares that vault file.
4. **Hunt the copies before declaring the exposure bounded:** the project tree, every web root the proxy container serves, and any backup export that might embed the value. An orphan build artifact outside the served path still carries a live credential, and it is the copy nobody deletes.
5. **Present the rotation ordering as an explicit choice** — it is the user's call, not a technical default. Revoke first and the live consumer breaks immediately; fix the consumer first and the key stays public in the meantime. Say what each option costs, then wait for the decision.
6. **The fix is a server-side proxy, not a redaction.** Strip the key from the shipped file and add a forwarding route on a process that already talks to that service server-side, so the frontend's calls survive unchanged behind a relative base path. Enumerate every HTTP verb the page used before writing the proxy — see `web-panel-on-existing-vps` step 12 for the `BaseHTTPRequestHandler` 501 trap that makes a GET/POST-only proxy break DELETE in prod.

## Pitfalls

- **A privileged key in a served page is not defended by row-level security.** `service_role` bypasses RLS entirely, so "the tables have policies" is not a mitigation while the shipped key is owner-level. Anon key plus RLS, or server-side proxying, are the only two shapes that actually close it.
- **Never store a key value in MEMORY.md, USER.md, SOUL.md, a skill file, or the chat.** Memory is injected into every prompt; a pasted key outlives its usefulness and leaks everywhere. Reference the path instead.
- **Scratch/temp dirs are not storage.** `$TMPDIR`/scratch paths get pruned on ttl and crash-boot cleanup — a private key parked there can vanish without warning, taking the project's access with it. Temp is for probes; the vault is for anything load-bearing.
- **Verify the "backup" files are actually clean.** Workflow JSON dumps may hold credential values even when the service stores them by reference. Inspect before declaring a backup directory safe, and do not assume — exports often embed resolved secrets that the UI never shows.
- **`800` vs `700`:** a vault readable by group/other is an exposure on any multi-user host. Check with `stat -c '%a %n'` after every write, including files created by tools that don't inherit your umask.
- **Cross-service key reuse is a fact to record, not to assume.** When one token serves two platforms, note the path and the fact once; do not go hunting for a second secret, and do not duplicate the value.
- **Revocable keys need a rotation note.** A private key file is not the secret's identity — record which account/SA it belongs to and that deletion of the file does not revoke access.
- **Decode a credential's own metadata before trusting its lifetime claims.** An API key that is a JWT may carry no `exp` claim at all, meaning it never self-expires and can only be revoked in the issuing UI. Report that when you store it — the user needs to know a leak is not time-bounded.
- **A service may hold credentials that never leave it, and that is correct.** Bots and workflow engines store their tokens in an internal credential store referenced by id; exports and backups then contain only the id. Before asking the user for a key to "fix" a workflow, check whether the platform already holds it — and never try to extract a value that the API deliberately does not return.
- **When the user says "just ask me for whatever keys you need", answer with a list of the ones actually missing** and what privilege level each needs (e.g. write-capable vs read-only), not a general request for credentials. Naming the specific file and the specific reason keeps the user from over-granting.

7. **Rotating a stored value means editing the file in place, not rewriting it.** A secret file may hold more than the key you are changing — a hook secret on line 2, a project ref, a comment block. `printf 'newvalue\n' > file` truncates everything after line 1 and the collateral loss surfaces later as a mystery 401 on an endpoint you were not touching. Either patch just the target line, or re-read the file first and rewrite it complete. After the write, assert the file still has the same number of non-empty lines and that each unrelated value is byte-identical, then live-test BOTH the changed path and the neighbour that shares the file.

   **Check the line count immediately after the write, not only when a neighbour
   401s.** The collateral loss is silent and the symptom surfaces far from the edit:
   the second line keeps serving a webhook signature or an app password, and the
   first evidence is an unrelated feature rejecting valid input hours later. The tell
   is in the byte count — `wc -c` before and after; a multi-line secret file that lost
   lines shows up as a sudden drop, and that is the moment to restore the neighbour
   rather than an hour later when some other endpoint starts failing.

## Reporting

Say which files now exist, their modes, what was verified live (with the actual status code), what remains unfilled, and which old paths were removed. State plainly if a suspected leak turned out to be clean — a wrong alarm costs the user time.