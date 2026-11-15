# Credentials and inbound auth: keep the token out of the graph, keep one auth contract

Two failure modes, both of which deploy clean and fail only on the first real
event.

## A secret in a node body leaks into every backup

Putting a token or shared secret directly in an HTTP node's `jsonBody` puts it
in plaintext in the workflow JSON, and every `GET /workflows/{id}` backup you
take from then on. The credential store exists for exactly this.

```
POST /api/v1/credentials
{"name":"<app> bearer","type":"httpHeaderAuth",
 "data":{"name":"Authorization","value":"Bearer <token>"}}
```

Bind it on the node instead:

```json
"authentication": "genericCredentialType",
"genericAuthType": "httpHeaderAuth",
"credentials": {"httpHeaderAuth": {"id": "<cred id>", "name": "<app> bearer"}}
```

`httpHeaderAuth` is the general case: any header, any scheme. Use it for a
bearer token to your own panel instead of a custom `genericAuthType`.

Rule: after wiring a credential, assert the string `"secret"` (or the token
value) appears zero times in the re-fetched workflow JSON. Backups are written
by convention and long outlive the session that created them.

## Specify credential in jsonBody only if the receiving service needs it there

A body-borne `secret` and a header-borne bearer are two different contracts. A
hook that validates one will 401 the other forever, and the graph looks perfect
while every execution fails at the HTTP node.

Before adding the new call, read the receiving handler and write down the exact
contract: which header, which body field, is either sufficient or are both
required. Then make the handler accept **both** where two callers legitimately
differ, and reject when neither matches.

## Fire the exact request the node will send

Inspecting the node's parameters proves nothing about the auth. Send the node's
own request shape — same header, same body, same query — and read the status.

```
200  credential accepted
401  auth contract mismatch — check the handler's expected field, not the node
400  accepted, but the payload shape is wrong (missing required field)
```

A 401 after adding a node is almost always the handler and the node disagreeing
about *where* the credential travels, not a wrong token value. Read the
handler's comparison before regenerating any secret.

## A 401 can be your test harness using the wrong credential file

When several secrets live in separate files, a generic name in a helper will
silently pick the wrong one, and the resulting 401 reads like a product bug. Name
test variables after their source (`max_token`, `app_token`, `n8n_key`), never
after their role, and print the length and a short prefix of the credential you
actually sent before concluding anything about the service.

Triage order for a 401: (1) which file did the value come from, (2) which
service issues that kind of token, (3) is the header name right. Do not rotate or
regenerate a token until (1) and (2) are settled — a regenerated token in the
wrong call site invalidates a working setup.
