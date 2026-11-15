# Source-correction pass

Depth for the stage after whole-document term absence has proven a record came
from a document you do not have. Read this when you are about to rewrite
confirmed-bad rows, decide what to do with rows whose provenance is unknowable,
or write the generator script for the correction.

## Three corruption shapes, not one

All three have filled fields, plausible phrasing, and a `source` citation pointing
at the manual. Retrieval returns them confidently and the bot states them as fact.

- **Fabricated meanings.** The code table lists `code 2 -> front passenger airbag
  circuit`; the corpus says `code 2 -> front left impact sensor`. Nothing in the
  record reads as wrong on its own, but the bot is now wrong about a safety system
  on a specific car.
- **A protocol attributed to the wrong variant.** The manual documents two
  procedures side by side - one for 4WD, one for 2WD, different parts, different
  steps - and a record keeps the one that reads most naturally while citing the
  wrong page. The owner follows it and the fault code does not clear.
- **A safety-critical numeric value that is simply wrong.** The most dangerous
  member of the family, because it survives every field check and nobody
  cross-checks a wait time against the precautions section. Measured: the corpus
  said wait **90 seconds** after disconnecting the battery before working on
  airbags where the manual says **3 minutes**, and capped the test meter at
  **5 V** where the manual caps output **current** at **10 mA** - a different
  quantity entirely, so the wrong number still looks plausible.

Detect the first by building an explicit `code -> meaning` map straight from the
table and diffing it against what the corpus claims, record by record. Detect the
third by cross-checking every safety value against the precautions section, not
only against the table it happens to sit near.

Scope by **the whole corrupted batch, not the batch you happened to audit.** Term
absence proves every record drawn from that source is suspect. One pass aimed only
at the code table turned 8 confirmed rows into 19 - the precaution and voltage
records from the same phantom document were wrong in different ways, and one was
sourced from the owner's manual rather than the repair guide, so a sweep scoped to
one document misses it.

## Never launder an inference into a citation

When you rewrite a record from the source, every sentence in it must be something
the source says. The tempting move is to help the user by adding the obvious
conclusion - the manual forbids disassembly and forbids parts from another car, so
writing "these nodes cannot be repaired, replace them" reads as helpful. But the
manual never states it, so the record now cites the manual for a claim the manual
does not make, which is the exact defect you are in the middle of fixing.

Write the prohibitions verbatim, then mark the inference as yours:

> The manual does not state this outright, but it forbids X and Y. Consequence:
> the node is not repairable.

Watch the units. If the corpus restricts one quantity and the manual restricts
another (voltage vs current), say so explicitly rather than restating the number
under the new label - "the limit is on current, not voltage" is correct and
legible; silently swapping the quantity teaches the user a rule the manual does
not have.

## Records whose source you cannot confirm: mark and keep

Once term absence has proven a record came from a document you do not have, do not
delete it and do not pretend the citation is fine. Prepend a provenance warning to
the answer text and replace the `source` field with the finding itself:

> SOURCE NOT CONFIRMED: the repair manual used for this corpus contains no
> procedure for <what is missing>. The figure below comes from a different source
> and is not verified here - check the manual for your car.

Keep the value. It may well be correct, and the owner's own reference is worth more
than a gap. The retrieval node's prompt forbids invention, so a record that opens
by declaring its own provenance makes the model answer "the base does not confirm
this" instead of stating the number as fact. Offer the user the three real options
- keep with warning, delete, or supply the other document - and take the answer;
this is the corpus owner's call, not yours.

## Verification passes that lie to you

All three of these produced confident wrong verdicts in one session.

**Line wrapping and hyphenation.** The fragment is present but broken across a
newline (`э/м клапан управления\nдавлением`). Do not "fix" the record to match the
failed check - the source is right and your substring is wrong. Search the raw text
for the *words* with surrounding context. If the words are absent, the record is
wrong. When a fact exists only in the PDF, re-extract from the PDF rather than
trusting the earlier dump, which may predate the widened page range.

**Spaced table cells.** An OCR'd code column renders `9 - 1`, `2 -5`, `5 -1`, so a
phrase check like `"9-1" in text` fails while the record is perfectly correct.
Strip all whitespace from both sides before comparing when the haystack is a code
table. Try progressively looser comparison before concluding the record is wrong -
whitespace-only, then case-folded, then punctuation-stripped.

**Your own corrective wording re-arms the sweep that caught the defect.** After
fixing "90 seconds -> 3 minutes", the natural phrasing is "wait 3 minutes, not 90
seconds as the base previously said" - which leaves the bad token in the record, so
the corpus-wide grep for the defect still reports a hit and you cannot tell a real
leftover from your own explanation. Either state the correct value with no
reference to the old one, or make the sweep exclude records whose hit is an
explicit refutation.

## Do not trust a hand-typed generator dict

Editing a generated-records script with `patch` broke a tuple's indentation and
smuggled in homoglyphs twice in the same file. A stale-read guard then refused the
rewrite, which is the tool working correctly. Recovery that worked: delete the file,
regenerate the dict cleanly, then gate on `ast.parse` plus the id-set assert before
running.

Re-validating syntax is not ceremony here. A malformed tuple can merge two records
while every count check still passes, and the output looks clean because each
individual record reads fine. Three traps in the dict form:

- **Declension from shared constants.** Hoisting a phrase into a constant fixes the
  wording but freezes its grammatical case. A constant reading `внутренняя
  неисправность` spliced after `указывают на` yields `указывают на внутренняя
  неисправность` in every record using it, so the error repeats at scale and looks
  consistent enough to pass review. Keep the case at the call site.
- **Mixed-script homoglyphs.** Latin substituted for Cyrillic inside a Russian word
  (`пagaснет`, `индикаторu`, `воспланимителя`, `componentes`) render as plausible
  words. Detect with a per-token script check, not by eye. Also grep for the
  replacement-character glyph, which appears when a patch introduces a broken
  codepoint.
- **Assert the id *set*, not the id count.** Compare the generated id list against
  the intended one element-wise.

Lint the generated output before any write, never by rereading it.