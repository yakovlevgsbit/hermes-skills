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

## Cloud provider key formats

### Yandex Cloud

Two distinct keys: **OAuth token** (for SDK) and **API key** (for REST). The API key is a simple string, no exchange needed.

```python
# REST — API key goes directly in the header
API_KEY = "AQVN..."  # from /root/.secrets/yandex-cloud.env
FOLDER_ID = "b1g..."   # folder_id from the cloud console
url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {"Authorization": f"Api-Key {API_KEY}", "Content-Type": "application/json"}
payload = {
    "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
    "completionOptions": {"temperature": 0.6, "maxTokens": 100},
    "messages": [{"role": "user", "text": "...", }],  # field is 'text', not 'content'
}
```

Image generation (YandexART) requires separate activation in the console — even with a valid key, returns 501 `unknown service` until activated.

```python
# YandexART (after activation)
payload = {
    "modelUri": f"art://{FOLDER_ID}/yandex-art/latest",
    "messages": [{"text": "...", "weight": 1}],
    "generationOptions": {"aspectRatio": {"widthRatio": 1, "heightRatio": 1}},
}
```

### GigaChat (Sber)

Two-step OAuth: exchange `Authorization Key` (Base64 `ClientID:ClientSecret`) for a short-lived access token, then call the API.

```python
import uuid, requests

AUTH_KEY = "MDFh..."  # Base64 encoded ClientID:ClientSecret
OAUTH_URL = "https://gigachat.devices.sberbank.ru/api/v2/oauth"
BASE_URL = "https://api.giga.chat/v1"

# Step 1: get access token (valid ~30 min)
headers = {
    "Authorization": f"Basic {AUTH_KEY}",
    "RqUID": str(uuid.uuid4()),  # REQUIRED — Sber WAF rejects without it
    "Content-Type": "application/x-www-form-urlencoded",
}
resp = requests.post(OAUTH_URL, headers=headers, data={"scope": "GIGACHAT_API_PERS"}, verify=False)
# verify=False needed — Sber uses self-signed cert chain
token = resp.json()["access_token"]

# Step 2: call API
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {"model": "GigaChat-2-Max", "messages": [{"role": "user", "text": "..."}]}
requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
```

**Pitfall:** Sber's WAF (SynGX) may return 403 even with correct headers — this is IP-based filtering, not a bad key. The OAuth host `gigachat.devices.sberbank.ru` is distinct from the API host `api.giga.chat`.

## Rotation and revocation

Deleting a file does not revoke anything. To rotate: write the new value alongside, verify a live request, remove the old, update the README checklist. For cloud service accounts, revocation happens in the provider console; the local file is only a copy.

## Cross-references

- Which credentials exist and their consumers: also summarized in MEMORY.md (paths only).
- Credential *values* used inside an n8n workflow stay in n8n and are unreachable by design; see the n8n skills for how to reference them.
- Message-platform auth quirks (raw token, no `Bearer` prefix) live in the platform's own API skill.