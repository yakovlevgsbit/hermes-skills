---
name: n8n-workflow-operations
description: "Use when operating n8n workflows over the REST API."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [n8n, workflow-automation, api, testing, debugging]
---

# n8n Workflow Operations

## When to Use

Use when a user hands you an n8n instance URL plus an API key and asks to inspect, explain, test, debug, or extend a workflow — including phrasings like «посмотри ноду», «почему не работает», «проверь живым прогоном», «почини». Also use for the cleanup pass that follows a live test, and for the chat-platform APIs those workflows call (see `references/max-messenger-api.md`).

Operate someone else's n8n instance through the public REST API: audit a workflow's logic, prove it works with a real execution, and leave the instance exactly as you found it. The instance is usually **someone else's production** — bots posting to live chats, rows in a live database.

## Setup

Ask for (or read from env) the base URL including the n8n path prefix (`https://host/n8n`) and an API key. All calls:

```bash
curl -s -H "X-N8N-API-KEY: $KEY" "$BASE/api/v1/workflows?limit=100"
```

Use `execute_code` with `urllib` when you need to filter/aggregate across many responses — it keeps large JSON out of context.

## Procedure

### 0. Gate: should this be automated at all

A workflow that saves ten minutes a week and pages you at 3am is a net loss.
Answer these eight in writing before building or extending one — the answers go
in the report, not in your head. Reasoning, failure examples and the three
verdicts: `references/automation-gate.md`.

1. **Value vs fragility** — what breaks if this dies silently for a day?
2. **Owner and failure path** — who is told, through which channel, and what
   happens meanwhile? No error branch means "it silently stops".
3. **What stays human** — name which steps need a person (delete, send to a
   client, change prices, publish); an approval node goes in the graph.
4. **Idempotency** — a replay must not post or insert twice; key on a stable id.
5. **Uncapped spend** — every loop, retry and paid call gets a cap and a timeout.
6. **Secrets** — credential store only; a pasted key lands in every backup.
7. **Rollback** — graph in `/root/n8n-backups/`, plus one line on how to disable it.
8. **Boundaries** — one line on what this deliberately does NOT do.

A live production graph is changed only after an explicit yes, with the diff
shown. No "done" on a write you cannot read back.

### 1. Audit before running anything

```
GET /api/v1/workflows?limit=100        → inventory: name, active, node count
GET /api/v1/workflows/{id}             → full graph
```

Print the node list (name, type, typeVersion) and the connection edges from `connections[src].main[0][].node` — the edge list is where data bugs hide. Then dump every `code` node's `jsCode`, every `agent` node's system prompt, and every Supabase/HTTP node's `filters`/`jsonBody`. Read-only, zero risk, and it is where 90% of real bugs are.

Read the trigger node first to learn the **real input shape**. Workflow code that reads `item.json.foo` tells you what the trigger actually emits.

**Google Sheets nodes: documentId is nested, not flat.** A Sheets node's `parameters.documentId` is an object like `{"__rl": true, "value": "1A4WI4k...", "mode": "list", "cachedResultName": "meat", "cachedResultUrl": "https://docs.google.com/..."}`. The actual spreadsheet ID is in `.value`. The sheet name is similarly wrapped: `parameters.sheetName.value`. To extract all Sheets nodes, recurse into the node JSON looking for `documentId` keys — a shallow `parameters.documentId` lookup misses nodes where the ID is stored deeper (e.g. in `filters` or `jsonBody`).

### 1c. Supabase DDL: REST API does not support CREATE TABLE

The Supabase REST API (`/rest/v1/`) only handles CRUD on existing tables. It does **not** support DDL (`CREATE TABLE`, `ALTER TABLE`). To create tables:

1. **psql** — connect directly with `psql "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"` (requires DB password in secrets or env)
2. **Supabase Dashboard** — go to SQL Editor and paste the script
3. **Supabase CLI** — `supabase link --project-ref <ref>` then `supabase db push` (requires `SUPABASE_ACCESS_TOKEN` from `supabase login`)

The `service_role` key works for REST CRUD but cannot create tables. If you have the service key but not the DB password, ask the user for the password or use the Dashboard.

### 2. Judge "active" claims honestly

A workflow showing 200 consecutive `success` executions proves nothing. Pull `GET /api/v1/executions?workflowId={id}&includeData=true` for a few and check `runData` keys: if every execution lists only the trigger node with an empty `main` array, the chain has never actually run end-to-end. Say that plainly instead of reporting "all green".

### 3. Run a live test without touching production

There is **no manual-run endpoint** — `POST /api/v1/workflows/{id}/run` returns 405. The working approach is a throwaway webhook-triggered copy:

1. `POST /api/v1/workflows` with a copy of the real graph, **trigger node swapped for `n8n-nodes-base.webhook`** and a unique path; keep all other nodes, names, and credential bindings identical so the copy exercises real code paths.
2. `POST /api/v1/workflows/{id}/activate` — webhooks only respond while active.
3. `POST {BASE}/webhook/{path}` with a realistic payload (fresh `timestamp`, plausible `sender_id`, real `mid`).
4. Poll `GET /api/v1/executions/{id}?includeData=true`, walk `data.resultData.runData`, and print per-node `executionStatus` + output. This is the only way to see what each node actually emitted.
5. `POST /api/v1/workflows/{id}/deactivate` then `DELETE /api/v1/workflows/{id}`.

### 3b. Cloning a workflow into a new one (POST, not PUT)

Cloning is the right move when you want a second entry point onto the same logic — typically a webhook-driven variant an external panel drives instead of a chat trigger. `POST /api/v1/workflows` validates a different shape than `PUT` does, and the three rejections below are creation-specific, so they will not appear on the edit path:

- **`connections` values must be objects, not arrays.** Each source maps to `{"main": [[{"node": ..., "type": "main", "index": 0}, ...]]}`. Hand-building `{"src": [ ... ]}` fails with `Workflow structure is invalid. connections.<src> (invalid_type): Expected object, received array`.
- **Node ids must be unique across the payload**, including among nodes copied verbatim from the source. A clone that reuses the source's custom ids dies on `duplicate_node_id: Nodes "A" and "B" share the node ID "..."`. Mint fresh UUIDs for every node in a POST.
- **A renamed node silently breaks every `$('Old name')` reference in the payload you copied.** A clone that renames the node the logic depends on ships fine and fails on the first inbound event as `ExpressionError: Referenced node doesn't exist`. Rewrite the references inside `parameters` — filter `keyValue`s, `url`, `text`, `jsonBody` — not just the node's `name`, then assert the old name appears zero times in the assembled body.

After a successful POST, `PUT` the rest of the fixes. The create call accepts the graph as given, so any correction has to be an explicit follow-up write, and the id from the POST response is the only handle you have on the clone.

Credential bindings copy across as references (id + name) — that is what makes the clone exercise real code paths, and also means the clone can mutate shared external state. Say so before activating it.

### 4. Publish edits

Back up the full live workflow before the first PUT (`GET /workflows/{id}` into `/root/n8n-backups/`). Publishing is version-dependent: on n8n 2.41.5, use `PUT /workflows/{id}?publishIfActive=true` and verify both the draft and `activeVersion.nodes` by GET; do not deactivate first. A 403 can save a draft without publishing. Modern publish/unpublish endpoints, create-schema differences, and non-secret credential tests are in `references/public-api-quirks.md`.

**A failed PUT must never leave the workflow deactivated.** If the PUT or the activate fails after the deactivate, re-activate the *fetched* workflow before reporting — otherwise a run that looked like a one-line fix leaves the production trigger off. `POST /activate` with the live workflow body restores it. On a scripted deploy, wrap deactivate→PUT→activate in a try/except that re-activates on any exception.

**`description: null` is rejected on both PUT and activate.** n8n returns `request/body/description Expected string, received null` for a workflow whose description is null. Send `"description": ""` instead — normalise nulls to empty strings in the body you PUT or activate.

**`settings` accepts only known keys.** An unrecognised key fails the whole PUT with `request/body/settings Unrecognized key(s) in object: '<key>'`, one per attempt, so the payload never lands and you discover keys by trial. Probe a candidate setting in an isolated PUT before putting it in the deploy body. Keys seen accepted: `executionOrder`, `binaryMode`, `timezone`, `saveManualExecutions`, `callerPolicy`.

**Some settings cannot be unset, only overwritten.** `timezone` ignores a PUT that omits it and rejects `null` with `400`; the only way to clear it is `"timezone": ""`. When you add a setting to a workflow, verify it can be removed — otherwise you have introduced a permanent divergence between the live graph and any local copy that predates it.

**Activating a new workflow: POST to `/activate`, not PATCH/PUT.** `PATCH /api/v1/workflows/{id}` returns `405 Method Not Allowed`. The correct path is `POST /api/v1/workflows/{id}/activate` with the full workflow JSON in the body (including all node credentials). If activation fails with "Missing required credential: X", the credential binding is missing from the node JSON — include `"credentials": {"supabaseApi": {"id": "...", "name": "..."}}` inside each node that needs it, then retry.

**Show the diff and wait for a yes before any write that is not a bug fix.** This user approves a fix immediately but wants a preview before a bulk data rewrite — and asking "apply or show diff?" pushes the decision onto them when the answer is nearly always "show diff". Show the plan as part of doing the work instead: scope, exact rows, before/after text, and what is lost, then ask. Never bundle "I will also do X" into a question about a fix.

**Verify the wiring and Code semantics before declaring a fix done.** `references/editing-node-wiring.md` covers the class of bugs that deploy clean and return `success`: wiring a downstream node to an output index the upstream never emits (it silently never runs), fan-out re-invoking a read node once per input (duplicated rows downstream), LangChain sub-nodes requiring `ai_languageModel` rather than `main`, `runOnceForAllItems` making `$json` only the first item, and the two coherent timezone conventions plus which mixup offsets every displayed time. Run `scripts/test_code_node.js` under `node` to exercise a Code node offline — faster than a live run and it isolates logic from the platform.

### 5. Clean up every artifact, and prove it

Enumerate what the test wrote *before* running it, then remove each one and read back. Test artifacts typically include: rows inserted into the live DB, messages posted to a chat, and pinned messages. Deleting the temp workflow is not cleanup — it is the smaller half.

When cleanup touches the DB the workflows write to, prefer querying the store directly over inferring from execution logs. n8n credentials are opaque through the API, so ask the user for a service key **and** the project ref / base URL — the key alone cannot form a request (`https://<ref>.supabase.co/rest/v1/<table>`). With both, assert cleanup by read-back: `SELECT` the affected rows before and after, and confirm the fields you reset are actually null rather than trusting the `success` status.

## Deploying a graph from a local source of truth

When a change is authored as a file and pushed to the instance, keep the file the
single source of truth and make the run **read-only by default**: print the diff
and the cost, and require an explicit flag before any write. A deploy that writes
on a bare invocation destroys the only safe way to review it.

**Diff the graphs on an allowlisted projection**, never on the raw objects: the
read-only fields (`id`, `active`, `versionId`, `activeVersionId`,
`versionCounter`, `meta`, `tags`, `createdAt`, `updatedAt`) are on every fetch and
always differ from a hand-authored file. Compare raw objects and every run
reports "changed" (or you stop believing the diff). The same field list is the
one the API rejects on write — see the first Pitfall below.

**Count what was DETECTED, not what was applied.** A summary line of
"N changed, M applied" reads as a pass when the run was a dry run and M is
always 0. Report the detected count separately from the applied count.

**Rebuild the PUT from a just-fetched live copy** and send the allowlist
`{name, nodes, connections, settings, staticData}`. A PUT replaces the whole
graph, so a payload composed from an older backup silently reverts every fix
made since.

## Pitfalls

- **PUT bodies must be minimal.** The API rejects read-only fields with `400 request/body/{id,active,meta,versionId,activeVersionId,versionCounter,createdAt,tags} is read-only`, one at a time. Send only `{name, nodes, connections, settings, staticData}`, and strip read-only keys by allowlist rather than by iterating the blacklist — it is the same list you strip when diffing a graph.
- **DELETE right after deactivate returns 409** ("still being unpublished"). Wait ~3–5s and retry once; do not loop.
- **`?workflowId=` on the executions list can return a stale page, especially immediately after firing.** After a webhook POST, list `GET /api/v1/executions?limit=10` and filter client-side by `workflowId`, otherwise you re-read the previous run and conclude the new one "didn't happen".
- **Webhook nodes wrap the payload**: output is `{headers, params, query, body, webhookUrl}`. The real trigger puts fields at the top level. Insert a normalization Code node in the *test copy* (`const event = (j.body && j.body.message) ? j.body : j;`) — never "fix" the production code to match your test harness.
- **Credentials are opaque through the API.** `GET /credentials` lists id/name/type only; secrets are never retrievable. If a live-run node needs a secret you can't read, ask the user for the token rather than trying to extract it.
- **Side effects outlive the execution you were watching.** If a node returns 0 items on one run, that does not mean nothing happened — earlier runs may have posted and pinned. Before reporting on chat/DB state, query the live state directly (`GET /messages/{mid}`, `GET /chats/{id}/pin`) instead of inferring from execution logs.
- **A test run against production publishes real content.** Ask the user up front whether the test may post to the live channel, and ask what to do with the result. Do not run it and decide afterwards.
- **A node returning 0 items is evidence about your harness first.** Before blaming production code for a silent no-op, confirm your injected payload matches the shape the workflow's own trigger emits.
- **When cloning a graph, copy every edge type, not just `main`.** AI Agent model/tool/memory links use `ai_languageModel` / `ai_tool` / `ai_memory`; a copy that keeps only `main` edges fails with `A Chat Model sub-node must be connected and enabled`. See `references/editing-node-wiring.md`.
- **The per-workflow executions endpoint can be absent entirely.** On some instances `GET /workflows/{id}/executions` answers `404 Version not found` even though the workflow exists — the error names versions, not workflows, so it reads like a bad id. Fall back to `GET /executions?limit=N&status=error|success` and filter by `workflowId` client-side. Query-parameter support also varies per endpoint: a `limit` accepted on one route returns `400 Unknown query parameter` on another. Probe the endpoint, do not assume the documented shape.
- **A `404`/`400` from n8n is not evidence about your key or your workflow id.** Distinguish transport-level rejection from auth failure before reporting either. See `references/public-api-quirks.md`.
- **A `400` whose message echoes your template back (`Invalid message_id: {{ $json.x }}`) means the expression never resolved**, not that the field name is wrong. Fix the leading `=` on `jsonBody`; see `references/expression-resolution-and-payload-integrity.md`.
- **Fetch large workflow JSON to a file before editing it.** A truncating tool splices its own marker inside a `jsCode` string, the JSON still parses, and the corrupted code reaches the instance on the next PUT.
- **A hand-rolled parser drops every record after the first malformed one, silently.** Any `"` opens a quote, so one stray quote inside a field stops comma/newline splitting and returns one mega-row. Print a column-count histogram after every parse — one row with hundreds of columns means the rest is gone. Rule to implement: a quote is special only when the field is still empty. See `references/external-data-parsing.md`.
- **Count against the source API, never against the pipeline's own yield.** A retriever's output is not evidence about its input: a broken parse made a 712-row base look like 175 and produced advice ("diagnostics are absent") that was factually wrong. When advising on coverage or quality, count via the authoritative read path first.
- **Re-derive a plan's volume from the authoritative count before quoting it.** A cleanup scoped to "6 rows" became 69 the moment the parser was fixed — 63 of them in the never-visible half. Scope every bulk-rewrite (delete these rows, rewrite these fields) from the source API, not from a sample that a broken pipeline produced, and re-state the count when it changes materially.
- **Split a mixed-content rewrite by whether the shared part has its own values.** When one row carries figures for two models, editing the question alone silently republishes the other model's numbers. Group the affected rows into: rows where the retained model has its own figures (rewrite the answer), and rows where the answer is already common (topic and question only). Print both groups and say which loses information.
- **Ask which boundary a model-name qualifier denotes before treating those rows as deletable.** `S-MX до 09.1999` reads like a split between two models and is actually a model-year split inside one; guessing wrong deletes or rewrites 63 rows on a wrong premise. One question resolves it.
- **Verify a fetch-then-parse fix against two oracles.** Run the new parser offline on the real payload, against an authoritative RFC-4180 reader (Python `csv.reader`), and against the live API read path. Drop the header consistently on both sides or the diff misaligns by one row. Then extract the function from the workflow **after** the PUT and run that, so a PUT that did not land cannot read as verified.
- **Renumbering a user-facing list is not a fix until the lookup node uses the same scheme.** Simulate the printed ordinal through the real lookup code offline and assert the ids match.
- **Two nodes can implement the same numbering rule and still disagree** — the ordinals come from the SELECT row set, and if the lookup node's WHERE clause is wider than the renderer's, one stale row shifts every printed number by one and the client books the wrong slot. Diff the filter sets of every node touching the table, widen the narrow pool (never shrink the visible one), and reproduce the poison row before calling it fixed. See `references/expression-resolution-and-payload-integrity.md`.
- **A credential pasted into a node body lands in plaintext in every backup.** Use `httpHeaderAuth` from the credential store, then assert the secret appears zero times in the re-fetched workflow JSON.
- **A 401 on a newly wired node is an auth-contract mismatch, not a wrong token.** Read the receiving handler to learn whether the credential travels in a header or the body; regenerate nothing until you know which file the value you sent came from.
- **Date formatters that differ between two nodes produce contradictory output** (`10.25.2026` in a post vs `25.10.2026` in a confirmation). Diff the renderers, don't eyeball one.
- **A format bug hides until the first value that distinguishes it.** Month/day order is indistinguishable while every day is ≤12; testing on `04.10` passes and shipping `10.25` for the 25th. Probe a formatter with values where swapping the fields changes the string — two-digit day plus a day above 12.
- **Verify a bulk write against the reader that will actually run, not just the writer's success.** After rewriting a whole table, confirm the count through the exact path the pipeline uses; a mismatched payload shape or an untrimmed tail can leave the sheet correct to the API and wrong to the consumer.
- **Never build a retrieval test set out of the base's own question column.** A probe cut from the row it must retrieve is a near-verbatim copy, so any retriever scores 95–98% and every comparison reads as a win. Take probes from the topic column or from outside the corpus; if no external question set exists, say the measurement is unavailable.
- **Check how many records share the top score before tuning weights.** When the correct rows sit at positions 2–3 tied with the wrong one, the discriminating feature is absent from the query and there is nothing to weight — that is a base-content or embeddings problem, and shipping a weight change only decides which of several wrong answers wins.
- **Resolve every row a bulk edit touches by content, never by a remembered id.** Ids drift; verify the landed row's topic and answer share content words with the intended edit, and do it before assembling the write payload.

## Reporting

Report what the live run *proved*, then what it exposed, then what remains. Name concrete values (row ids, message ids, the actual text that landed in the chat) — those are checkable. If you revise an earlier claim mid-session, say so explicitly and correct it; a wrong claim left standing is worse than the original omission. Never report an external side effect as done without a verifiable handle or a read-back.

**A green execution is not a delivered answer.** `status: success`,
`executionStatus: success` and `ok: true` with a real `message_id` all describe the
*chain*, not the content. When the tail of the chain forwards an LLM node's text
to a live channel, read the string that landed. Provider-routed models
(`openrouter/free`) can return metadata instead of prose with every status green,
and the break appears mid-window with no edit of yours in it — sweep executions
and compare against the edit's `updatedAt` before attributing it to your change.
See `references/llm-node-output-validation.md`.

## References

- `references/automation-gate.md` — the eight-question gate before building an automation: value vs fragility, failure path, human steps, idempotency, spend caps, secrets, rollback, boundaries — plus the build / build-with-gate / do-not-build verdicts.

- `references/public-api-quirks.md` — endpoint capability differences across instances, the executions-endpoint fallback, and inspecting an API key's JWT claims for expiry.
- `references/max-messenger-api.md` — MAX bot API: auth header format, pin/unpin, message delete.
- `references/editing-node-wiring.md` — output-index/fan-out semantics, LangChain sub-node edges, `runOnceForAllItems` item loss, timezone storage conventions, LLM date validation, offline harness recipe.
- `references/expression-resolution-and-payload-integrity.md` — the `=` prefix on `jsonBody`, truncation-safe workflow reads, composing PUTs from live state, node-deletion pruning, displayed-ordinal/lookup agreement across differing SELECT pools, month-day order bugs.
- `references/credential-and-auth-consistency.md` — keeping tokens out of the graph via `httpHeaderAuth`, writing the inbound auth contract down before adding a call, and triaging a 401 by credential provenance.
- `references/external-data-parsing.md` — Code nodes that fetch and parse external blobs: the silent-drop parser trap, column-count histograms, counting against the source API, Google Sheets service-account read/write paths, trimming a shortened rewrite.
- `references/latex-column-cleaning.md` — stripping `$`/`\text{}`/`{,}` from a PDF-converted knowledge-base column: substitution order, the residue assertion, number-invariant triage.
- `references/retrieval-quality-measurement.md` — measuring a lexical retriever before recommending a fix: building an honest probe set, why a suffix stripper fails Russian, when a tied score means ambiguity rather than ranking, and when every candidate fails so nothing should ship.
- `references/llm-node-output-validation.md` — when the chain is `success` and the user still receives junk: free-router aliases returning provider metadata, proving the break is external by sweeping executions, and the guard node to put between the agent and the send node.
- `scripts/test_code_node.js` — run a Code node's `jsCode` offline under node with mocked `$input`/`$json`/`$()`.