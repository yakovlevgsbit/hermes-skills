# Displayed ordinals, lookup keys, and date formats

Two bug classes that survive a passing test suite and reach the user.

## A displayed ordinal is a contract with the lookup node

**Failure shape.** Several posts feed the same date. Each publish gets its own
`slot_index` starting at 1, so three posts for one day produce three rows with
`slot_index: 1`. A merged list prints the duplicate:

```
🟢 1. 14:00 – 16:00
🔴 1. 17:00 – 18:00 (занято — ...)
```

The original lookup node grouped by `group_message_id` and, when a number
appeared in several sets, took the newest — so it happened to be right, while
the post was misleading.

**Renumbering the list alone makes it worse.** With a correct 1..N list, the
lookup still compares the stored `slot_index` and the client's digit resolves to
a different slot or to none at all:

```
1 -> id=42 ✅
2 -> not found ❌
3 -> not found ❌
```

**Fix both halves from ONE ordered source.** Sort by `start_time` and assign
`i + 1`; have the lookup node rebuild the same map instead of comparing a stored
per-post index:

```js
const ordered = [...rows].sort((a, b) => String(a.start_time).localeCompare(String(b.start_time)));
const displayNum = new Map();
ordered.forEach((r, i) => displayNum.set(r.id, i + 1));
const slot = ordered.find(r => displayNum.get(r.id) === wanted && r.status === 'available');
```

Ordinals in a rendered list must also be unique — that is the symptom, not the
cause. Derive them from the sorted order, never from whatever index the data
carries.

**Prove it offline before deploying.** Feed every printed ordinal back through
the real lookup code and assert:

- each free row → `found.id === displayed_row.id`
- a booked row → `not_found`
- an out-of-range number → `not_found`

The not-found hint must list the displayed numbers (`свободны 1, 3`), not raw
stored indices, or the client is told to type something that no longer exists.

## Month/day swap passes every test until day > 12

A formatter built from an ISO match:

```js
const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
return `${m[2]}.${m[3]}.${m[1]}`;   // m[1]=year m[2]=month m[3]=day -> month first
```

renders `2026-10-25` as `10.25.2026`. Every date in the single-digit range
(`2026-10-04` -> `10.04.2026`) is indistinguishable under the bug, so a suite of
otherwise-correct checks passes and the defect appears the first time a
two-digit day is rendered.

**When a workflow formats dates in more than one node, render one real date
through each and diff the strings.** Identical parsing with divergent output
means one node has the swap. The confirmation path — `date_display` sliced as
`slice(8,10).slice(5,7).slice(0,4)` — is the reference to compare against,
because it is the string the user reads in their DM.

The user-visible symptom is a single workflow printing two different formats for
the same booking: «25.10.2026» in the confirmation and «10.25.2026» in the
pinned post. Fix by making every formatter match, not by picking a winner.

**The root cause is upstream, and worth fixing too.** Duplicated ordinals exist
because the master is allowed to publish a fresh post per slot batch. Two durable
options, in order of preference: (a) when a post for that date already exists,
EDIT it instead of publishing another — the schema already records
`group_message_id` per slot, so the "is there a post for this date" lookup is
one query; (b) if multiple posts per date are intentional, renumber both halves
as above and accept that the number is a position in the merged list, not a
stable slot id. Option (a) also removes the duplicate-posts-in-chat problem that
option (b) leaves behind. Say which one you implemented.

**Related:** the same rule applies to any tuple built from a positional regex or
split — always name the group you mean (`{day}.{month}.{year}`) rather than
indexing blindly, so a future group reorder cannot silently swap fields.

## Scope limit — this pass assumes ONE group

Everything above assumes every printed number is resolved against a single
collection, which is what makes `sort by start_time` + `i + 1` sufficient. It stops
being sufficient the moment the bot accepts a bare digit and more than one group
(date, room, category) is published: the digit carries no group, so per-group lists
that restart at 1 are ambiguous and no lookup-side filter can repair it. That case,
the stable-numbering-pool invariant, and the one-pinned-message constraint are in
`references/cross-date-ordinal-identity.md`.

One ordering detail from this pass does carry over: derive the number from the
sorted order, never from whatever index the data carries. Withdrawn rows must be
excluded before numbering, since a number they hold can never be resolved again.