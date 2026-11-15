# Expression resolution, payload integrity, and structural edits

Four classes of mistake that each cost a full deploy cycle. All of them deploy
clean and fail at runtime, so they are only visible in a live run.

## An HTTP node's `jsonBody` needs a leading `=` to resolve expressions

Without the `=` prefix n8n treats the field as a **literal string** and sends
the template text verbatim. The remote API then reports the template itself as
the invalid value:

```
description: Invalid message_id: {{ $json.group_message_id }}
```

The value on the wire was correct — the substitution simply never happened.
Compare against a sibling HTTP node that works: if one node's `jsonBody` starts
with `=` and another does not, that is the defect.

Working form:

```
={"message_id": {{ JSON.stringify($json.group_message_id) }}}
```

Two details that are easy to get wrong:

- `JSON.stringify("mid.x")` already returns a quoted string. Do **not** wrap it
  in quotes inside the template — that yields `"\"mid.x\""` and a valid-JSON
  body with a wrong value.
- Query-string parameters (`queryParameters.parameters[].value`) do resolve
  `={{ $json.x }}` without any `=` prefix on the body; the two fields behave
  differently, so verify each separately rather than assuming.

A `PUT` body sent with `--data-binary @file` must declare
`Content-Type: application/json`, and `description: null` is rejected with
`request/body/description Expected string, received null` — send `""`.

## Never read a large workflow through a truncating tool

Tool output that clips at a size ceiling inserts a marker like
`... [OUTPUT TRUNCATED - 1,080 chars omitted] ...` **inside the JSON string** it
was truncating. The document stays parseable, so `json.loads` succeeds and you
get a plausible-looking workflow containing garbage inside a `jsCode` node. A
subsequent PUT ships the corruption to the instance.

Rule: fetch large JSON to a file (`curl -o`), then read the file. Before any
PUT, assert the payload is clean:

```python
raw = open(payload_path).read()
assert "OUTPUT TRUNCATED" not in raw          # our own clipping marker
p = json.loads(raw, strict=False)
```

Also grep for the marker after reading a node's code back — if it appears in a
`jsCode` string, the read, not the instance, is corrupt.

## Compose every PUT from a just-fetched live copy

Node edits are not stored per-node: a PUT replaces the whole graph. Building
the payload from a backup taken earlier in the session silently reverts every
fix applied after that backup was written, and the reverts look like nothing
happened. Re-fetch the live workflow immediately before composing the payload,
and diff it against the version you meant to edit.

## Deleting nodes: prune `connections` keys, not just targets

Removing a node from `nodes` leaves it as a `connections` key, and the API
rejects the PUT with `unknown_connection_source`. Removing an edge *into* a
deleted node leaves `{"main": [[]]}` — and that is **truthy**, so a filter like
`any(o for o in v.get("main", []))` keeps the key. Test for real targets:

```python
has_targets = lambda v: any(x for o in (v.get("main") or []) for x in (o or []))
conn = {s: v for s, v in conn.items() if has_targets(v)}
```

Validate before sending: every `connections` key must name an existing node, and
every edge target must exist as a node.

## Never diagnose a field mismatch from a partial read

Printing `date: null` for a node and concluding the field is wrong is a
self-inflicted bug when the node emits `slot_date` instead and the downstream
consumer reads exactly that. Print the item's **full key set** and the value
across both nodes before naming a mismatch:

```python
print(sorted(item))                 # all keys the node emits
print(producer["slot_date"], consumer["date"])
```

Two nodes may legitimately rename a field at their boundary; check the mapping
in code before calling it inconsistent.

## Displayed ordinals and lookup keys must be one scheme

When a composed list prints a number for the user to type back, the lookup node
must resolve that same number. If the list renumbers across the whole date
while the lookup still matches a per-post `slot_index`, every ordinal past the
first either books the wrong slot or returns "not found".

Renumbering the *display* alone is not a fix — simulate it: build the printed
ordinals, feed each back through the real lookup code offline, and assert
`found.id == displayed_row.id` for every free row, plus `not_found` for a
booked row and for an out-of-range number. Slot ordinals also must be unique
within a rendered list; derive them from a single sorted-by-time order in both
nodes rather than from whatever per-post index the data happens to carry.

## The ordinals agree only while the SELECT row sets agree

Two nodes can implement the same numbering rule and still disagree, because they
read the table through **different WHERE clauses**. Audit the filter set of every
node that touches the table, print them side by side, and diff them:

```
pool A (lookup) : status != expired AND group_chat_id = …
pool B (render) : master_id = … AND date >= today AND status != expired
pool C (panel)  : date >= today AND status != expired
```

The defect is always the pool that is **wider** than the others. A lookup missing
a `date >= today` bound admits stale-but-not-expired rows, and since ordinals are
positional, one extra row at the head shifts *every* number by one: the list
prints "2" for 14:00 while the lookup returns 10:30. Silent, and the only
symptom is a client booked into the wrong appointment.

Three rules that close it:

- **Bound the lookup pool to the render pool, not the other way round.** Add the
  missing condition to the wider node; never delete rows from the visible list to
  make the two match.
- **Bind filter values to the same computed field the renderer uses** (a `today`
  already produced upstream, the chat id from the event) rather than a literal,
  so the pools cannot drift when the constant changes.
- **Reproduce the bug's input before declaring it fixed.** Insert the poison rows
  the defect needs — a past-dated, not-yet-expired slot — assert they fall out of
  every pool and that the remaining ordinals match, then delete them.

Then simulate the live path: for each printed digit, assert the lookup returns
the row the printed list named. Assert per digit, not in aggregate; a count
comparison hides which digit broke.

If the list is composed by a service the workflow calls (a panel, an app), make
that service the **only** builder of the string and delete the workflow's
copy — two builders of one user-facing string is a permanent drift risk. What
the workflow still needs from the DB is the *lookup* pool, which legitimately
reads rows; that is one implementation, not two, as long as its row set matches
what was printed. See `references/credential-and-auth-consistency.md` for the
call contract of that new edge.

## Month/day order bugs hide until day > 12

`${m[2]}.${m[3]}.${m[1]}` from an ISO match renders `10.25.2026` for
`2026-10-25` — month first. Every test date in the single-digit range passes.
When a date formatter exists in more than one node, render the same value with
each and compare against `date_display` from the confirmation path; the odd one
out is the bug, and consistency of the user-facing format is the actual
requirement.