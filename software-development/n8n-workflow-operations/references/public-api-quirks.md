# n8n public REST API — instance-level quirks

The public API v1 (`/api/v1`, header `X-N8N-API-KEY`) is not uniform across instances or versions. Some routes exist on one deployment and 404 on another with the same n8n version. Probe before concluding anything about credentials or ids.

## Endpoint capability differences

| Call | Symptom when unsupported | Working alternative |
|---|---|---|
| `GET /workflows?limit=N` | — | works widely; `limit` is accepted here |
| `GET /workflows/{id}/executions` | `404 {"message":"Version not found"}` | `GET /executions?limit=N&status=...`, filter `workflowId` client-side |
| `GET /executions?limit=N&status=error` | `400 {"message":"Unknown query parameter 'limit'"}` on some routes | drop the parameter, page with `nextCursor` |

Read the response body of a failure before interpreting it. `"Version not found"` names versions, not workflows — it is not a bad workflow id, and it is not an auth problem. An auth failure surfaces as `401`, not `404`.

## Modern publication and stored-credential checks

For n8n 2.41.5, `PUT /workflows/{id}?publishIfActive=true` saves and re-publishes an active workflow. A restart or deactivate/activate cycle is unnecessary; confirm the exact values under `activeVersion.nodes` and `activeVersionId == versionId`. Set `publishIfActive=false` only when intentionally saving a draft. Missing `workflow:activate` API scope or `workflow:publish` project permission can return 403 **after saving the draft**, leaving the old published version live, so always read both snapshots after an error.

`POST /workflows/{id}/publish` accepts a minimal `{versionId: "..."}` publication body; `/activate` is a deprecated alias. `POST /workflows/{id}/unpublish` replaces `/deactivate`. Before changing an instance of another version, inspect its schema instead of assuming these capabilities.

Create and update use different schemas: a `description` accepted by PUT is rejected by `POST /workflows` on this version. Start creation with `{name,nodes,connections,settings}`; add only fields the create schema supports.

`POST /credentials/{credentialId}/test` tests a stored credential without exposing its value (requires `credential:read`). Inspect the credential type's test request before using it: Telegram uses `getMe`, OpenRouter uses `/key`, both non-generating checks. A successful credential test proves authentication only, not delivery or model access.

For isolated model tests, clone only the AI Agent/model/output guard, keep the credential reference, supply a captured knowledge-base context and remove Telegram and production-memory nodes. Use a temporary webhook with `options.ipWhitelist: '127.0.0.1,::1'`; invoke it with a tiny `docker exec ... node` HTTP request to the container's own loopback. A host-to-container request can appear from a Docker gateway and receive 403 despite using host 127.0.0.1; do not remove the allowlist to make that pass. Allowlist only model IDs whose current catalog reports zero text pricing and text output. Read the answer, not just `garbageDetected=false`: mixed-language or confused technical answers can pass a simple Cyrillic guard. Unpublish and delete the temporary workflow, then verify GET returns 404; a first DELETE may return 409 while unpublication completes.

## Status values for `GET /executions`

`success`, `error`, `waiting`, `running`. `waiting`/`running` are the useful health signal: non-zero means work is stuck and needs attention, while a large `error` count against a healthy `success` stream is usually partial-failure by design (a "slot already taken" branch), not a broken chain. Report the ratio and the workflow split; do not call it a bug from the count alone.

Sampling caps at whatever `limit` allows — a `success` list of exactly the limit is a truncated page, not the total. Say "at least N".

## Inspecting an API key before using it

n8n public API keys are JWTs. Decode header and claims (no signature verification needed — you only want to read metadata):

```python
import base64, json, time
h, p, s = key.split('.')
d = lambda x: json.loads(base64.urlsafe_b64decode(x + '=' * (-len(x) % 4)))
print(d(h))                      # {'alg': 'HS256', 'typ': 'JWT'}
c = d(p); print(c)               # sub, iss='n8n', aud='public-api', iat, jti
print('exp' in c)                # False => non-expiring, manual revocation only
```

A key whose claims carry **no `exp`** never expires on its own. The only revocation path is deleting it in the instance UI (Settings → n8n API). Say that explicitly when storing such a key: the user needs to know a leak does not expire on its own.

Store the key in the credential vault, never in memory or a skill file — see the `service-credentials-vault` skill.