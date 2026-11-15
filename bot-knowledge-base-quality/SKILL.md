---
name: bot-knowledge-base-quality
description: "Audit and improve a bot's knowledge base corpus."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-base, rag, retrieval, data-quality, search, evaluation]
---

# Bot knowledge base quality

## When to Use

A bot answers from a structured corpus — a Google Sheet exported as CSV, a DB table,
a Markdown collection — through a retrieval node that scores records by token
overlap or embedding similarity. Use for: "why does the bot give a wrong answer",
"improve the knowledge base", "clean up the records", "make the search find the
right row", "the bot hallucinates / answers off-topic", or a request to remove a
class of records (a model, a variant, a superseded line).

Read-only audit first. Any write to the corpus is a data change to something
production serves — show the diff and get a yes, and back up before writing.

## The failure is almost never the ranking

Before tuning search, establish which of the two problems you have, because the
work is completely different:

- **Ranking problem** — the right record exists, the wrong one wins. Fix search.
- **Coverage problem** — no record exists for what is asked. Fix data. No
  retrieval tuning helps, and a beautiful ranking over a corpus that does not
  contain the answer still fails.

Distinguish them with one check: take five real questions the user would ask and
grep the corpus for records on each topic. **A hit count of zero is a coverage
gap, not a ranking miss.** Report that split before proposing any tuning.

A very common shape: the corpus is reference data (torque figures, dimensions,
part numbers) while the real questions are **symptom-shaped** ("stalls on the
road", "smoke from the exhaust", "how much oil"). Symptom→cause records are
absent, so the bot confidently quotes an unrelated specification. A retrieval
improvement is wasted motion until a diagnostic layer exists.

## Procedure

1. **Back up first.** Dump the full corpus to a timestamped file before any
   planned write, even read-only audits that may become writes.
2. **Read the corpus the way the bot reads it**, not the way the API serves it.
   If the consumer parses CSV, parse it with the consumer's parser and compare
   against a reference parser. A silent parser bug can hide hundreds of records
   and looks exactly like "the data is incomplete".
3. **Inventory**: row count, field completeness, duplicate questions, source
   coverage, and the length/format distribution of the answer field. Report the
   real numbers; do not characterize.
4. **Classify what is actually asked.** Harvest real user phrasings (see
   *Sourcing real questions* below) and test the current search on them.
5. **Fix coverage gaps before search.** Write the missing layer, sourced strictly
   from the reference material you already have.
6. **Only then tune search**, and only with a benchmark you did not build from the
   corpus.
7. **Re-verify through the consumer's view** and report before/after on the same
   benchmark, plus an explicit regression check on queries that already worked.

## The benchmark gate

**Never build evaluation probes from the corpus's own question column.** A probe
assembled from the words of record N is near-verbatim that record, so any
retrieval scheme scores 90%+ and the number says nothing. This failure mode is
silent and severe — it produced a confident "95% accuracy, tune from here" in a
session where the honest figure on real questions was 2/8.

Rules for a benchmark that means something:

- Probe text must be phrasings the corpus does **not** contain. Real user text, or
  words drawn from the *topic* field rather than the question field.
- **Never tune parameters and evaluate on the same set.** Grid-searching weights
  on the benchmark you will report is fitting noise; the winner is whichever
  setting best memorized those specific probes. Use separate tuning and reporting
  sets, or a held-out split.
- Report the number with its probe count and its construction. "12/20" on
  20 real questions is a finding; "286/300" on probes derived from the questions
  is not.
- Always run a **regression set** — queries that already resolved correctly —
  and assert none flipped. An improvement that quietly breaks prior answers is
  not an improvement.

## Search-tuning findings worth knowing before you try them

Measured, not assumed. Treat any of these as disproven until your own data says
otherwise:

- **A heavier weight on the record's topic/category field usually makes ranking
  worse.** Topic terms are already inside the scored haystack, so re-weighting
  inflates incidental matches. Monotonically worse as the weight rises.
- **TF-IDF re-weighting and topical disambiguation both scored below plain
  token-overlap** on a 658-record corpus. Reach for them only after the coverage
  gap is closed and a benchmark proves a specific failure they fix.
- **Ties are usually a symptom of near-duplicate records**, not of scoring. When
  the correct record sits at positions 2–3 with an identical score, the
  discriminator you are looking for is a qualifier that is absent from the query
  ("front" vs "rear", "2WD" vs "4WD"). Merging the near-duplicates into one
  record with a per-variant breakdown is a better fix than any scoring change.
- **Russian/Ukrainian inflection is not solvable with a suffix stripper.** The
  stemmer fails because the alternation is in the stem, not the ending
  (`клапан` → `клапа`). A hand-curated base-form dictionary works; a few dozen
  pairs covering the verb/noun families you actually see is enough.

## Sourcing real questions

Real phrasings are the only valid benchmark, and they are usually obtainable:

- **Forum/board threads are the best source** — thread titles are literally
  questions. Harvest via search with `site:` operators rather than trying to read
  the board's index page.
- When a site is behind a JS/interstitial bot wall and a direct fetch returns an
  interstitial, do not conclude the content is unavailable: search-engine snippets
  of `site:domain <topic>` return thread titles and fragments, which is enough.
  Note this in your report — the probe set is forum-derived, not owner-verified.
- When no source exists, **ask the user for their real questions** before
  writing a benchmark. A benchmark you invent measures your own assumptions, and
  reporting it as the user's quality is a misrepresentation.

## Forums are also a content source, not just a benchmark source

Once the coverage gap is confirmed, the same threads that supplied the phrasings
can supply the missing layer — and they are often the *only* place the diagnosis
exists, because manuals document procedures and specifications while owners
document what actually fixed the car. This closes gaps no amount of extraction
from the corpus can.

The failure mode is **cross-vehicle contamination**, and it is silent because
search returns the thread regardless of which car it is about. Before citing:

- **Confirm the thread is about the target variant from the post body — not the
  board, not the section, not the title.** A board dedicated to one model carries
  threads where owners post other cars into the same symptom discussion, and a
  search for the target model returns them.
- **Attribute advice per reply, not per thread.** In one thread the person asking
  owns the target variant while the person answering owns a later one, so the
  answer is advice about a different drivetrain. Grep each reply body for the
  vehicle its author declares.
- **Write the mismatch into the record.** When a diagnosis came from a
  non-target variant, keep the substance and add an explicit caveat naming the
  variant it came from and what may differ (wiring, torque values, component
  layout). Dropping the caveat turns forum hearsay into asserted fact for your
  exact car.
- **Label the provenance in the source field** (owner experience + URL vs the
  manual's own citation) and open the answer text by saying which kind of source
  it is. That is what lets the bot tell the user "the manual has no algorithm for
  this, but owners report X" instead of blending the two.
- Prefer findings where **two or more owners converge** on the same cause — that
  repetition is the only corroboration a forum offers.

## Verify every extracted claim against the source, mechanically

Whatever produced the new layer, no assertion goes in on the strength of your
reading. Assemble the layer in a **script** rather than by hand so numbers cannot
drift between the draft and the sheet, then run a list of distinctive fragments
(one per record) back through the raw extracted text and confirm each is present.

Because the record text is long prose held in Python string literals, the script
itself becomes a failure surface — and the errors are invisible in review because
each individual record reads fine. Lint the generated output mechanically before
any write, not by rereading it:

- **Mixed-script homoglyphs.** Latin letters substituted for Cyrillic inside a
  Russian word (`пagaснет`, `индикаторu`, `воспланимителя`) render as plausible
  words. Detect with a per-token script check (any token containing both scripts),
  not by eye.
- **Declension from shared constants.** Hoisting a shared phrase into a constant
  fixes the wording but freezes its grammatical case. A constant reading
  `внутренняя неисправность` spliced after `указывают на` yields
  `указывают на внутренняя неисправность` in every record that uses it, so the
  error repeats at scale and looks consistent enough to pass review. Keep the
  case in the call site, or make the constant carry its own verb frame.
- **Assert the id *set*, not the id count.** A malformed tuple in the literal can
  merge two records while the count still matches the plan, so a count assert
  passes while one record's body is gone. Compare the generated id list against
  the intended one element-wise.

Fix these in the script and re-run; never hand-edit the JSON the script emitted,
or the next run reintroduces them.

Expect **false negatives from line wrapping** and do not "fix" the record to match
the failed check — the source is right and your substring is wrong. Symptom of it:
the fragment is present but broken across a newline or hyphen (`э/м клапан управления\nдавлением`). When a check fails, search the raw text for the *words* with
surrounding context rather than the exact string; if the words are absent, the
record is wrong. When the check needs a fact that is only in the PDF, re-extract
from the PDF rather than trusting the earlier text dump — the dump may predate
the page range you widened to.

Two more ways a verification pass lies to you, both measured here:

- **Spaced table cells need whitespace-insensitive matching.** An OCR'd code
  column renders `9 - 1`, `2 -5`, `5 -1`; a phrase check like
  `"9-1" in text` fails while the record is perfectly correct. Strip all
  whitespace from both sides before comparing when the haystack is a code
  table.
- **Verify numeric claims by token, not by the phrases you remember.** A
  per-record phrase check only proves the fragments you thought to probe. The
  complete version extracts every numeric token from each generated answer and
  searches the whole extracted source for it (accepting the comma/dot
  `4,14` / `4.14` variants), then reports a count of unconfirmed numbers per
  record. It is one pass over the corpus and it catches a figure that drifted
  from the source while every prose fragment still checks out — which is exactly
  the class of error a sampling check misses. The one script output to distrust
  is a zero: confirm the tokeniser actually found numbers before believing that
  nothing is unconfirmed.
- **A damaged source row is a finding, not a blank to fill.** Scanned tables lose
  cells, and the gap usually sits in the row the corpus has no record for. When a
  value will not extract, write the *comparison procedure* the surrounding rows
  imply plus an explicit statement that the source gives no figure — never a
  plausible number. Same for a dash in a pin table: it means no specification
  exists, not that any reading is acceptable, and a record saying so stops the
  bot from inventing one.
- **Pin-designator records need the cross-variant trap stated inline.** Two
  variants in one manual carry *different* expected voltages for the same-named
  function — indicator pin reading zero on one and 4–6 V on the other, a
  fail-safe relay inverted between them. A record quoting only its own table is
  correct and still gets applied to the wrong car, so name the sibling's differing
  value in the answer.
- **Your own corrective wording re-arms the sweep that caught the defect.** After
  fixing "90 seconds → 3 minutes", the natural phrasing is "wait 3 minutes, not
  90 seconds as the base previously said" — which leaves the bad token sitting in
  the record, so the corpus-wide grep for the defect still reports a hit and you
  cannot tell a real leftover from your own explanation. Either state the correct
  value with no reference to the old one, or make the corpus-wide sweep exclude
  records whose hit is an explicit refutation.
- **A malformed literal silently merges records.** Editing a generated-records
  dict with `patch` broke a tuple's indentation and twice smuggled in homoglyphs;
  a stale-read guard then refused the rewrite, which is the tool working
  correctly. Recovery: delete the file, regenerate it cleanly, then gate on
  `ast.parse` plus the id-set assert before running. A count check still passes
  when a broken tuple merges two records, and the output reads clean because each
  surviving record is individually fine.

## "Подтяни остальное" means re-audit, not extract more

When the user asks for the remainder of a layer, treat the layer as **unverified** and
prove its extent before extracting anything further. The failure is announcing a
count ("65 records for five systems") and letting it stand in for coverage: one
record per code family is the recommended shape, so record count and coverage move
inversely — a complete table can be a dozen records, a partial one fifty.

The gap, when it exists, is usually **not more of the thing just built**. A completed
diagnostic-code layer leaves the procedures and specification tables *around* the
codes uncovered, and those are what a follow-up request is really about:

- connector/pin voltage tables (pin designators, signal names, expected volts)
- read/clear/road-test procedures where the corpus holds only a bare mention
- lookup tables keyed on a test condition (stall test → selector position → fault;
  pressure → selector position → clutch circuit), where the corpus holds only the
  test's headline numbers
- per-variant procedure and pinout tables, where only the primary variant was written

**Prove a sub-table absent by probing with its own column headers, not with topic
keywords.** A manual's tables are labelled with designators and signal names
(`FL-IN`, `FR-OUT`, `WARN2`, `разъём "А"`) that appear nowhere else in the document,
so a corpus-wide literal search for a handful of them settles in one pass whether
that whole table is missing, partially present, or fully covered. Topic-keyword
probes (`abs`, `напряжение`) answer a different question and will overstate coverage.

Enumerate the candidate gaps as a table — group, what is missing, source pages,
projected record count — and rank by **whether anything is there at all**, not by how
many codes are involved. Whole-table voids first: they are what a symptom-shaped
question ("ABS light is on", "Check Engine is on") actually retrieves against. Then
ask whether to land the whole set or start with the voids.

The per-table diff method, the header-token probe, and the page-offset check are in
`references/completeness-re-audit.md`.

A corollary for the report: say plainly when the layer turns out to be **already
complete**. "Пять таблиц DTC покрыты полностью, дотягивать нечего; дыры — в
процедурах и спецификациях вокруг них" is a finding, and it is the honest answer to
"finish the rest" — the alternative is inventing records to justify the request.

Rank the gap table by **whether anything is there at all**, and expect the
whole-table voids to be the ones a user question actually retrieves against
(`"ABS light is on"`, `"Check Engine is on"`). Two habits from landing such a set:

- **Scope the batch on the user's own instruction, then land it whole.** When the
  gap table is enumerated and the user answers "делай все", that is approval for
  the whole table — do not re-ask which group to start with, and do not land a
  subset. Approval of an enumerated diff covers exactly what was enumerated.
- **Prove each gap is still a gap immediately before writing, not at the start of
  the session.** A resumed or multi-batch session can have had a gap closed in
  between. Re-probe each candidate group against the corpus as it stands, and
  re-read the live sheet right before the append — a layer built against a stale
  local CSV duplicates records that already landed.

Then verify the write on three axes, because each catches what the others cannot:
numeric tokens confirmed against the source (above), no duplicate questions and no
id collision against the live corpus, and the layer read back through the
consumer's own view rather than the writer's API.

## A corpus record that cites the source can still contradict it

The most valuable output of a manual-derived audit is not the new layer — it is
the records that **misattribute** the manual. These share every surface property
of good data: filled fields, plausible phrasing, a `source` citation pointing at
the manual. Retrieval returns them confidently and the bot states them as fact.

Two shapes, both measured:

- **Fabricated meanings.** A code table lists `code 2 → front passenger airbag
  circuit`; the corpus says `code 2 → front left impact sensor`. Nothing in the
  corpus looks wrong in isolation, but the bot is now wrong about a safety
  system on a specific car.
- **A protocol attributed to the wrong variant.** A manual documents two
  procedures side by side — one for 4WD, one for 2WD, different parts, different
  steps — and a corpus record keeps only the one that reads most naturally while
  citing the wrong page. The owner follows it and the fault code does not clear.
- **A safety-critical numeric value that is simply wrong.** The most dangerous
  member of the family, because it survives every field check and nobody
  cross-checks a wait time against the precautions section. Measured: a corpus
  said wait **90 seconds** after disconnecting the battery before working on
  airbags where the manual says **3 minutes**, and capped the test meter at
  **5 V** where the manual caps output **current** at **10 mA** — a different
  quantity entirely, so the number looks plausible. Both sat in four records
  each, one of them sourced from the owner's manual rather than the repair
  guide, so a sweep scoped to one document misses the sibling copies.

Detect both by building an explicit `code → meaning` map straight from the table
and diffing it against what the corpus claims, record by record.

**Prove provenance by whole-document term absence.** Do not settle for "the table
disagrees" — scan every page of the source document for the *exact term* the
corpus uses. A term with **zero** hits across the full document is decisive: the
record did not come from this source at all, so there is no page to re-cite and no
reason to hunt for a misreading. That converts a judgement call about which
number is right into a fact about where the data came from, and it is a cheap
single pass. Corollary: when the cited pages exist but hold unrelated content
(removal procedures where the record claims a code table), the corruption is in
the *whole edit batch* from that source, not in the one record — which tells you
how many more rows to expect to be wrong.

Report as a numbered diff with the manual's version beside the corpus's, then
**stop and ask**.
Do not fold the correction into the write you already planned: these are
production records, their provenance may be a source you have not seen, and
replacing someone's manual citation with your own reading of the same manual is
a decision the corpus's owner makes. Batch the whole fix into one approval pass
with the layer, and note the `source` citations that point at pages the document
does not contain — that pattern usually means a second, older edition fed the
original extraction.

For the rewriting stage — turning a confirmed-bad row into a sourced one, marking
rows whose provenance you cannot confirm, and the verification passes that produce
false verdicts — see `references/source-correction-pass.md`.

## Writing records for a diagnostic layer

When the gap is symptom→cause rather than reference data:

- Anchor every new record to **specific existing records** and keep the anchor ids
  in a field or comment. Verify all anchors resolve and that each is topically
  relevant — a plausible-looking id is how unrelated records get cited.
- **Lift figures verbatim** from the anchors. Do not recompute or round.
- **Where the reference material has no answer, say so in the record text.** A
  record reading "the manual does not cover this cause; the base has no
  algorithmic answer" plus whatever adjacent facts DO exist is far more useful
  than a plausible diagnosis, especially when the bot's prompt forbids invention.
  This is the difference between a bot that admits a gap and one that confidently
  misleads.
- Use the user's own vocabulary in the question field, including the colloquial
  and misspelled forms the corpus's own questions never use.
- **Space new ids away from existing ranges and assert no collision.** Also
  remember that a re-layer can collide with the base you are layering onto: a
  first pass added a diagnostic block, and the next pass that started at `1001`
  needed a fresh check against *all* existing ids, because the first block had
  landed at `901-936` and would have been silently overwritten. Assert the id set
  against the live base every time, not just the first time.
- **Group by the code family, not one record per code**, when the table does.
  Forty sibling codes whose entries differ only by wheel position or by which
  circuit failed share every other token, so as forty records they compete with
  each other and the only thing distinguishing them — the number — is the token
  the tokenizer is most likely to drop. One record per family with the number
  mapping inside the answer wins on real queries and is what a human would read
  anyway.
- **State the cross-variant trap explicitly in the answer.** When the same code
  number means different things on different variants, say so in the record that
  answers it ("same number on 4WD means X, on 2WD means Y"). Otherwise the bot
  retrieves the right record and cites it for the wrong car.
- **Know whether the retrieval can even see your codes.** Many tokenizers filter
  on minimum token length or word shape, which silently drops bare numbers
  (`31`, `2-3`). Test a probe consisting of a code and a subsystem word; if the
  layer lands at position 8+ while old records sit at 1–3, the barrier is
  tokenization, not the layer's wording — and shortening `topic` will not fix it.
  Check this before spending effort on question phrasing.
  Shortening the topic is in fact a **regression** for codes: the only field where
  the number sits beside the word "код" is the title, so keep that adjacency and
  trim only the redundant middle. The barrier itself is a retriever change — see the `n8n-workflow-operations`
  skill, "Structured identifiers need their own phase" in its retrieval reference.
- **Record the page the claim is actually on, and admit when the source is
  silent.** When the manual has no sentence for a record's assertion, do not
  paraphrase the nearest implication as though cited — say what the source does
  say and mark the conclusion as derived. Two shapes to avoid: turning a
  prohibition ("do not disassemble") into a positive rule the manual never states
  ("replace the deployed unit"), and restating the wrong number from the corpus
  inside the clause that corrects it. "The manual does not state this directly,
  but forbids X, therefore Y" is defensible; asserting Y with a page number is
  not.

## Data-cleaning rules

- **Persona/stylistic scaffolding in the data field is a hygiene problem, not a
  search problem.** Measure its search effect before claiming a win — two or three
  common words that never appear in questions usually changes nothing. Its real
  justification is that style belongs in the prompt, and that non-factual tokens
  dilute relevance scoring. Report the measured effect honestly, including
  "no measurable ranking change".
- **Formatting artifacts from a PDF import** (`$...$` math, `{,}5` decimal commas,
  `\text{unit}`, escaped quotes) must be cleaned at the source, and the converter
  must refuse to apply a record whose output still contains markup rather than
  writing a half-cleaned record.
- When converting, **verify numbers survived**: compare the multiset of numeric
  tokens before and after, and investigate every difference. Expect false
  positives from re-parsing (`16\pm2` read as `162`) and confirm each individually.
## Look up record ids by topic, never from memory

Guessing ids and writing before checking that the question and topic at that id
agree will corrupt unrelated records. This happens when you draft an edit list,
discover a problem in the list, and keep patching it — the surviving rows still
carry the ids you invented. Two habits prevent it:

- **Find every target by searching the corpus for its topic or answer content**,
  then read the question↔topic pair at the id you found. Verify that pair agrees
  for every row you will touch.
- **Assert non-interference on the fields you did not intend to change.** Before
  sending, check that `topic`, `answer` and `source` are byte-identical to the
  re-read for every row except the ones whose `question` you deliberately
  rewrote. A clean assert here is what catches a mis-mapped id; a diff you skim
  will not.
- Build the payload from a body fetched immediately before assembly, not from a
  copy read earlier in the session, or a re-fetch silently reverts earlier fixes.
- Re-read the whole corpus after the write and grep for the **defects you just
  removed**, not only for the records you touched: a corpus-wide sweep for the
  fabricated term and the misattributed protocol confirms the pattern is gone from
  every row. Per-row checks cannot tell you whether sibling records from the same
  bad batch were left behind.

## Approved corrections are still a separate pass from the layer

Once the user approves a misattribution fix, it does not merge into the write you
already had queued. Keep them as two payloads with two backups, and land the
correction first — a layer written on top of uncorrected records leaves the
contradiction live and, worse, the new layer competes with it for the same query,
so the wrong record can keep winning the ranking. After correcting, re-run the
ranking probe for the affected subsystem: correcting the record does not
guarantee it now surfaces, because whatever beat it before may still be ahead of
it.

## Fix the question wording in the same pass as the retriever fix

A mis-wording defect looks like a retrieval defect and survives any amount of
retriever work. The row answering "how do I clear the ABS codes on 4WD" is
phrased with *«стереть»* while its own topic says *«сброс»*, so a user typing
«как сбросить ошибки abs?» matches the topic, misses the question, and the
top-5 fills with rows about tyres and brake feel. Symptom to recognise it: the
correct row's **question** does not share a content word with the user's
phrasing, while the **topic** does.

Two halves, and they are independent — do both:

- **Retriever:** a synonym dictionary keyed on the forms actually present in the
  question and topic columns, which makes the two phrasings intersect.
- **Data:** rewrite the question to the phrasing users use, and include *every*
  colloquial noun they reach for (`сбросить коды **и ошибки** неисправностей`) —
  the extra synonym costs a few characters and covers the case where the
  dictionary does not fire at all, which is what happens whenever the query
  contains none of the mapped trigger words.

When you find this in a live execution, it is a **user-reported miss you have
not yet reproduced**: say so, add the trigger-less phrasing to the benchmark
first, and treat a pass on the earlier benchmark as no evidence about it. Why
shipping a general stemmer for a single phrasing miss is the wrong fix is
measured in the `n8n-workflow-operations` skill, under its retrieval-quality
reference.

Keep the wording pass in the same write as anything else you have queued for
that subsystem, with its own backup — it is the same class of production data
change and splitting it leaves the corpus half-fixed between sessions.

## Reporting

- Lead with the coverage/ranking split — it reframes the whole task.
- Give before/after on a named, honestly-constructed benchmark, with the
  regression count.
- List what you could not verify and why (no live run, token rotated, no real
  question source).
- State the residual gaps as data work, not as tuning work, and name what input
  would close them — usually the domain owner's own experience.
- If tuning attempts failed, report the failed approaches as failed. Do not
  dress up the best of several bad options as a recommendation.

## Stop and name it when the corpus is answering the wrong question

This audit is worth running before any data cleanup at all. A corpus can be
fully clean — no duplicates, no markup artifacts, no persona scaffolding, no
formatting residue, every field populated, and every record individually
correct — while the bot still fails, because the corpus documents the wrong
*kind* of thing. Reference values are what a manual publishes; what owners ask is
symptoms. When the topic distribution is dominated by one subsystem's
specifications while the real question set is symptoms across many subsystems,
cleanup is wasted motion: it improves records nobody queries.

Say this plainly rather than delivering the cleanup and letting the unchanged
behaviour stand as evidence the cleanup worked. When the user has an owner of the
machine in the loop, the honest close is that the remaining input is their own
experience for the specific symptoms the corpus cannot answer.