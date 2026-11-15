# Re-auditing a layer's completeness

Worked method for "подтяни остальное" / "finish the rest" against a manual-derived
layer. Proves extent first, then finds the real voids.

## Step 1 — Re-read the live corpus, not the session's cached copy

Read the current corpus (CSV dump or API), and inventory what exists after the layer
you are extending:

- record count, id range, max id
- per-source-page distribution of the layer you are extending
- the full topic list of the layer, so duplicates are visible

Assert the id set against the live base before planning any new ids — a previous
layer may already have landed above `1000` (see SKILL.md, id-collision rule).

## Step 2 — Map the source document's tables, not its chapters

A manual's extractable knowledge is a set of tables. List them by page:

| Table kind | Typical label | Landable as |
|---|---|---|
| Diagnostic codes | "Коды неисправностей" | one record per code family |
| Read/clear procedure | "Считывание кодов", "Сброс кодов" | one record per procedure |
| Connector voltages | "Напряжение на выводах блока управления" | one record per pin group |
| Test procedure | "Проверка давления", "Stall test" | one record per step |
| Condition lookup | "Поиск неисправностей по результатам теста" | one record per row |
| Specifications | "Основные технические данные" | one record per value |

Then diff this against the corpus per table. One pass per table, verdict is
present / partial / absent.

## Step 3 — Probe a table's absence with its own column headers

Extract the distinctive tokens from the table — pin designators, signal names,
connector labels — and grep the whole corpus for a sample:

```
header tokens: FL-IN, FR-OUT, R-IN, CHG, SCS, PARK, WARN1, WARN2, PMR,
               разъём "А", разъём "В"
```

- **Zero hits for every token** → the whole table is absent. Highest-value target.
- **Some hits** → partial; list which pins are covered and which are not.
- **Most hits** → covered; do not re-extract.

These designators are single-table vocabulary, so one pass settles the question.
Topic keywords (`abs`, `напряжение`, `проверка`) cannot: they hit unrelated records
and will tell you coverage exists when the table is a void.

Same idea for condition-lookup tables — probe with a value only that table contains
(e.g. `21,6 МПа`, `1-st hold`, `830-880` for a specific circuit) rather than with
the subject word.

## Step 4 — Rank by emptiness, present the plan, ask

Projected size for each gap, then order:

1. **Whole-table voids** — nothing in the corpus addresses this question shape.
2. **Partial tables** — the common rows exist, the tail does not.
3. **Missing procedures where a mention exists** — cheapest, lowest risk.

Report as a table (group, what is missing, pages, record count), name the top voids
explicitly, and ask whether to land the whole set or start with the voids. Do not
write first — same approval gate as any other corpus change.

## Step 5 — If the layer is already complete, say so

The honest answer to "finish the rest" is sometimes "there is nothing left in that
part." State which tables are fully covered, then redirect to the voids you found.
Inventing records to satisfy the request is worse than reporting a completed layer.

## Extraction notes

- Printed page number = PDF page index − 1 when the text layer starts on the page
  after the cover. Confirm by reading the footer/header line rather than assuming;
  a wrong offset makes every `source` citation point at unrelated content.
- Dump all pages to one JSON keyed by page number once, then read subsets from it.
  Re-parsing a 380-page PDF per probe costs minutes each time.
- Column tables extract as interleaved prose (`код — неисправность — место`), so build
  records from the row text rather than trying to slice columns.
