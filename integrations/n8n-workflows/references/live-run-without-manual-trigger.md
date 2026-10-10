# Driving a live execution from the public API

Validated path for actually exercising a workflow when the user asks for a live
run. Read-only inspection is the default posture; a live run writes to whatever
the workflow writes to (DB rows, chat messages, pins), so confirm scope with the
user before firing one at a production instance.

## Manual trigger endpoints do not exist

`POST /api/v1/workflows/<id>/run` returns **405 "POST method not allowed"** on
current n8n, and `GET /api/v1/executions/current` 400s demanding a positive
integer executionId. Do not burn turns rediscovering this. The working method is
a throwaway webhook-triggered copy.

## Build the test copy

1. `GET /api/v1/workflows/<id>` — take `nodes` and `connections` verbatim so
   credentials ride along by reference (never re-create credential ids).
2. Deep-copy nodes; drop the original trigger node and any dedupe node that
   reads execution history (`removeItemsSeenInPreviousExecutions`) — it is
   keyed to the real workflow's history and will drop everything.
3. Prune the dropped node from `connections` on both sides: remove its key as a
   source AND filter it out of every remaining source's `main` arrays.
4. Insert a webhook node (`n8n-nodes-base.webhook`, typeVersion 2) with
   `httpMethod: POST` and a unique `path`, and point the original first real
   node at it.
5. `POST /api/v1/workflows` with the copy, then `POST /api/v1/workflows/<newId>/activate`.
   A 200 with `"active": true` is the gate — a created-but-inactive workflow
   still answers the webhook path with a workflow-not-found style failure.
6. Fire a real POST to `<base>/webhook/<path>` with a realistic payload and a
   **fresh `timestamp` in ms** — most such chains have an age guard that silently
   drops stale input.

## Trigger payloads are NOT shaped like live payloads

A webhook node emits `{headers, params, query, body, webhookUrl, executionMode}`.
Chat/poll triggers from these bot nodes emit the event at the **top level**
(`item.json.message.*`). Downstream Code reading `item.json.message.body.mid`
sees `undefined` under a webhook and the first real node returns zero items — and
because zero items is a legal result, the execution still reports `success`.

Add a normalize node as the FIRST consumer in the test copy:

```js
const j = $json;
const event = (j.body && j.body.message) ? j.body : j;
return [{ json: event }];
```

Symptom to recognize: every run is `success`, `lastNodeExecuted` is the first
Code node, and its `main` is `[[]]`. That is a payload-shape mismatch, not a
broken dedupe — do not debug the dedupe logic until the normalize node is in.

## PUT body: strip read-only fields

`PUT /api/v1/workflows/<id>` rejects the whole body if it carries read-only
keys, one at a time: `id`, `active`, `meta`, and `versionId`/`activeVersionId`/
`versionCounter` will all 400 with `"request/body/<field> is read-only"`.
Build the update as exactly three keys:

```python
body = {"name": w["name"], "nodes": w["nodes"],
        "connections": w["connections"], "settings": w["settings"]}
```

A workflow's `active` flag is set only through `/activate` and `/deactivate`.
Editing nodes does not re-deploy them; if a fix does not take effect, do a
`deactivate` -> `activate` cycle to republish the active version.

## Read the newest execution from the GLOBAL list

`/api/v1/executions?workflowId=<id>` can return a stale page — a freshly
triggered run was missing from the workflowId-filtered list while present in
`/api/v1/executions?limit=N`. When a webhook returned "Workflow was started"
but nothing new shows up, re-read the unfiltered list, keep the max `id` for
that workflowId, and fetch that one. Never conclude a run did not happen.

Per-node truth comes from `/api/v1/executions/<id>?includeData=true` ->
`data.resultData.runData`: print each node name, `executionStatus`, and the
first ~400 chars of `main`. The tail of the chain carries the interesting
evidence — the actual composed outbound message, the API response body, and the
row the DB node wrote (its `id` is what you clean up by).

## Clean up after yourself

Delete the rows you created (capture the inserted `id` from the run data and
filter a Supabase `delete` node on it), then verify with a `getAll` read node in
the same execution — do not assume the delete landed. Deactivate before DELETE or
the API 409s with "Workflow is still being unpublished"; retry once after a few
seconds. Then confirm the instance is back to its original workflow list.

Say explicitly what you could NOT undo. A message already posted to a chat and
pinned is only retractable with the bot token, which n8n will not hand back
through the API (credential secrets are never returned). Leave production rows
you did not create alone — identify them by timestamp and report them instead.