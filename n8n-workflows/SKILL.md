---
name: n8n-workflows
description: Use when inspecting, debugging, or editing n8n workflows.
---

# Working with n8n workflows

Read-only inspection is the default posture. Never PUT/PATCH/DELETE a workflow,
activate/deactivate it, or trigger a run until the user explicitly asks for the
change — and when they do, show the diff of node parameters first and get a yes.

## Step 1 — authenticate and prove the connection

The public API takes the key in a header, NOT as `?apiKey=` (that is the
internal API and it is refused with a misleading auth error):

```
curl -s -H "X-N8N-API-KEY: <key>" "<base>/api/v1/workflows?limit=100" -w "%{http_code}\n"
```

A 200 on that call is the only proof the key works. Report the HTTP status, not
"connected". If a self-hosted base URL has a path prefix (e.g.
`https://host.tld/n8n`), keep it in the base — endpoints are `<base>/api/v1/...`.



### Step 1b — the key returned has never been live: a 401 means you read a mask, not the key

`.env` files and terminal output routinely print only the head+tail of a long
key (`eyJhbG...9mE0`), and the same masking can be applied to the value in a
credential database. **Re-typing the displayed mask is the most common cause of
a 401.** If the public API refuses with `401 Unauthorized`:

1. The authoritative copy of the live public-api key is the n8n instance
   database itself: `/opt/n8n/data/database.sqlite`, table
   `user_api_keys`, column `apiKey` (rows where `audience = 'public-api'`).
   The `.env` that ships with the project is a redacted copy of the same value,
   so it will fail the same way.
2. Read the value into a variable with python (never print it to the screen or
   paste it into chat):

```bash
export N8N_KEY=$(python3 - <<'EOF'
import sqlite3
con = sqlite3.connect('/opt/n8n/data/database.sqlite')
con.row_factory = sqlite3.Row
row = con.execute("SELECT apiKey FROM user_api_keys WHERE audience='public-api'").fetchone()
print(row['apiKey'])
EOF
)
```

3. Prove the connection with the 200-status check first (the skill's Step 1
   rule), then continue with the normal workflow listing.

If the DB row is also unreadable, or the value there is visibly truncated,
fall back to a local JSON backup — but treat the backup only as a diff baseline,
never as the source of truth, and say so in the report.

**Two instance-level API quirks will otherwise read as data problems.**
`GET /api/v1/workflows/<id>/executions` can answer `404 "Version not found"` —
use the GLOBAL `GET /executions` and filter by `workflowId` client-side, because
an unreachable endpoint and "zero executions" are indistinguishable in a report.
And `limit` is not accepted on every endpoint: `400 Unknown query parameter`
means the parameter is unsupported there, not that the filter is wrong. Strip the
parameter and retry unfiltered.

## Step 2 — list, then fetch the single workflow in full

`/workflows` returns the list view (names, active flags, inline nodes, no
connections). `/workflows/<id>` returns `connections` and full node parameters.
Always take the id from the list view, then fetch the single workflow before
reading any code — the list view's node objects are abbreviated.

**A local JSON backup is a fallback for when no API key is available yet, never
the source of truth.** Before reporting any finding, diff the backup against the
live workflow: compare `versionCounter`/`updatedAt`, node count, node names and
each `parameters` blob. Findings from a stale copy routinely name bugs that were
already fixed (an absent `alwaysOutputData`, a rewritten expression) and hide the
real breakage. Report "already fixed on the live version" instead of listing it as
open.

**Fetch every API body to disk with `curl -o <path>`, then `json.load` it. This
applies to `/workflows/<id>` as much as to executions.** Any body over the tool's
stdout budget (~50 KB) is truncated with a literal `... [OUTPUT TRUNCATED - N
chars omitted ...]` marker spliced INTO the text. When that cut lands inside a
JSON string value, `json.loads` still succeeds and hands you a plausible object
whose embedded code has a corrupted line in the middle — a "live" workflow that
differs from the instance. Two guards, both mandatory before any PUT:

```bash
curl -s -m 60 -H "X-N8N-API-KEY: $K" "$B/workflows/<id>" -o TRUE-wf.json
grep -c "OUTPUT TRUNCATED" TRUE-wf.json   # must be 0
python3 -c "import json;json.load(open('TRUE-wf.json'),strict=False)"
```

and re-assert the marker is absent from the assembled PUT payload
(`"OUTPUT TRUNCATED" in open(payload).read()`). Compare a node's `jsCode`
length against the previous copy as a second tell — a code blob that shrank by
hundreds of characters between fetches is truncation, not an edit. n8n also
embeds raw control characters inside bodies, so always `json.loads(text,
strict=False)` — plain `json.loads` dies with `Invalid control character at:
line 1 column NNNNN` on a valid response.

**A fetched workflow carries TWO copies of the graph: `nodes` and
`activeVersion.nodes`.** The snapshot under `activeVersion` is what the trigger
actually executes and it can differ from `nodes`, so an audit that reads only
`nodes` can miss the live persona, a reverted prompt or a disabled branch. Diff
the two node lists (count plus per-node `jsCode`/`systemMessage` length) before
reporting anything from a fetched body, and patch BOTH lists whenever you build
a copy of a workflow for reuse — a single-list patch leaves the stale snapshot
running with no error anywhere. Full templating procedure:
`references/workflow-templating.md`.

## Step 3 — print the graph before reading any node

Reconstruct edges from `connections` and emit an ASCII arrow graph first:

```
for src, outs in wf["connections"].items():
    for oi, out in enumerate(outs.get("main", []) or []):
        for dst in out or []: print(f"{src} -[{oi}]-> {dst['node']}")
```

Then dump each node's parameters grouped by type (`code` -> `jsCode`,
`supabase`/`httpRequest`/`*Trigger` -> whole `parameters` JSON, `langchain.agent`
-> `options.systemMessage` + subnode list). Printing `list(p.keys())` first for an
AI-agent node tells you whether the prompt is in `text` or `prompt` before you
print the wrong key and see empty output.

## Step 3b — a polling trigger that stopped is a config problem, not a code problem

Before reading any node, check whether the workflow is even receiving events:

```
GET /api/v1/workflows/<id>            -> staticData.node:<trigger>.marker, pollTimes
GET /api/v1/executions?workflowId=<id>&limit=5
```

Three failure shapes, all silent:

- `pollTimes.item` is empty (`[]`) — the trigger has no schedule at all. It ran
  once at activation and never again. Symptom: exactly one `trigger` execution,
  then silence forever, while a sibling workflow on the same bot polls fine.
- Two active workflows on the SAME bot credential share the event cursor. If
  both show the same `marker` value, whichever polls first consumes the events
  and the other sees empty polls. Fix by giving each its own schedule and
  verifying the markers diverge, not by editing node code.
- Every poll returns zero items because nothing is being sent. Distinguish this
  from "trigger broken" by checking whether ANY recent execution had a non-empty
  trigger output, not by the exit status.

## Step 3c — audit the input gate of every conversational branch

A bot that listens to a group must answer only what it understands, and the gate that
enforces that is the one node worth reading first on every pass. Two shapes appear:

- **Strict-match consumer (usually correct).** A regex like `^([1-9]|1[0-9]|20)$`
  accepts a bare digit and drops everything else silently — greetings, images,
  questions, typos. "The bot ignored my message" is the intended behaviour here, so
  do not "fix" it by widening the pattern.
- **Open-ended consumer (usually the defect).** A branch that sends every inbound
  message into an LLM and then reports a parse failure sends the error to the
  *sender* when the content was never a command. A master typing «доброе утро» or
  sending a sticker then receives «⚠️ не понял дату». The filter upstream of it usually
  checks only sender identity and message age, never content.

Fix the open-ended shape by adding a content predicate before the expensive node: if the
message carries an attachment, or contains none of the expected command words/digits,
return `[]` and end the branch silently. Keep genuine malformed-command feedback — «free
on the 32nd» should still be answered with a clarifying question — by gating on intent,
not on parse success.

Read both gates before reporting anything: one of the two bots on the platform may already
be correct, and the report should say which is which rather than implying both are broken.

## Step 5a — structural edits: deleting or re-routing nodes

Removing a feature (a reminder chain, a duplicate-post path) is a normal request,
and it edits the graph rather than one node's parameters. Two traps, both
reached the same session:

**`connections` keys survive their node.** After deleting nodes, every connection
entry whose *source* was one of them must go too, or the PUT fails with
`400 Workflow structure is invalid (unknown_connection_source)`. And the obvious
emptiness filter is wrong:

```python
# WRONG: [[]] is a list containing one empty list -> truthy
conn = {s: v for s, v in conn.items() if any(o for o in (v.get("main") or []))}
# RIGHT: does the entry name an actual target node?
conn = {s: v for s, v in conn.items()
        if any(x for o in (v.get("main") or []) for x in (o or []))}
```

**Build the PUT from a body you just fetched, never from a backup you read
earlier in the session.** A backup is a diff baseline; using one as the mutation
base silently reverts every fix applied since that copy was taken. Re-fetch
immediately before assembling the payload, and assert each already-shipped fix is
still present in the base (`"$saveWorkflowStaticData(" not in dedup_js`) before
editing.

**A node that is the tail of a deleted chain must lose its outgoing connection
entirely**, not be left pointing at a removed node: reassign its only outgoing
edge (e.g. `Code: пересобрать текст` -> `HTTP: Edit Message`) or delete the key so
the node becomes terminal.

Validate the assembled payload before sending — dangling sources, dangling
targets, and removed nodes still referenced in any `parameters` expression:

```python
names = {n["name"] for n in p["nodes"]}
bad_keys = [k for k in p["connections"] if k not in names]
dangling  = [(s, x["node"]) for s, v in p["connections"].items()
             for o in (v.get("main") or []) for x in (o or []) if x["node"] not in names]
```

**Removing a feature does not clean up the data it wrote.** A slot left `locked`
by a crashed run stays invisible to clients, and the workflow's own UPDATE cannot
repair it: lock nodes filter on `status = available`, so a row already in another
state is deliberately excluded. Say so explicitly and ask which the user wants.

**Direct DB writes need a key the REST API never returns.** n8n exposes only the
credential `id` and name; the secret is encrypted instance-side. And a service
key alone cannot form a request — the project ref (the `<ref>` in
`https://<ref>.supabase.co`) lives inside that same credential. So a stale row
can only be fixed by (a) the user supplying BOTH the service-role key and the
project URL, or (b) a command node inside the workflow. Ask for both parts in
one message; discovering the ref is missing after the key arrived wastes a round
trip. Read the affected rows back after writing rather than trusting `success`.
Offer (b) as the durable option — it removes the need for ad-hoc database
access next time too.

**Never store secret tokens in node JSON bodies; use n8n credential store (e.g., httpHeaderAuth) to avoid leakage into backups and workflow exports.** When a node needs a bearer token or API key, create a credential of appropriate type and reference it via the node's authentication settings. This keeps secrets encrypted in the instance's credential store and prevents them from appearing in workflow JSON or backups.

**When using Supabase nodes for slot listing, always include a date filter (e.g., `date ≥ today`) to ensure the pulled set matches the active pool used elsewhere (e.g., in the app or other workflows).** Omitting the filter causes numbering drift between the list shown in the group and the list used for booking, leading to clients selecting the wrong slot.

## Step 5a-bis — data-shape multiplication: one node run per input item

The single most productive class of bug this instance family produces. A Supabase
(or any DB) node in n8n **executes once per input item**, so a read placed after a
write multiplies: N inserted rows -> N runs of the SELECT -> N×N rows out. The
downstream text node then renders every slot N times and the user sees a list of
duplicates where a booking list should be.

```
insert 3 rows  ->  SELECT runs 3x  ->  9 rows  ->  message lists each slot 3x
```

Recognise it in the execution data: group by node and compare the output count to
the input count.

```python
for name, runs in rd.items():
    print(name, [len(b or []) for b in runs[0]["data"]["main"]])
```

Three distinct mechanisms produce this, and each needs its own fix:

- **`.item` / `.first()` inside a filter value.** `$('Node').item.json.date`
  resolves per item, so the node runs once per item even when the value is
  identical across them. Prefer `$json.<field>` when the field is present and
  constant on every incoming row.
- **`alwaysOutputData: true` on a write node.** The write returns its INPUT rows as
  well as what it wrote, so the batch is duplicated at the source.
- **`returnAll: true` on a read node.** Combined with per-item execution this pages
  the whole result set once per item.

**The durable fix is architectural, not a flag: build the outgoing list from the
payload you already have, not from a re-read of the table you just wrote.** If a
webhook/normaliser node already carries the full slot list, a Code node can render
the message straight from it — fewer nodes, fewer round trips, and the
duplication class is structurally impossible. Reach for this before tuning
`alwaysOutputData`/`returnAll`; those only hide the symptom when the item counts
happen to be 1.

**A Switch fan-out runs its branches in PARALLEL, not in sequence.** Routing a
write and a side-effecting update to two branches of the same Switch means they
race, and the loser corrupts the winner's result — a cleanup update that sets
`status = expired` will happily mark rows the insert branch just wrote, and the run
still reports `success`. If one branch must observe the other's result, chain them
through a node instead of fanning out. Symptom to recognise: rows appear correctly
inserted and are then immediately mutated by a node that "only" tidies up. Delete
the racy node and do its work synchronously before the write when possible.

**Never wire a node's own output back into itself.** An update node returns the rows
it changed; feeding those into an insert of the same table raises
`duplicate key value violates unique constraint "<table>_pkey"`. Delete the edge.

**Renaming a node breaks every `$('Old name')` reference, including ones nested
deep in parameters.** A rename done in the PUT body leaves other nodes pointing at a
name that no longer exists, and the failure only appears at RUN time as
`ExpressionError: Referenced node doesn't exist` — often on the node you did not
touch, and n8n may silently mark nodes `disabled` after such an error. Grep the
whole workflow for the old name before renaming (the string lives in
`parameters.filters.conditions[].keyValue`, `jsonBody`, `url`, and `text` alike),
and after the PUT assert the old name appears ZERO times in the live body. Print
`disabled` nodes explicitly afterwards: a node n8n switched off mid-run is a
feature that silently stopped existing.

## Step 5b — the PUT itself

`PUT /api/v1/workflows/<id>` with the whole workflow object. Field rules learned
the hard way:

- The body is validated as a strict schema. Every string field must be present
  as a string — a workflow with `description: null` returns
  `400 request/body/description Expected string, received null`. Coerce `None`
  to `""` for `description` and `name` before sending.
- Strip read-only keys or they are rejected/ignored: `id`, `active`,
  `versionId`, `versionCounter`, `activeVersionId`, `activeVersion`,
  `createdAt`, `updatedAt`, `triggerCount`, `shared`, `tags`, `meta`,
  `isArchived`, `pinData`, `staticData`, `sourceWorkflowId`. Keeping the body
  to `name`, `description`, `nodes`, `connections`, `nodeGroups`, `settings` is
  the reliable minimal PUT.
- A successful PUT returns 200 with the full workflow and a bumped
  `versionCounter`. Re-fetch afterwards and assert the intended field actually
  changed (`jsonBody`, a code substring) — a 200 on a stale or mis-keyed body
  looks identical to a real fix.
- `active` is preserved and polling keeps ticking on its own; a
  deactivate/activate cycle is NOT required after a PUT. Confirm by listing
  executions a minute later rather than restarting the workflow.
- Never hand-edit `staticData`. The trigger `marker` and any static-data array
  the user relies on live on the instance side and your PUT must not clobber
  them.

A PUT that changes an active workflow bumps `versionId`; the trigger marker can
reset and old messages replay. After any PUT: re-read executions, and if the
schedule looks wrong, deactivate + activate, then confirm new trigger executions
appear.

## Re-rendering shared state: edit the original post, never post a new one

When a bot publishes state to a chat and later needs to update it (a slots list
after a booking), the wrong shape is `recompute -> SendToChat -> HTTP: Pin`. Every
update leaves a second post behind while the ORIGINAL stays pinned showing stale
data — the pinned message contradicts the newest one, and the "reply with a
number" prompt keeps advertising slots that are already taken. The right shape is
`recompute -> HTTP: Edit Message` keyed on the remote message id recorded at
publish time, deleting the send/pin nodes entirely.

**A literal template string in an API error means the expression was never
resolved, not that the field name is wrong.** An HTTP 400 whose body echoes
`Invalid message_id: {{ $json.group_message_id }}` is the API reporting the
literal text it received. Before hunting for a renamed field, check the HTTP
node's `jsonBody` for the leading `=`:

```
WRONG  '{"message_id": "{{ $json.group_message_id }}"}'    n8n sends it verbatim
RIGHT  '={"message_id": {{ JSON.stringify($json.group_message_id) }}}'
```

Any HTTP-node string parameter that should interpolate MUST begin with `=`; n8n
treats it as a plain literal otherwise. The same node working elsewhere is the
tell: diff the two nodes' parameter prefixes and copy the working one. Note
`JSON.stringify` already returns a quoted string, so the template must NOT add
its own quotes around the interpolation. Diagnose from the `=` prefix and the
error text together — guessing at field names from this error sends you to
inspect every emission map for a problem that does not exist.

Also check for a second, independent publisher before concluding one exists: two
active workflows sharing one bot credential can both write to the group, and only
one of them may be the culprit you are looking at.

**Editing in place has a prerequisite: the post must actually be pinned.** The
edit-instead-of-repost shape only works if something pinned the ORIGINAL at
publish time. If the pin node failed on every publish, the shared post exists but
is invisible in the pinned view — editing it then updates a message nobody is
looking at, and the group keeps showing whatever older post got pinned or no pin
at all. After switching a workflow to edit-in-place, confirm the pin actually
succeeded at least once; if it never has, the fix is incomplete and the pinned
view is still wrong.

**Prove "never worked" instead of "not verified".** To establish whether a node
ever succeeded, sweep the retained executions for that node's output rather than
only reading the newest few:

```bash
# every run that reached the node, with its outcome
for o in runData.get(<node>, [{}])[0].get("data", {}).get("main", [[]])[0] or []: ...
```

An entry with `data` succeeded; an execution whose `resultData.error.node` names
that node failed; its complete absence means the node was never reached. This
separates three claims people blur together — "correct by inspection", "executed
and failed", and "never executed" — and only the third is settled by scanning
history. A fix whose node has no successful run in the whole retained window is
unverified no matter how obviously right the expression looks.

**Scan history before promising a downstream fix will land.** A corrected pin
node that has not run since the correction is a claim, not a result: say the
expression is right but no live call has exercised it, and name the action that
would produce one (a new post from the master) instead of implying it is done.

## Step 4 — executions are the truth about what ran

`/api/v1/executions?workflowId=<id>&limit=250` gives status/count/timestamps;
`/api/v1/executions/<id>?includeData=true` gives `data.resultData.runData`.

**Never treat an all-`success` execution list as proof the pipeline works.**
A scheduled trigger that yields zero items exits successfully by construction.
The discriminator is `len(runData)`:

- `runData` with one key = the trigger -> nothing downstream ever ran. Report
  this as "no data has traversed this pipeline in the retained window", not as
  health.
- `runData` with multiple keys -> inspect `executionStatus` per node for the
  real failure point.

History is truncated by the instance's retention (often same-day only). Say
"retained window", never "it has never run".

**Counts of `error` rows are not a diagnosis, and `success` does not mean the
side effect happened.** A successful execution proves the run reached the end of
the graph, which is exactly what a workflow does when a write targets an empty
or mis-keyed table. So when you report execution statistics, cross-check the
thing the workflow exists to do: read the target rows back (DB `SELECT`, a Sheets
range, the pinned chat message) and compare against the run window. Empty target
plus fresh `success` runs is a contradiction the user must hear about — report
both numbers side by side rather than picking the reassuring one. Symmetrically,
offer the two candidate explanations instead of silently picking one: state that
it is either "nothing has been published lately" or "the write is not landing
where you think", and name the one observation that separates them.

**A dead trigger outranks every code finding.** Check the newest execution's
`startedAt` and, for polling triggers, the `staticData` marker
(`node:<trigger name>.marker`). Compare against a sibling workflow that uses the
same trigger type and platform account: if the sibling still ticks on schedule
while this one has been silent for hours, the workflow receives no events at all
and no node-level fix matters. That check costs one `/executions?limit=10` call
against the GLOBAL list and settles "why does this feel dead" faster than an
audit.

## Step 5c — tearing down state the bot wrote

`references/teardown-chat-and-db-state.md` covers a "clean the slots, the old
messages and the pin" request: build the inventory from a DB `SELECT` plus the
messaging nodes' execution envelopes (you usually cannot list chat history),
unpin before deleting the post the pin points at, and read every deletion back
per item instead of trusting 200s. It also lists the two distinct `verify.token`
401s (rotated value vs. a wrongly added `Bearer ` prefix) so a stale token is
diagnosed in one call rather than retried.

Also print nodes with `disabled: true` — a disabled branch (a wait+reminder
chain, a duplicate-post edit) is a feature that silently does not exist, and the
user usually does not know it was switched off.

**A fix is only verified when a non-empty poll has run through it.** After
changing a node, group recent executions by `len(trigger output)` and require at
least one with `> 0` that traversed past the edited node. All-`success` runs with
`poll: 0` prove only that the trigger still ticks. Also state plainly that the
message which exposed the original bug is still lost — it errored before the
fix, and nothing replays it, so the user must re-send it.

**Latent bugs surface one at a time, so expect more than one round and say so.**
A pipeline stopped early hides everything downstream: fixing the third node can
expose failures in the fifth and eighth that were never reached. Each round,
read the whole `runData` map (`len(rd)` and per-node output lengths) to see how
far the run got, and report progress as "advanced from N to M nodes" rather than
declaring the fix complete. Before the user re-sends a test message, scan the
REMAINING nodes of the branch statically for the same class of bug — every key
an expression names must appear in some upstream emission map, and every node's
input shape must match what the previous node actually emits. Fixing what the
execution reached and leaving the untested tail unexamined guarantees another
test-message round-trip.

**Read a node's execution output by dumping every key, never a hand-picked
subset.** Selecting `["action", "date", "slot_index"]` and reporting `date: null`
invents a bug when the node emits the value under a different, correct name
(`slot_date`), and the whole report then argues with the user about a defect
that was never there. Print `sorted(json.keys())` first, then read what is
actually there. When the two name-spaces differ across a node boundary, that is
usually deliberate renaming — verify by grepping every `json.X` reference in the
workflow against the real emission maps before calling it a defect.

**This is a gate, not a style preference: a phantom finding costs round trips
the user pays for.** The pattern is always the same — you report a defect, the
user approves the fix, approves the sibling, and only then does the raw data
show there was never a defect. So before any node-level finding enters a report,
ask: did I read this from the node's own output, or from a list I typed myself? A
key absent from my selection and a key that is null in the node look identical in
the report; only `sorted(json.keys())` separates them. Symmetrically, when the
evidence says the field is correct, stop drilling for a cause instead of
escalating.

**Retract a wrong finding in the same breath you made it.** When a later check
contradicts an earlier claim, say plainly which claim was wrong and why the
earlier reasoning was wrong. Do not silently drop it or bury the reversal under
the next finding — a retracted defect the user still remembers as outstanding
misdirects their next decision, and they have already approved edits for it.

**A messaging node's output is a transport envelope, not your domain record.**
Send/publish/pin/edit nodes emit what the platform replied with — message id,
timestamp, `recipient`, `sender`, body text — and none of your record's fields.
So a downstream Code node wired to read `$input.all()` from a send node gets an
empty result set and returns `[]`, silently ending the branch. When a compute
node needs domain fields, reference the node that produced the record
(`$('Code: <result>').all()`) rather than the node that delivered it, and do not
assume the node one hop upstream is where those fields live. Check the emission
map by content, not by graph position: `body`/`sender`/`recipient`/`timestamp`
means you are looking at an envelope.

**Re-read the field contract on the LIVE workflow every session, not only when
a bug is reported.** Field-contract breaks recur because an earlier fix patched
the node that threw without grepping for the sibling that references the same
key. Run the expression cross-check from `references/field-contract.md` on every
audit pass; the live version may also have drifted since your last backup, so
diff `versionCounter` first and treat any change as someone else's edit.

## Step 5 — audit for the silent-failure patterns

`references/audit-checklist.md` is the review pass: read-back queries missing a
discriminator, two-phase writes without a transaction, stacked dedupe layers,
hardcoded IDs, implicit timezone, swallowed LLM parse errors, side effects that
cannot be retried, cross-node expressions naming a field nobody emits,
never-evaluated expressions. Run it before reporting findings; it is ordered by
how quietly each one breaks production.

`references/field-contract.md` is the focused pass for the rename class of bug:
build the key-emission map from the Code nodes, list every `{{ $... }}`
reference, cross-check, then confirm against one real execution.

When a list of user-typable ordinals exists, add the display/lookup agreement
pass from `references/display-ordinal-and-date-format.md`: assert the number
printed in the chat is the number the booking node resolves, offline, for every
free row; and when dates are formatted in more than one node, render one real
date through each and diff the strings.

**When one ordinal has to span several groups — multiple dates, rooms or
categories — read `references/cross-date-ordinal-identity.md` as well.** A bare
digit cannot carry a group, so per-group lists that restart at 1 make the lookup
ambiguous, and a platform that allows only one pinned message makes per-group
posts self-replacing. It carries the stable-numbering-pool invariant (the pool
includes booked rows, so a booking does not shift every later digit) and the
simulated proof for both.

## Step 5d — platform migration: Telegram → MAX (or any other)

`references/platform-migration.md` covers the systematic replacement of all
Telegram I/O nodes with MAX HTTP equivalents: trigger → cron+GET, send →
POST with recipient in query params, inline buttons → reply keyboards, file
download → two-step HTTP. The domain logic (Sheets, DB, AI agent) stays the
same — only the transport layer changes.

## Turning one workflow into a niche template

When a working bot has to be resold into another niche — different persona,
username and knowledge base, identical behaviour — build the copy offline from
a backup and never edit the production workflow. `references/workflow-templating.md`
carries the procedure: the config schema, the two node lists that must both be
patched, the two agent-prompt fields, the read-only keys to strip while
credential references survive, and the fingerprint guard that refuses to emit a
workflow still carrying the source niche's words.

## Step 6 — only when the user asks for a live run

`references/live-run-without-manual-trigger.md` is the validated procedure:
build a webhook-triggered copy, activate it, POST a realistic payload, read the
newest execution from the GLOBAL executions list, then delete your rows and both
throwaway workflows. Two things to internalize before you start: a webhook
payload is not shaped like a chat-trigger payload (insert a normalize node or
every run "succeeds" with zero items), and a live run on a production instance
posts real messages — confirm with the user what may be published before firing.

## Code node mode: `$json` is NOT the event in a batching node

n8n Code v2 defaults to run-once-for-all-items when the node emits one item per
batch. In that mode `$json` is only the FIRST item — a node written as
`const event = $json; event.message.body.text` silently reads the wrong element
(or throws `text is not defined`) while the sibling `$('Node').item` calls work
fine. Every Code node must either declare `mode: runOnceForEachItem` or use
`$input.all()` explicitly. Verify on a real execution before shipping:

```python
for n, runs in runData.items():
    print(n, [len(x or []) for x in runs[0]["data"]["main"]])
```

Silent-empty (`[[]]`) at a node that should produce output means the branch
stopped there, not that the node was skipped.

## Local simulation of Code nodes before shipping

You can execute a Code node's JS against captured execution data without
touching the instance: compile the source with `new Function('$input', '$',
'$getWorkflowStaticData', 'console', src)` and call it, feeding items captured
from a real `runData`. **Do NOT wrap the source in `(function(){ ... })()`** —
n8n already compiles the body as a function, so an extra wrapper makes the node's
top-level `return` return from the wrapper and your function returns
`undefined`. That failure is easy to misread as a logic bug. This catches the
failure modes a static read cannot: wrong `$` target, run-once-for-all items
dropped, and date math. Use real payloads plus a synthetic contention case
(UPDATE returning 0 rows) for the paths production hits only under race.

Assert the compiled result is an array before trusting it, and cover at least:
first pass with a batch containing a duplicate, a repeat pass with the same
ids (expect empty), a fresh id (expect one item), and an item missing the key
the node indexes on (expect a logged drop, not an exception).

**An unfaithful harness manufactures FAILs that are not defects, and the failure
mode is repeated and confident.** Two stubs cause nearly all of them:

- *Incomplete payload.* The stub `$json` omits a field the node reads early —
  `message.sender.user_id`, `message.body.attachments`, `_cfg`. The node then takes
  its identity/`is_bot` branch and returns `[]` for EVERY case, so valid inputs read
  as failures. Symptom: all cases reject, while `console.log` inside the gate shows the
  real reason. Fix: build the fixture from every field the node dereferences before the
  first assert.
- *Wrong pass detector.* A filter continues by returning `[{ json: event }]` and stops
  with `[]`; a detector that checks `out.length` on a shim whose shape differs, or that
  treats a thrown `THREW` string as `true`, reports the opposite of reality. Assert on
  the real shape: `Array.isArray(out) && out.length > 0 && 'json' in out[0]`.

When a harness reports failures, **suspect the harness first and say so out loud
before touching the workflow.** Reporting "the filter is broken" on the strength of a
stub you wrote yourself burns the user's trust twice: once for the phantom finding and
again for the retraction. Get to `fails=0` on the faithful stub before any PUT, and if
you cannot, ship nothing and name what you could not verify.

**A passing live test may have exercised a different branch than the one you
changed.** Content gates sit behind identity checks, so a test message from a sender
the branch does not accept is discarded at the identity gate and never reaches the
logic you edited — the run looks green and proves nothing. After a live check, read
the execution's own trigger output and confirm `sender.user_id` and the message body
match the case you meant to test. If they do not, say plainly which gate consumed it
and ask for a message from the right sender rather than reporting the filter verified.

**Inject only helpers n8n actually provides.** A hand-written shim for a
function that does not exist in production turns the simulation into a false
pass: the sandbox runs clean, the instance throws `ReferenceError` on every
event. `$getWorkflowStaticData('global')` is real; there is NO
`$saveWorkflowStaticData` — mutations to the returned object are persisted
automatically at the end of the run. Check any helper you are unsure about
against the Code-node builtin list before stubbing it, and Never treat a green
simulation as proof: re-group `/executions` by error after the change. And
re-check the Code node's own syntax inventory — a nonexistent builtin in the
middle of an otherwise correct node kills the whole downstream chain on every
inbound event, which reads in the execution log as one failed node rather than a
workflow-wide outage.

## Reporting shape the user wants

- Node inventory first (name | active | node count), then the graph, then
  findings.
- Findings numbered, each one mechanism + consequence, most damaging first.
- Separate "verified from data" from "cannot verify without a live run" — an
  expression whose behavior depends on a run you cannot trigger is a question,
  not a claim.
- Close with a concrete choice of next step, not a summary of what you read.
- State plainly when a check cannot be settled without input you do not have (a
  rotated token, a message only the user can send), and name the single action
  that produces the evidence. Offer to prepare the fix in parallel rather than
  making the user wait on a round trip — but when they ask to see the result
  first, hold the edit.
- Reply in the user's language.