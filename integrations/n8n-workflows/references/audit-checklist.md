# Audit checklist — silent-failure patterns

Ordered by how quietly each one breaks production. Run before reporting findings;
the point of each item is the mechanism, so a finding you cannot trace to a
mechanism is not a finding yet.

## 1. Read-back queries missing a discriminator

A SELECT that filters only on an entity type (e.g. `status = 'available'`) with
no date/owner/cycle guard will silently absorb rows left behind by earlier runs.
Live run, this is the bug that reaches users: the composed message lists
overlapping intervals with duplicate start times, and the "reply with a number"
prompt indexes rows whose stored `sort key` does not match the printed order —
so the client books the wrong slot.

Check every read feeding a user-facing message for: a date/cycle filter, and an
explicit exclusion of rows that are not yet finalized (a sentinel value like
`mid-pending`, written before a post-publish update lands).

## 2. A guarded UPDATE that aborts the branch on zero rows

The optimistic-lock shape — `UPDATE ... WHERE id = ? AND status = 'available'`,
then branch on whether a row came back — is correct in intent and broken in
n8n by default: Supabase returns an empty list when the filter matched nothing,
an empty list ends the branch, and the losing client gets NO reply at all. The
execution looks clean; nothing logs. Two fixes, both needed in practice:
`alwaysOutputData: true` on the UPDATE node, and a run-once-for-all-items Code
node that maps zero rows to an explicit failure action instead of returning
nothing. Verify against a real execution that the Switch output counts are
`[1, 0]` and never just `[1]` when a race is possible.

Same class, different trigger: a Code node left in run-once-per-item mode while
its body treats `$json` as a single event. It fails only on the first item
(`ReferenceError: <name> is not defined`) and passes batch runs, so a workflow
can be green for a hundred executions and then lose a run. When auditing any
Code node, match its body against its mode: run-once-for-all-items must use
`$input.all()`, per-item must return an array per item.

## 3. Two-phase writes without a transaction

`INSERT -> post to chat -> write back the remote id -> pin` has four points where
a failure leaves the DB inconsistent, and the recovery filter usually cannot see
the orphan. A row stranded with the sentinel value is skipped by the
finalize-update (which filters on the sentinel) yet still picked up by the
read-back in item 1. Put the finalize step before the side effects, or make the
read-back exclude the sentinel, or both.

Also check the ordering assumption: a node whose data snapshot in the run log
still shows the sentinel after a later node set it means `executionOrder` is not
what the author assumed. Never infer ordering from graph position alone.

## 4. Stacked dedupe layers

Two nodes filtering the same id (a built-in "remove items seen in previous
executions" plus a hand-rolled static-data array) means one silent drop path and
two places to debug. Plus an age guard on top. Together they mask outages: input
older than the guard window disappears with no error and no log, so a lagging
poll looks identical to an idle master.

Rule: exactly one dedupe layer, and it must be loud — when it drops, log the
count and reason so a missed message is diagnosable from execution history.

## 5. Hardcoded identity in many nodes

IDs repeated in Code bodies AND in node filter fields mean a single config
change is a multi-node edit with no compiler to catch a miss. Promote them to
workflow-level config or env and reference them.

The fix that works in n8n is a dedicated Code node at the top of the chain that
stamps `_cfg = { master_id, group_chat_id }` onto every item; downstream nodes
read `$json._cfg` or `$('Code: конфиг').first().json._cfg`. Note the residual
cost: a node whose URL needs a config value must be built as
`url: "=https://host/{{ $('Code: конфиг').first().json._cfg.group_chat_id }}/..."`,
and a doubled `=` there is a typo, not an expression — n8n silently sends the
literal string and the call fails on an empty/garbage id.

## 6. Implicit timezone

When an LLM prompt is told to convert colloquial times ("from 2 to 4" -> 14:00)
the offset lives in the prompt, while formatting uses `getUTC*` in Code. Nothing
in the data records which zone it is in. Verify the prompt's assumed offset
matches the master's actual zone and the server's, and store the zone with the
row so the assumption survives a move.

When a region is pinned to a fixed offset (no DST), the robust formatting is a
regex slice of the stored ISO string (`/T(\d{2}):(\d{2})/`), not `getHours()` —
`Date` re-interprets a naive timestamp in the server's zone and shifts every
displayed time by hours. Any in-code comment naming the offset is documentation,
not enforcement: say so in the finding and recommend storing the zone on the row.

## 7. Swallowed input in LLM parse nodes

`JSON.parse` inside a try/catch that rethrows is fine; a catch that logs and
continues turns a bad model response into a silent partial publish. Check where
each throw lands: a throw stops the branch (good, visible), a `return []` does
not (bad, invisible).

## 8. Post-publish steps that can never be retried

Pin/publish after the DB write means a pin failure leaves finalized rows with no
pin and no retry hook. Either make the side effect idempotent and re-runnable by
stored id, or move it before the finalize write.

## 9. Expressions that have never been evaluated

A field with a leading `=` in an otherwise literal field (e.g. a URL) is either
an expression or a typo depending on the field's expression resolution. If no
retained execution ever passed through that node, report it as unverified rather
than asserting it works — a live run is the only way to settle it.

## 10. Cross-node expressions naming a field nobody emits

When a hand-off node renames a field (`group_message_id` where the HTTP body
still says `message_id`), n8n renders the unresolved expression as its own
literal source, so the request leaves the instance carrying
`{{ $json.message_id }}` and the remote API answers with a validation error
that names the literal string. Everything upstream is healthy — only the side
effect fails, and only for consumers downstream of the renamed node.

Rule: for every expression crossing a node boundary, diff the referenced field
against the key set the upstream node actually emitted. One real execution
settles it — print the failing node's input item and its parameters from the
same execution body, so emitted key and referenced key sit side by side. Apply
the same check to `{{ $('Node').item.json.x }}` after any refactor of an
upstream Code node. `references/field-contract.md` has the per-node listing
procedure.

Error executions are the cheapest evidence available and the most often unread:
group them by node, take one representative, and read `resultData.error` plus the
failing node's parameters out of the SAME execution body. The failing node's
parameters in the log are the historical version, which is how a bug fixed hours
ago keeps showing up as a live error until someone diffs it against the workflow.