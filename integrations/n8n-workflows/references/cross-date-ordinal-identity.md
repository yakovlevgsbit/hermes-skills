# When one lookup key must span several groups (dates, rooms, categories)

The single-date ordinal contract in `display-ordinal-and-date-format.md` assumes
every printed number is resolved against the same collection. Multi-date publishing
breaks that assumption, and the failure is invisible on the happy path.

## The ambiguity is structural, not a missing filter

A booking bot that prints one list per date and accepts a bare digit CANNOT resolve
the digit to a date. The bot receives `2` and has no signal for which list that is —
the number is identical in every list:

```
📅 10.05   1. 10:00   2. 15:00     Ответь цифрой: 1, 2
📅 10.06   1. 14:00   2. 16:00     Ответь цифрой: 1, 2
```

So a client replying to the 10.06 list can land on a 10.05 slot. Adding
`date = <lookup date>` to the SELECT does not fix it — there is no lookup date to
filter on. Recognise the dead end before spending an attempt on it.

## Two platforms, one slot: check for a hard one-pin limit first

Before designing per-date posts, verify how many pinned messages the chat platform
allows. MAX permits exactly **one** pinned message per chat: `PUT
/chats/{chatId}/pin` takes a single `message_id`, `GET /chats/{chatId}/pin` returns
one object, and a `message_ids` array answers `400 Field 'messageId' cannot be
null`. So per-date posts mean each publish silently replaces the previous pin, and
the group loses access to the earlier dates.

The durable shape is therefore **one message covering all groups**, edited in place:

```
🗓 Свободные слоты
📅 10.05
🟢 1. 10:00 – 11:00
🔴 2. 15:00 – 16:00 (занято — Евгения)

📅 10.06
🟢 3. 14:00 – 15:00
🟢 4. 16:00 – 17:00

Ответь цифрой: 1, 3, 4
```

Numbering runs **continuously across every group** (day 1 → 1, 2; day 2 → 3, 4). A
per-group restart at 1 is what makes the digit ambiguous in the first place.

## The numbering pool must include terminal-but-live rows

This is the invariant that makes the numbering stable, and it is easy to get
backwards. The pool that assigns numbers must contain every row that should hold a
number — including rows already booked:

```
pool = rows where status != 'withdrawn'      // includes 'locked'
```

If the pool is `status = 'available'`, then the first booking removes a row, the
pool shrinks, and **every subsequent digit shifts by one**:

```
message says   1. 10:00   2. 15:00   3. 14:00
client types 1 -> 10:00 booked, leaves the available pool
client types 2 -> pool is now [15:00, 14:00]  ->  2 resolves to 14:00  ❌
```

Availability is a separate predicate applied at lookup time (`status ===
'available'`), never a filter on the numbering pool. Withdrawn rows are the only
ones excluded — they are gone, and leaving them in would hand out numbers nobody
can match.

**Prove stability by simulation, not by reading the code.** Seed the rows, print the
numbering, book one row, print the numbering again, and diff. Any movement is the
bug. The same check catches the reverse case: a withdrawn row must disappear from
the pool, or the message advertises a number the lookup will never resolve.

## The repaint window must start at TODAY, not at the booked date

The merged message has to list every upcoming date, so the node that gathers rows for
it cannot filter on one date. The tempting fix — anchor the window to the date of the
booking that triggered the repaint — is wrong and fails in a way that looks like data
loss:

```
book a slot on 06.10  ->  filter date >= 06.10  ->  every earlier date vanishes from
the pinned message the moment a later date gets booked
```

The user reports "when the client takes a slot on the 6th, the 5th disappears from the
pin" — the rows are intact, the window simply no longer covers them. Anchor the window
to the current day in the instance timezone, and expose that value from an upstream node
so both the filter and any downstream logic read the same string. A `date gte <today>`
filter on the repaint read is what keeps all future dates in view while still excluding
past ones.

Check this one specifically after any multi-date publish: book the LATEST date, then
confirm an EARLIER date is still present in the rendered message.

## One numbering function, three call sites

When the message is rendered in more than one place — a workflow node that publishes,
a second node that repaints after a booking, and a separate panel/service that also
rewrites the text — the numbering logic must be identical in all of them, or the
printed digits and the resolved digits diverge per surface. Write the rule once,
name the shared ordering key (`start_time`, never a per-post index), and keep a list
of the call sites in the runbook so a future change updates all three.

## Offline assertion before deploying

Feed every printed number back through the real lookup code:

- each free row → resolves to the row that printed that number;
- a booked row → `not_found`, and its number absent from the footer;
- a withdrawn row → absent from both the list and the numbering pool;
- a number from one date never resolving to a slot on another date.