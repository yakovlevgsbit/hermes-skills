---
name: hermes-dashboard-auth
description: "Use when changing Hermes dashboard login credentials. Reset safely and verify the active service."
version: 2.0.0
author: Masha
tags: [hermes, dashboard, authentication, password]
related_skills: [hermes-agent]
---

# Hermes dashboard authentication

## Scope and prerequisites

Load `hermes-agent` before changing Hermes. Consult the installed CLI/source and the official dashboard documentation:
https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard#usernamepassword-provider-no-oauth-idp

- Distinguish dashboard credentials from Linux accounts, provider API credentials, Nous Portal, and messaging pairing. A menu selection such as `2` is not a chosen password.
- Discover the active profile and actual service. Use `command -v hermes`, `hermes dashboard --help`, and `systemctl --user show hermes-dashboard.service -p MainPID -p ExecStart -p WorkingDirectory` where systemd is present. The dashboard and messaging gateway are separate processes.
- Read only the required setting: `hermes config get dashboard.basic_auth.username`. Do not dump the whole auth section or unrelated credential stores. On the operator's default installation the observed username is `yakovlevgs`, but verify it rather than treating it as universal.

## Credential safety

- Do not ask for passwords in chat or repeat passwords, signing keys, cookies, or tokens in outputs. Use supported vault/masked input. Never type a password with browser input/JS tools or extract one from the DOM.
- Use the installed `plugins.dashboard_auth.basic.hash_password` helper to create a salted hash from securely supplied input. An already-generated hash may be applied only when its provenance ties it to the authorized password change; an arbitrary old hash is not a recovered password.
- The installed basic provider uses `scrypt$n$r$p$salt_b64$digest_b64`; known parameters are n=16384, r=8, p=1, a 16-byte salt and a 32-byte derived key. Check the installed implementation rather than assuming this forever.
- Keep plaintext out of shell arguments, scripts, files, logs and tool results. Never print a full config, `_settings()` result, or environment. Inspect only selected non-secret fields and boolean comparisons.
- A denied sensitive-file write is not permission to switch to sed, Python, or another lower-level writer. Use the supported `hermes config` operation; stop if that authorized route is refused.

## Safe password change

1. State the production scope: password only, backup first, restart only the dashboard. Keep the username and unrelated settings unchanged.
2. Check effective auth resolution. The basic provider's `_settings()` resolves config/environment through Hermes's normal loader. Nonempty `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` overrides a config hash; an environment hash can also override the config value. Inspect presence/comparisons without displaying values. Do not read protected credential stores through a bypass.
3. Save and verify an exact pre-change config backup in a private subdirectory of `/root/n8n-backups/` (directory 0700, file 0600). Keep secrets out of any human-readable report.
4. Apply the authorized hash using `hermes config set dashboard.basic_auth.password_hash <hash>`. Pass arguments without shell expansion of `$`. Never replace a hardcoded line number or hand-edit YAML.
5. Read back the exact setting and compare the parsed config before/after. Only the intended field should differ. Confirm the effective resolver selects the new hash and expected username.
6. Restart the discovered dashboard service only, e.g. `systemctl --user restart hermes-dashboard.service`. Do not restart the messaging gateway to refresh dashboard auth.
7. Verify readiness and authentication below. Preserve the backup and report any blocker honestly.

Changing only the password hash does not revoke existing stateless sessions when the signing secret is unchanged. Rotating that secret logs out existing sessions and needs explicit scope; do not silently broaden a password-only edit.

## Verification

- `/api/status` must answer HTTP 200 with `auth_required: true` and `basic` in `auth_providers`. This endpoint is public: a 200 is **not** proof of login.
- An unauthenticated `GET /api/auth/me` and one deliberately incorrect-password request should be rejected (normally HTTP 401). Avoid repeated failures: password login is rate-limited.
- Positive verification requires a genuine `POST /auth/password-login` using the authorized credential via a secure input path, followed by authenticated `GET /api/auth/me`. Check the expected username/provider without printing cookies or tokens.
- Confirm the dashboard is active and the messaging gateway PID/state did not change when it was outside the edit scope.
- A matching config hash, successful restart, and negative login test do not prove positive login. Report these checks separately.

## Secure-input limitations

For browser login: open the exact login origin, call `browser_vault_list`, then the relevant vault fill/save tool. Some messenger/headless sessions cannot display the masked prompt; a browser helper can also show the login page while the vault reports a different or blank origin. Retry navigation once, then respect `prompt_unavailable`.

Do not work around an unavailable vault by typing a chat password into the page, reading encrypted vault contents, minting an auth token from a signing secret, or weakening the gate. If an authorized precomputed hash has been applied and read back but secure positive login is unavailable, clearly state that the configuration was changed and the user's browser login remains to be confirmed. Never claim access was restored solely because a file write succeeded.
