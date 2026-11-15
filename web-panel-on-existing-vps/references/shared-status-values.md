# Shared status values: one writer, many silent readers

A state machine whose transitions are written in one place and read in five fails
*quietly*. No error, no failed request, no log line — just a panel that is always
empty and a system that looks healthy.

## The shape of the bug

A booking row moves through states. Exactly one node writes them:

```
"Supabase: UPDATE lock"   status -> "locked"
"Supabase: expire старых"  status -> "expired"
"Supabase: Insert"        status -> "available"
```

Every reader is a *separate* piece of code that spells the state differently, and
each wrong spelling produces the same symptom — an empty view:

| Reader | Wrong value | Why it looks fine |
|---|---|---|
| "Кто записался" list | `status = booked` | empty list |
| Day view | `status = booked` | every row shows "свободен" |
| Time-slot grid | `status = booked` | no button ever greys out |
| Cancel endpoint guard | `status = locked` | 409 on a real booking |

## Procedure

1. **Find the writers first, and treat them as the schema.** Search the workflow for the field name, not the value:
   ```
   grep -o "'(available|locked|booked|expired|cancelled)'" <workflow json>
   ```
   Two workflows writing the same column with different vocabularies is the same bug one layer up.

2. **Grep every reader for the literal, not for the concept.** A reader that filters on a *timestamp* (`booked_at IS NOT NULL`) is a different reader again and will not show up in a search for status words.

3. **Fix all readers in one pass.** Partial fixes leave a panel where the list shows a booking but the grid offers the same slot, which is worse than a uniformly empty view because it invites a double-booking.

4. **Distinguish the two empty states.** "The writer never ran" and "the reader filters on the wrong value" look identical from the UI. Prove which by querying the table directly and comparing to what the reader asks for:
   ```
   rows exist with status=locked   +  reader asks for booked   -> reader bug
   no rows at all                                     -> writer never ran
   ```

## Why it costs so much when it slips through

The failure is invisible to every automated signal: the write returns 200, the read
returns an empty list rather than an error, and an execution-status dashboard shows
all-success. Only a human looking at the panel notices. So when adding a new reader
for an existing state machine, treat the status string as an interface — import it
from one place if the language allows, and when it does not, leave a comment on
each reader naming the node that writes the value.

## Adjacent trap: a value with no writer

The mirror image is a state nothing ever sets. A UI filter on a state that only a
future feature will produce reads as "no bookings have happened yet" indefinitely —
and gets mistaken for a data problem rather than a missing writer. Before filtering
on a state, confirm something actually transitions into it.