# Workflows that fetch and parse external data

Applies whenever a Code node consumes a blob fetched by an HTTP node — a Google
Sheet exported as CSV, an API JSON dump, an HTML table — instead of a typed n8n
data node. The failure mode is silent and expensive: the parse returns a
plausible result that is a fraction of the truth, and every downstream
recommendation built on it is wrong.

## The core failure: one malformed record blinds everything after it

A hand-rolled CSV parser that treats any `"` as a quote delimiter will, on the
first field containing a stray quote, stop splitting commas and newlines. It
does not crash. It returns one mega-row and drops every record that followed.

```
stuck record:  ... answer: Метка"<” на поршне ... метка"11" ...
result:        175 records parsed, 537 silently dropped (75% of the dataset)
```

The tell is a column-count histogram: one row with hundreds of columns among
rows that should all have the same count. Print it every time you parse.

```js
const cols = {};
for (const r of recs) cols[r.length] = (cols[r.length] || 0) + 1;
console.log('column histogram:', JSON.stringify(cols));
```

## Assert yield against the authority, never against your own pipeline

A retriever's own output is not evidence about the source. When advising on
coverage, quality, or what to add to a knowledge base, count via the
authoritative API (Sheets `values` endpoint, the DB REST endpoint, the vendor
API) and compare against what the pipeline actually yields.

Reporting "codes, diagnostics and starter motor are absent from the base —
6 records" when the real base holds 537 more records is a wrong recommendation
built on a broken parse. Fix the parser first, re-count, then advise.

## Rule to implement: quote is special only at field start

RFC 4180 semantics, which most hand-rolled parsers skip:

- a `"` **only** opens a quoted field if the field is still empty;
- a `"` **inside** an already-started unquoted field is an ordinary character;
- inside a quoted field, `""` is one escaped quote;
- `CR` is skipped unconditionally, so CRLF and lone CR do not create rows.

Track two booleans, `fieldStarted` and `inQuotes`. Do not infer "am I quoted?"
from the character alone.

## Prove the fix against two independent oracles

Do not validate a parser against itself. Before shipping:

1. the new parser, run offline on the real fetched payload;
2. the same payload through an authoritative RFC-4180 reader (Python
   `csv.reader`);
3. both against the live source via its own API read path.

All three must agree record-for-record, including the header row — drop the
header consistently on both sides or you will diff one row out of alignment and
misread it as 700 field mismatches. Then confirm the specific records that
exposed the bug parse correctly, and the last record in the file.

Extract the function from the **live workflow after the PUT** and run that, not
the local draft — this catches a PUT that did not land or a payload built from a
truncated read.

## Google Sheets: writing from n8n-adjacent tooling

Read path used by such workflows is usually the public export
(`/gviz/tq?tqx=out:csv`), which is read-only and needs no auth. That path cannot
prove record count against the API, because it truncates and re-quotes; the
`values` endpoint is the truth.

Write path (service account):

1. Build a JWT assertion: `iss` = `client_email`, `scope` =
   `https://www.googleapis.com/auth/spreadsheets`, `aud` = `token_uri`,
   short `exp`. Sign RS256 (`pyjwt` + `cryptography`, both usually present).
2. Exchange at `token_uri` with
   `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer`. Token lasts ~1h —
   cache it, do not re-mint per call.
3. `GET https://sheets.googleapis.com/v4/spreadsheets/{id}` for the sheet title
   and `protectedRanges`. A protected range silently caps what you can write.
4. `GET .../values/{SheetName}!A1:F1000`. **The response key is `values`**, with
   `range` and `majorDimension` alongside — not `valueRanges` (that is the
   `batchGet` shape). Non-ASCII sheet names work unencoded.
5. Back up the full sheet to disk before the first write.

### Writing the new table, and trimming the leftover tail

Deleting rows means the new block is shorter than the old one, so a plain
values write leaves stale rows below it and the base still parses. Trimming is
the fiddly part; these shapes work, the others do not:

- Write payload is `{"range": "Лист1!A1", "majorDimension": "ROWS", "values":
  [[...]]}` — the wrapper key is required. Posting a bare array returns
  `Invalid JSON payload ... Root element must be a message`.
- **`values:clear` is not usable.** Every documented form of it returned an
  error here (404 from the front end when the range was in the query and the
  sheet name was non-ASCII, 400 on a body carrying `range`). Do not spend
  turns on it.
- **`deleteRange` needs an explicit dimension and rejects extra fields.** It
  answered `No dimension specified` even with a complete GridRange (all four
  bounds), and rejected `dimensions` and `inheritFromBefore` as unknown names.
- **What works: blank the tail with `updateCells`.** Overwrite the leftover
  rows with empty `userEnteredValue` cells:

```python
n_tail = old_rows - new_rows
fields = [{"userEnteredValue": {}}] * (n_tail * ncols)
req = {"requests": [{"updateCells": {
    "range": {"sheetId": sid,
              "startRowIndex": new_rows, "endRowIndex": old_rows,
              "startColumnIndex": 0, "endColumnIndex": ncols},
    "rows": [{"values": fields[i*ncols:(i+1)*ncols]} for i in range(n_tail)],
    "fields": "userEnteredValue"}}]}
```

`sheetId` comes from the spreadsheet metadata and is **not** the sheet's
display index. Returns 200 with empty `replies`.

Always re-read afterwards and assert on non-empty row count, not on the write's
own success — after trimming, re-`GET` the range and check that the last
non-empty row is exactly the last row you wrote.

The service account must be shared onto the sheet as **Editor**. Sharing is a
separate step from key creation and is the usual reason a valid key 403s.

Service-account keys grant access to every GCP project where the account holds a
role; treat them as revocable and get them back out of the working directory
afterwards.

## Also check on the data, not just the parse

Once rows parse correctly, two artifact classes usually surface and belong to the
data, not the code:

- **LaTeX leakage.** Rows converted from PDFs carry `0{,}08`, `\text{мм}`,
  `\cdot`, `$...$`. A model handed these forwards them verbatim into chat. Clean
  the column as data, and gate the conversion on a residue check so no row is
  written with markup left in it. See `references/latex-column-cleaning.md` for
  the two traps that yield a clean-looking run with wrong numbers, and for the
  residue assertion that catches them.
- **Persona boilerplate baked into data.** Stylistic catchphrases inside the
  `answer` column consume tokens during retrieval and pollute scoring with
  content-free words. Move voice into the system prompt.

## Voice/persona in the system prompt must survive a thin base

When an agent is told "never invent, always defer to the provided base", and
the base is silently truncated, the model does not fall silent — it answers from
general knowledge while believing it is grounded. A retriever defect therefore
shows up as *confident fabrication*, not as an error. Treat a grounding claim as
unverified until you have counted what the retriever actually returns.