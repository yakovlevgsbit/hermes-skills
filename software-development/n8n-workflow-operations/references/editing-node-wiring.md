# Editing node wiring and Code semantics

The failure modes below all pass validation, deploy cleanly, and return
`success` — you only learn about them from a live run or an offline harness.

## Output index: only wire indices a node can actually emit

A node that returns a single array emits **only `main[0]`**. Pointing a
downstream node at `main[1]` (to get two branches) is accepted by the API and
by the UI, and the downstream node then **never executes** — no error, no
warning, the execution just ends at the upstream node. Fan out by listing
multiple targets on the *same* index instead:

```python
conns["Code: enrich"] = {"main": [[{"node": "A", ...}, {"node": "B", ...}]]}
```

## Fan-out runs downstream once per input item, and Switch branches run in PARALLEL

Two nodes on one output index means each receives its own copy of every item.
If a downstream read/SELECT node is fan-out-fed *and* receives multiple items,
it is invoked once per input and each invocation returns the whole result set —
so N inputs produce N×M rows into the next node. Duplicated lines in a
composed message usually come from here, not from bad data. Verify by
comparing the item count leaving the fan-out node against the row count
entering the next.

A Switch's branches are **not** a sequence — they fire concurrently. Putting a
row-mutating UPDATE on one branch and an INSERT on the other lets the UPDATE
win the race and mark rows `expired`/`stale` the instant they were created; the
execution still reports `success`. When a branch has a side effect on the same
rows another branch writes, serialize them upstream (one node that does both,
in order) instead of trusting branch order.

Prefer removing the redundant read entirely: if the upstream node already
carries the full record, build the user-facing text from that node's output
instead of re-querying.

## Supabase write nodes echo their input back

`alwaysOutputData: true` on a Supabase **write** node emits the incoming items
*as well as* the written rows, and `returnAll: true` on a read node emits every
row regardless of how many were asked for. Either one puts duplicate or
unfiltered rows into the next node — the classic symptom is a numbered
user-facing list where every entry appears two or three times.

Set `alwaysOutputData: false` on write nodes whose output feeds a builder, and
`returnAll: false` with an explicit `limit` on read nodes. Then read back the
actual rendered message (not just the execution status) and count its entries
against the number of records you meant to publish.

## Renaming a node breaks `$('Old name')` references everywhere

Renaming a Code node and updating only the Code bodies leaves stale references
inside other nodes' `filters.conditions[].keyValue`, `fieldValues`, `jsonBody`
and URL expressions. The graph then fails at runtime with
`Referenced node doesn't exist`, naming a node you did not touch.

Two traps make this survive two fix attempts:

- A naive string replace over `json.dumps(node)` misses nothing **only if** you
  replace inside the parsed structure. Replacing in the outer payload and
  re-serializing works; replacing in `parameters` after you already stripped
  other keys does not.
- `GET /workflows/{id}` returns an `activeVersion` object containing its **own
  snapshot** of the nodes. Counting old-name occurrences in the whole response
  keeps reporting leftovers forever even after the live `nodes[]` are clean.
  Grep `nodes[]` only, and re-read after the PUT rather than trusting the PUT
  response body.

Assert the rename is complete by asserting the old name appears **zero** times
in `nodes[]`, then run one live execution.

## LangChain sub-nodes connect by their own type, not `main`

An AI Agent's model is wired through `ai_languageModel`, not `main`. A test
copy built by copying `main` edges alone fails with
`A Chat Model sub-node must be connected and enabled`. When cloning a graph,
copy every non-`main` edge type too:

```python
conns["Model node"] = {"ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]]}
```

Same for tools (`ai_tool`), memory (`ai_memory`), and embeddings
(`ai_embedding`).

## `runOnceForAllItems` + `$json` silently drops items

Code nodes default to run-once-for-all-items. In that mode `$json` is only the
**first** item, so a pattern like `Array.isArray($json) ? $json : ($json.data || [$json])`
degrades to a one-element array and every subsequent `rows[0]` /
`map()` over it sees a single record. Use `$input.all().map(i => i.json)`.

Symptom to recognize: a composed list that renders exactly one entry when the
data had several. Check whether the node's parameters carry an explicit
`runOnceForAllItems`/`mode` key at all — absence means the default, which is
all-items.

## Timezone: pick the storage convention, then never re-convert

Two coherent designs; mixing them is the bug:

- **Store UTC**, render with an explicit zone via `Intl.DateTimeFormat`.
- **Store local wall-clock verbatim**, render by slicing the ISO string
  (`String(iso).match(/T(\d{2}):(\d{2})/)`) and never touching `Date`/`Intl`.

If the DB holds local time but the formatter converts, every displayed time is
offset by the zone. Note that Postgres/Supabase round-trips a naive timestamp as
`+00:00`, so a row written as `14:00` reads back as `14:00+00:00` — under the
verbatim design that is exactly what you want, and any `Intl` call adds the
offset a second time.

State the convention in the LLM prompt explicitly ("14:00 means 14:00 local, no
offset") and assert it in the code, or the model and the formatter will each
assume a different one.

## LLM date output must be validated in code

A prompt carrying "today's date" handles relative phrases correctly but can
roll a *named* date back a year ("on 15 October" → a past-year ISO date),
because nothing in the data constrains the year. Prompt wording reduces it;
only a code guard closes it: reject/flag any slot whose `date` is before today
before it is inserted, and surface the failure instead of publishing it.

## Creating a graph from scratch over the API

Two shape errors are rejected at `POST /workflows` and cost a round trip each:

- `connections` values must be objects of the form
  `{"main": [[{"node": "X", "type": "main", "index": 0}]]}`. A bare array per
  source fails with `connections.X (invalid_type): Expected object, received array`.
- Node `id` values must be unique within the graph. Copying a graph while
  renaming nodes commonly collides on an inherited id:
  `nodes[1].id (duplicate_node_id)`. Reassign fresh UUIDs to every node on create.

Credential bindings (`{"supabaseApi": {"id": "...", "name": "..."}}`) carry over
from the source workflow unchanged and resolve to the instance's credential store,
so a copy exercises the same real integrations.

## Offline harness for Code nodes

Run the `jsCode` under `node` before deploying — much faster than a live run
and it isolates the logic from the platform. Provide the n8n globals yourself:

```js
const INPUT = /* array of item json */;
const NAMEJSON = {/* "Node name" -> item json for $('Node name') */};
const $json = INPUT[0];
const $input = { all: () => INPUT.map(j => ({ json: j })) };
const $ = (n) => ({ item: { json: NAMEJSON[n] || {} } });
const $getWorkflowStaticData = () => ({ /* ... */ });
(async () => { /* jsCode */ })()
  .then(o => console.log(JSON.stringify(o, null, 1)))
  .catch(e => console.log('THROWN: ' + e.message));
```

Assert on the boundary condition that matters (empty input, duplicate keys,
two posts sharing a sort key), not just the happy path — those are the cases
that reach users. See `scripts/test_code_node.js`.