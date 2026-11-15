# API Credential Onboarding

When the user provides API keys/tokens for external services, store them securely
and verify them with a real API call before reporting they work.

## Storage Pattern

```bash
# Store in /root/.secrets/<service>.env with restricted permissions
SERVICE_API_KEY=<value>
chmod 600 /root/.secrets/<service>.env
```

Never paste the key back in chat or log output. Only show the first/last few
characters for confirmation.

## Verification Steps

1. **Read the key from the secrets file** (don't retype from the chat message)
2. **Make one real API call** to verify the key is alive
3. **Report what the key CAN do** — not just "it works" but actual permissions/scopes
4. **Report what it CANNOT do** — missing scopes, empty account, etc.

## Common Provider Quirks

- **Vercel**: token can be `limited` (only `/v2/user`) or full access. Check
  `limited` field in the response. Empty projects may mean the token scope
  doesn't cover them, or the account is genuinely empty.

- **Upload-Post**: key + profile name (usually `default`). Verify by calling
  `/uploadposts/users/<profile>` to see connected social accounts and quota.
  Key is `Authorization: Apikey <key>` header.

- **Kling AI**: `Authorization: Bearer <key>`, domain is
  `api-singapore.klingai.com` (not `api.klingai.com`). API returns 429 with
  `"Account balance not enough"` when the key is valid but unfunded —
  distinguish this from 401 (bad key).

- **Sim AI**: `X-API-Key: <key>`, domain is `api.sim.ai`. May return 404
  with a Vercel deployment error — the real host may be `app.sim.ai`.

## What to Report

- Service name and key location (path only, not value)
- What the key can actually do (verified via API call)
- What it cannot do (missing scopes, empty account, insufficient balance)
- Next steps if action is needed (fund balance, expand scope, create project)