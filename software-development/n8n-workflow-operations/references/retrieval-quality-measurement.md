# Measuring a lexical retriever before recommending a fix

Applies when a Code node does bag-of-words retrieval over a knowledge base and
someone asks how to improve it ("add stemming?", "clean the column?", "the
search is bad"). The instinct is to write the fix and report the improvement.
Measure first — most suspected retrieval defects are not defects, and the honest
answer is frequently "reword the questions, not the code".

## Build a question set and a baseline

Ten to twenty questions a real user would type, with the inflected forms that
make retrieval hard, not the forms the base happens to use:

```
"какой зазор на свечах?"   "момент затяжки болтов ГБЦ"   "зазор клапанов"
"проверка компрессии"      "как проверить компрессию"     "замена ремня грм"
```

Re-implement the node's scoring offline (tokenize → per-record unique-token
intersection → sort desc, top 5) and print score + topic for each. Keep this
harness; every candidate fix is scored through it, before and after, and the
only metric that matters is **how many top-1 hits changed, and whether any got
worse**.

## Never build the probe set out of the base's own questions

The obvious way to get 300 test cases is to take each row's question, chop it to
its first few keywords, and use that as a probe. This measures nothing. The probe
is then a near-verbatim copy of the row it must retrieve, so *any* retriever
scores 95–98% and every comparison looks like a win.

```
probes from the base's own question column     286/300  (95%)
same retriever, probes built from topic words    2/8      (25%)
```

Build the probe set the other way: take the words from the row's **topic** (not
its question), or better, take questions from outside the corpus entirely — from
the user's own support history. If no external question set exists, say the
measurement is unavailable rather than substituting a self-referential one.

## Tune on one set, measure on another

Sweeping a weight grid and reporting the best score from the same rows used to
tune is overfitting, and with a small corpus it will pick a setting that looks
better on every query you can see and worse on the one you cannot. Split the
probes, or state the caveat in the same breath as the number.

## A genuine tie is an ambiguity problem, not a ranking problem

The decisive diagnostic: after every scoring variant, look at **how many records
share the top score**. When the correct rows sit at positions 2–3 *tied with the
wrong one*, no weighting separates them, because the discriminating feature
("rear wheel", "front wheel", "oil pan") is absent from the query — there is
nothing to weight.

```
"момент затяжки гайки ступицы"  score=4:  карданный вал
                                          приводные валы
                                          задние приводные валы   ← correct
```

Read that as a base-content problem (merge the near-duplicate rows so the tie
cannot exist) or an embeddings problem — never as a tuning problem. Weights on a
tied set only decide which of several wrong answers wins.

Weight grids are worth running precisely because they can refute your hypothesis:
theme-weight 1.0 → 286, 2.0 → 269, 3.0 → 228, TF-IDF → 274, TF-IDF plus
theme-disambiguation → 254. Monotonically worse as the theme weighs more, which
means the theme is already inside the haystack and re-counting it inflates
irrelevant rows. When the grid contradicts the idea, stop and say so.

## If every candidate fails, ship nothing and say that

The outcome this section exists to permit: measure, report that none of the
proposed fixes survived measurement, recommend leaving the retriever alone, and
name what would actually move it. A clean "the top-5 already contains the right
record and the model is instructed to reconcile sources — no change needed" is a
better result than a shipped degradation dressed as an improvement. The user's
question was how to improve the bot, not whether this session would ship code.

## Address rows by content, never by remembered id

Ids are not recallable and drift as rows are inserted and deleted. Every
bulk-rewrite pass must resolve each target by searching on topic or answer text
and printing the row it landed on:

```
guessed: id 132 "момент затяжки болтов ГБЦ?"
landed:  id 132  [Замена сальников коленчатого вала]
                         "Как заменить передний сальник коленвала?"
```

Three of eleven rewrites were aimed at seal, locknut and ABS rows this way. The
tell is cheap: assert that the target row's topic and answer share content words
with the edit you intend, and fail loudly when they do not. Do this **before**
assembling the write payload — the row is otherwise already staged.

## Rewrites measured against a stale baseline understate the gain

When a question-column rewrite lands, re-run the harness against the *post*-write
base, not the copy you edited in memory, and report both numbers. A rewrite that
looked like 5/11 before the write can read differently once the sheet is what the
pipeline reads.

## Structured identifiers need their own phase, not a longer word list

Codes, part numbers and error strings (`31`, `2-3`, `10-1`, `p0135`) are the one
class of query token that a length filter drops by construction: `length >= 3`
discards every bare number, so "код 31" reduces to the single word "код" and the
record holding the meaning of 31 ranks on generic SRS/ABS vocabulary instead.
Measured: the correct record sat at position 8 while four generic ones held 1–3.

**Do not lower the length filter.** It exists to drop short function-ish tokens;
removing it fills the top-5 with rows matching on particles. Add a second phase
that extracts the identifier from the query and matches the **whole string**
("код 31", "2-1") against the question/topic fields, with a bonus large enough to
outrank a word score (word score is bounded by question length, so 100 is safe).

Four pitfalls, each of which produces a patch that looks applied and returns
nothing:

- **`\b` is ASCII-only in JavaScript.** A regex written `/\bкод\s+(\d+)/` matches
  nothing, because there is no word boundary between Cyrillic and a digit under
  JS semantics. Use negative lookarounds instead: `(?<![a-zа-яё0-9])`. Symptom is a
  helper that returns `[]` for "код 31 ABS" while working for "SRS код 2-3" — the
  hyphenated form matched only because its own regex had no `\b`.
- **Strip compound codes before matching simple ones.** Extract `3-1` first and
  remove it from the working string, otherwise "код 2-3" also yields a spurious
  bare `2`.
- **The corpus writes the same code in two shapes.** Some records read "код 15",
  others "коды 2-1, 2-2, 2-3, 2-4, 2-5" — where the wanted number sits *after*
  other numbers. A pattern anchored to the word "код" matches the first shape and
  silently misses the second. Parse the enumeration after "код" and test
  membership, and accept the ellipsis form used in titles ("коды 2-1…2-5").
- **The same number means different things per subsystem.** Code 15 exists for the
  gearbox and for the fuel system. Require the subsystem word to co-occur, and
  **never match a bare number** — otherwise `195/65R15` and `R15` look like code
  15 and a tyre-pressure row wins. Look for the code adjacent to "код", and read
  only the question/topic fields: matching inside the answer pulls a code out of an
  unrelated long row.

Verify with two sets, not one: identifier queries (expect the matching record at
1–2) **and** questions that contain digits but no code (`"давление в шинах
195/65R15"`, `"момент затяжки 104 нм"`) to prove the phase stays inert. Report
identifier misses as *"no such code exists in the corpus"* only after grepping the
identifier across every record — an OBD rule that never fires is usually an empty
corpus, not a broken rule.

## A Russian suffix stripper does not work — and shipping one is worse than shipping nothing

Writing the obvious fix and testing it on word forms is the fastest way to learn
this:

```
проверка / проверить / проверки  ->  проверка | провер | проверки
замена / заменить / замены       ->  заме | замен
клапан / клапана / клапанов      ->  клапан | клапа
```

Russian stems change *inside* the root, not only at the end; a stemmer needs a
dictionary of stems, exceptions and a POS sense to know that `клапан → клапа` is
a noun losing its case and not a verb losing `-ть`. Snowball does this with
~200 lines and still mis-handles domain neologisms. A hand-rolled ending list
fails on 16 of 19 obvious form pairs. Do not ship one on the strength of the
word "stemmer".

**Run the stemmer through the harness before believing it fixes the miss.** A
root-truncating stemmer aimed at one real miss (`сбросить` vs `стереть`) does fix
it, and then rewrites ranking everywhere else. Measured on a 752-record base,
truncating to 4, then 5, then 6 characters, over an 18-question regression set:

```
stemmer  4 chars: target fixed, 44 of 50 top-5 positions moved
stemmer  5 chars: target fixed, 44 of 50 moved
stemmer  6 chars: target fixed, 42 of 50 moved
dictionary only:  target fixed, 29 of 110 moved, zero regressions
```

The regressions were not subtle. `замена свечей зажигания` promoted
`Предохранители — замена`; `отрегулировать клапаны` promoted `Настройка часов`;
`как снять двигатель` promoted `Блок управления двигателем`. Short roots fuse
unrelated words (`предохранители` → `пред`), so the extra matches are noise that
outranks the real answer. Raising the root length and down-weighting stem hits
(both tried) did not recover it — **measure, and if the only change that fixes
the target also breaks neighbours, the change is not the fix.**

A small hard-coded `{root: [forms]}` map is the version that survives
measurement. Build it by **counting the forms actually present** in the
question and topic columns first, then adding only those — not by listing every
form the language allows:

```python
for form in ["сброс","сбросить","стереть","стирание","очистить", ...]:
    n = sum(1 for r in recs if form in (r['question'] + ' ' + r['topic']).lower())
```

This is what surfaced that `замена` (29 rows) and `заменить` (10) do not
intersect, and that `сброс` (11) and `стереть` (5) are both real but rarer than
expected — the map should be sized by the corpus, not by the grammar.

**Check each dictionary entry for over-breadth before shipping it.** An entry is
not safe because its forms are real; it is safe only if no other sense of the
word coexists in the corpus. `настроить` was added to the `регу` group because
it is a legitimate synonym of `регулировать` — and it promoted `Настройка часов`
above the valve-clearance record, because that row also matched. Drop the
entry; a synonym the corpus never uses for this sense costs nothing to omit and
silently demotes a correct answer when included. Report the measured ratio
("29 of 110 positions moved, zero regressions"), never "search fixed".

## Word the base's question column the way users ask

When a miss comes from `затяжка` (participle) not matching `затяжки` (genitive),
the cheapest durable fix is the question text itself. If the row asks
"Как затягивать болты ГБЦ?" and a user asks "Какой момент затяжки болтов ГБЦ?",
rewriting the row to the latter matches on all three content words with no code
at all. Sweep the question column for rows whose wording does not match their own
topic, and prefer this over any code change. Recommend it as option A, the
dictionary as option B, embeddings as option C with its cost named.

Measured on this corpus: rewording seven rows moved top-1 from 2/11 to 5/11 with
**zero** regressions on eight unrelated queries. The remaining misses were rows
tied on score with the wrong answer — see the tie section above; rewording cannot
fix a tie.

## Cleanups are hygiene, not improvement — report them as such

Removing persona boilerplate (`Слушай сюда.` / `Поехали?`) from the answer column
is defensible as data hygiene: styling does not belong in a column of facts, and
the voice belongs in the system prompt, which already lists the catchphrases.
But run the before/after harness before claiming it helps retrieval. Measured
here: 151 rows cleaned, 3.9% of text freed, and **zero** change in top-1 or score
across ten queries — those tokens almost never appear in a user's question.

The same shape applies to any "clean the data" advice. What the cleanup buys is a
base whose columns mean one thing; what it does not buy is better answers. Say
both, so the user is not left expecting a quality jump.

## After any base or retriever change, close with one live run

Static verification says the rows are clean and the counts agree; only a real
execution proves the model was handed clean text. Send the bot a question whose
answer contained the artifact being removed (a `$`-wrapped value, an
inflected-form miss), then read the execution's `Search Knowledge Base` output
and the `Send a text message` payload and assert the artifact is absent in both
— the context you verified is not the same string the user received.

**A benchmark built only from questions that exercise your new code phase is a
blind spot, not a test.** The harness proves the phase you added works; it
cannot prove the phase fires when the query omits that phase's trigger word.
Measured: after adding identifier extraction, all ten code-shaped probes passed
and 15 unrelated queries showed zero movement — the retriever looked fully
fixed. The live run then asked `как сбросить ошибки abs?` with **no word "код"
anywhere**, so the new phase never ran, the answer stayed wrong, and the top-5
held records about tyres and brake feel. Always include probes whose shape
**omits** the trigger your fix keys on (`ошибки` instead of `код`), because a user
will phrase it that way without being asked to.

**Verify the live run is newer than your edit.** Compare the workflow's
`updatedAt` with the execution's `startedAt` — both in UTC. A run that started
before the write proves nothing about the write, and reading it as confirmation
manufactures a result you never tested. The gap here was small enough to be
mistaken for timezone skew.

**Read the context the node actually sent, not the harness's output.** The
execution's `runData["Search Knowledge Base"]` context is the ground truth for
"did the retriever help"; whether the *model* then answered correctly is a
separate check on the model and the prompt. Report them as two findings — a
correct retrieval with a wrong answer is a prompt problem, not a retriever one.

## Verify the persona survives the move out of the data

Before deleting stylistic text from a base, confirm the system prompt actually
carries the voice: read `options.systemMessage` and look for the catchphrases
listed explicitly. If they are there, the character survives; if not, the bot
goes clinical and the strip was a regression. After the strip, watch one live
answer — a model that used to copy a stock phrase and now must generate one may
simply drop it.