# Vault layout and per-service loading recipes

`/root/.secrets/` — dir `700`, files `600`. Established when the user asked where to keep service API keys so new projects could self-serve.

## File naming

Plain `KEY=VALUE` lines in `.env` files (no `export`, no quotes). JSON key files keep their provider's native name (`google.json`). One file per service so rotation touches exactly one file.

| File | Contents |
|---|---|
| `google.json` | service-account JWT private key (Google) |
| `n8n.env` | `X-N8N-API-KEY` |
| `supabase.env` | `SUPABASE_URL`, `SUPABASE_KEY` |
| `openrouter.env` | `OPENROUTER_API_KEY` |
| `tokens.env` | messaging bot tokens |
| `README.md` | inventory, rules, load recipes, verification checklist |

## Loading patterns

Env-style file:
```bash
set -a; . /root/.secrets/supabase.env; set +a
curl -s "$SUPABASE_URL/rest/v1/rows?select=*" -H "apikey: $SUPABASE_KEY"
```

JSON key file — pass the path, never inline the content:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/root/.secrets/google.json
```

Google service account in Python — use the library, and send the Bearer header yourself:
```python
from google.oauth2 import service_account
import google.auth.transport.requests as tr, urllib.request
creds = service_account.Credentials.from_service_account_file(
    '/root/.secrets/google.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
creds.refresh(tr.Request())
req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + creds.token})
```
A hand-rolled `jwt.encode` needs the `iss`/`scope`/`aud`/`exp`/`iat` claims set consistently; the library is immune to that class of mistake. Refreshing per write batch, not per session, avoids mid-task 401s.

Manual signing (`openssl dgst -sign`) writes the base64 key and signature into the working directory. Put them in a scratch dir and `shred -u` immediately — never inside the vault.

## Rotation and revocation

Deleting a file does not revoke anything. To rotate: write the new value alongside, verify a live request, remove the old, update the README checklist. For cloud service accounts, revocation happens in the provider console; the local file is only a copy.

## Cross-references

- Which credentials exist and their consumers: also summarized in MEMORY.md (paths only).
- Credential *values* used inside an n8n workflow stay in n8n and are unreachable by design; see the n8n skills for how to reference them.
- Message-platform auth quirks (raw token, no `Bearer` prefix) live in the platform's own API skill.