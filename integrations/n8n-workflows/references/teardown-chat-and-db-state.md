# Tearing down state a bot wrote: DB rows, chat messages, pin

A "clean everything up" request spans three stores that fail independently, and
the DB is the easy one. Build the inventory first, delete in dependency order,
and read every result back.

## 1. Inventory before deleting anything

**DB rows:** one `SELECT` with all columns you will filter on, dumped to disk.
Print the count and the per-row summary (id, date, status, owner) so the user can
see exactly what is about to go. Then `DELETE` with `Prefer: return=representation`
and assert the returned row count equals what you listed — a filter that silently
matches nothing returns an empty 200.

**Chat messages:** you usually CANNOT list chat history with the credentials on
hand. Reconstruct the set from the platform's own execution records instead —
every messaging node's execution output is a transport envelope carrying the
remote `mid`:

```python
for f in execution_files:
    runData = (d.get("data") or {}).get("resultData", {}).get("runData", {})
    for node, runs in runData.items():
        for out in runs[0].get("data", {}).get("main", [[]])[0] or []:
            body = (out.get("json") or {}).get("body") or {}
            if body.get("mid"):
                collect(body["mid"], node, chat_id, text)
```

Sweep the full retained window (`limit=250`), not just the newest executions —
the oldest orphan usually predates the newest fix. Deduplicate by `mid`. Two
node classes matter: the state-publishing node (posts that will need unpinning)
and per-recipient notifications (confirmations, error messages, DMs). Print the
final list grouped by chat so the user approves a concrete inventory.

## 2. Unpin BEFORE deleting the post it points at

The pinned message id lives in chat state, not in anything you are about to
delete, but the pinned post is often the same `mid` in your delete list. Order
matters for verifiability: read the current pin (`GET /chats/<id>/pin`), unpin
it, confirm it is empty (`{}`), and only then delete messages. Reversed, you
cannot tell "the unpin failed" from "the post vanished first".

Unpinning also fixes a state bug on its own: a pin left pointing at a post whose
DB rows were just deleted advertises slots that no longer exist.

## 3. The platform token is a hard dependency, and the one you remember may be dead

If the bot's platform credential lives only inside the workflow's encrypted
HTTP-auth credential, the REST API cannot surface it — `/credentials` returns
only `id`, `name`, `type`. A token in your notes can also be stale after a
rotation, and the two failures look different and both matter:

- `401 {"code":"verify.token","message":"Invalid access_token"}` — rotated; the
  value is wrong.
- `401 {"code":"verify.token","message":"Malformed access token"}` — a `Bearer `
  prefix was added; some platform APIs want the RAW token.

So try the remembered token once, and if it 401s, ask the user for a working one
and state which chat/message ids are waiting on it. Do not start deleting with
an unverified token, and do not promise the cleanup before it succeeds. Probing
a cheap authenticated GET first (`GET /chats/<id>/pin`) tells you in one call
whether the token works.

Also check `POST /workflows/<id>/run` before planning to make the instance act
on your behalf — some deployments reject it, so a throwaway webhook workflow may
be the only way to exercise an instance-held credential.

## 4. Verify with a read-back per item, not with the delete status codes

Every delete returning 200 is the API accepting the request, not proof the
message is gone. After the batch, GET each id and count the ones that still
return 200:

```python
alive = [m for m in mids if http_get(f"/messages/{m}") == 200]
assert not alive, alive
```

Report the verified counts ("12 of 12 confirmed gone", "8 rows deleted, table
now empty") rather than the number of successful responses. Then state the
resulting system state plainly: with the DB empty and the pin cleared, the bot
has nothing to serve until the user publishes slots again — a client message now
correctly produces "no slots available" rather than silently failing.

## 5. Leave the workflows running

Teardown is about accumulated data, not about the automation. Verify afterwards
that both workflows are still `active` with a bumped `versionCounter` and recent
`success` executions; a bot left deactivated is a second incident the user did
not ask for.