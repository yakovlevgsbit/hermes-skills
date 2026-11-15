# Staying under the memory character cap

`MEMORY.md` has a hard budget (~2 200 chars) and rejects the WHOLE operation batch if the final size would exceed it. A `replace` that grows an entry can therefore fail even when the addition itself is small — you must free room in the same call.

Applies equally to `USER.md` (~1 375) and `SOUL.md` (~20 000). `USER.md` is the one that overflows first: findings that feel like facts about the user leak in from `SOUL.md`, which already holds them as standing rules.

## Order of operations

1. Read all three files and count actual chars before planning.
2. Classify each entry: durable-and-unique (keep), procedure (move to a skill), duplicate or superseded (delete), transient setup state (delete).
3. Compute the final size after all removals and additions, then issue ONE atomic batch.

## USER.md is a profile, not a rules mirror

`SOUL.md` holds standing rules and outranks `USER.md` on everything about how work is done. An entry in `USER.md` that restates a `SOUL.md` rule costs double: it is injected twice every turn and can drift when only one is edited.

When consolidating `USER.md`, strip these classes entirely:

- Working-rule restatements (finish-and-verify, plan-only-for-production, install-is-preapproved, do-no-harm, language convention). They belong in `SOUL.md` only.
- Assignment dates and verbatim quotes. Keep the fact («named me Мария, addressed as a woman, name is in SOUL.md»), drop the date and the quote.
- Incident records — a past conversation that resolved one ambiguity. If the lesson generalizes, phrase it as a rule; otherwise it is session history.
- The same preference phrased two ways in a row (e.g. two lines about informal register). One entry, one rule.

Keep in `USER.md` only what `SOUL.md` does not already say: timezone with its verification source, hardware and its practical consequence, that the user works solo, the review-before-write habit, and how they answer questions.

## What to move out to skills

Anything with steps, endpoints, commands, or a debugging path. Memory keeps a single line naming the skill; the skill keeps the detail. Moving ~500 chars of procedure out is usually enough headroom for a new fact.

## What to delete outright

- Superseded entries describing the same system in older or wrong terms. Duplicate workflows are the most common source of waste — two entries, one reality, and future sessions cannot tell which is current.
- Credential VALUES. Keep the location and the rotation advice.
- Session narrative: what was built on which day, which ids existed before a rename.
- Environment-dependent failures that the user can simply fix.

## Batching mechanics

- One `memory` call with an `operations` array applies atomically; nothing is written if any operation overflows.
- `remove` needs a short unique `old_text` substring identifying the entry — not the full text.
- `replace` needs `old_text` to locate the entry AND the complete new text as `content`; it overwrites the whole entry, so re-include anything worth keeping.
- After a successful batch, do not re-issue it. The response reports current usage — check that number instead.

## Reading these files back for an audit

When the ask is 'check my memory files' rather than 'remember this', the deliverable is an
integrity report, not a write:

1. Confirm actual sizes against each file's budget and name which file is over.
2. Scan for leaked secret VALUES — pattern-match the usual key shapes, then remember that a rendered
   match may be the tool's redaction of a harmless string. Confirm any suspected leak with `od -c`
   on that line before reporting it.
3. Diff `USER.md` against `SOUL.md` and list every rule present in both; duplicated rules are the
   cheapest wins and should head the cleanup proposal.
4. Propose the consolidation as a batch and ask before writing — memory files are part of the
   operating setup, and the skill's standing rule is a numbered diff plus an explicit ask for
   changes the user has already vetted.
5. When memory keeps overflowing because project knowledge accumulates faster than the cap allows,
   the answer is not a bigger memory file but a second-brain directory (`second-brain-kb` if
   adopted): memory holds one pointer line per project, the KB holds the substance. Record that
   convention in the KB skill, not in memory.
6. When a `patch` fails to match the same anchor twice, stop reformulating the string — reload the
   file and inspect the exact bytes (`sed -n 'Np' file | od -c`) before writing again. A line that
   looks mangled in tool output is usually intact on disk; the mangling is display-time redaction,
   so every patch anchored on the rendered form will keep missing.

## Sanity check before finishing

Budget at 80–90 % is healthy. Above that, the next fact will fail, and the fix (a consolidation pass) costs more than maintaining headroom would have.