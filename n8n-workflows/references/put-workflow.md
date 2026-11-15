# Applying a change to a live workflow (PUT recipe)

Minimal, verified sequence. Every rule here came from a request that failed;
the mechanism is in parentheses.

## 1. Back up the live workflow first

```
GET /api/v1/workflows/<id>   ->   /root/n8n-backups/<stamp>-<label>-v<N>.json
```

Note `versionCounter` in the filename. This backup is also your diff baseline:
after the PUT, re-fetch and compare the specific `parameters` blob you intended
to change, so you can prove which version shipped.

## 2. Build a minimal PUT body

Keep exactly: `name`, `description`, `nodes`, `connections`, `nodeGroups`,
`settings`.

- Coerce `None` to `""` for `description` (and `name` if null) — the API
  validates every string field and answers
  `400 request/body/description Expected string, received null`.
- Drop read-only keys, or you risk overwriting instance state with a stale
  copy: `id`, `active`, `versionId`, `versionCounter`, `activeVersionId`,
  `activeVersion`, `createdAt`, `updatedAt`, `triggerCount`, `shared`, `tags`,
  `meta`, `isArchived`, `pinData`, `staticData`, `sourceWorkflowId`.

Never send `staticData`: the trigger `marker` and any static-data array the
user relies on (e.g. a dedupe store) live on the instance. A PUT that includes
your last-read copy resets them.

## 3. Simulate every Code node you touched

Compile with `new Function('$input','$','\$getWorkflowStaticData','console', src)`
— see the SKILL.md simulation section for the wrapper trap. Only inject
builtins n8n really provides; an invented shim makes the sandbox pass while the
instance throws on every event.

Feed the simulation the node's REAL input shape from `runData`, not a convenient
one. A node wired after a send/notification node receives that node's request
ENVELOPE (`body`, `sender`, `timestamp`), which carries none of the domain fields
the code indexes on — the code then finds nothing, returns `[]`, and the branch
ends silently several nodes later. This is why a reminder stage can look wired and
correct while never producing a single item.

## 4. Deleting nodes: prune `connections` keys, not just targets

A connection entry is keyed by its SOURCE node, so deleting a node leaves its
entry behind and the API rejects the write with `unknown_connection_source`. The
emptiness filter is easy to get wrong in a way that hides the bug:

```python
# [[]] is truthy -> the entry survives -> 400
if any(o for o in (v.get("main") or []))
# correct: does the entry name any target at all?
if any(x for o in (v.get("main") or []) for x in (o or []))
```

Rebuild the dict from `wf["connections"]` and assign it BACK to
`wf["connections"]` — mutating a local alias and saving `wf` keeps the old dict
intact and silently ships the broken payload. Then assert before the PUT: no
`connections` key outside `nodes`, no target outside `nodes`, and no removed
node's name left in any node's `parameters`.

## 5. PUT, then verify the write landed

```
PUT /api/v1/workflows/<id>     # 200 + full body + bumped versionCounter
GET /api/v1/workflows/<id>     # assert the exact field you changed
```

Assert on the value, not the status: check the `jsonBody` string or the code
substring you edited. A 200 from a mis-keyed or stale body is indistinguishable
from a real fix.

## 5. Do not restart by reflex

`active` survives the PUT and polling keeps ticking; a deactivate/activate cycle
is unnecessary and resets the trigger marker. Just re-list executions.

## 6. Verification is a non-empty poll, not a green status

Group the newest executions by trigger output length. All-success runs with zero
poll items mean only that the trigger still ticks. The fix is proven when an
execution with a real inbound message ran through the edited node and produced
downstream output.

Then state explicitly: the message that exposed the bug errored before the fix
and will never replay, so the user has to re-send it. Do not let "0 errors in
the last hour" stand in for "the bug is fixed".