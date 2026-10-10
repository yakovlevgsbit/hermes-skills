---
name: google-sheets-writes
description: Use when writing to a Google Sheet via API v4.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [google-sheets, api, oauth, service-account, csv]
---

# Google Sheets API v4 writes

## When to Use

Writing to a Sheet that a bot or workflow reads (gviz CSV export, API reads, CSV
imports). Also for bulk edits where a row-count change is part of the task —
deleting rows is the part that breaks.

## Setup

Sign a JWT assertion for the service account and exchange it for an access token.
No `gspread` needed; `pyjwt` + `cryptography` are enough. The token lives ~1h —
re-sign when a call returns 401 mid-task.

```python
import json, time, urllib.request, urllib.parse, jwt
key = json.load(open("/root/.secrets/google.json"))
now = int(time.time())
claims = {
    "iss": key["client_email"],
    "scope": "https://www.googleapis.com/auth/spreadsheets",
    "aud": key["token_uri"], "exp": now + 3600, "iat": now,
}
a = jwt.encode(claims, key["private_key"], algorithm="RS256")
d = urllib.parse.urlencode({
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": a,
}).encode()
tok = json.loads(urllib.request.urlopen(
    urllib.request.Request(key["token_uri"], data=d), timeout=30).read())
```

**Prefer the library over a hand-rolled JWT when it is already importable.** If
`google.oauth2.service_account` and `google.auth.transport.requests` are available
in the interpreter, they are strictly less code and immune to claim-scoping
mistakes:

```python
from google.oauth2 import service_account
from google.auth.transport.requests import Request

creds = service_account.Credentials.from_service_account_file(
    "/root/.secrets/google.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
creds.refresh(Request())
tok = creds.token          # use as Bearer for the values API
```

**A valid access token still 403s if you forget the header.** After `creds.refresh()`,
send `Authorization: Bearer <token>` on every request; without it Google answers 403
even though the credential is perfect, which reads as a permissions problem and sends
you off to re-share the sheet for no reason. Verify the header, then the grant.

The service-account key belongs in the credentials vault, not next to the script or in
a scratch dir — see the `service-credentials-vault` skill.

**Refresh per write batch, not per session.** A token saved hours earlier is the
usual cause of a 401 on an otherwise identical request that worked before; a 401 on
the values endpoint means re-sign, not "the sheet is read-only".

Scope matters: `spreadsheets` for values/batchUpdate, `drive` for file-level ops.
Also verify the service-account `client_email` has actually been granted access on
the Sheet ("Share" → Editor). A valid token with no grant still reads nothing.

## Read the sheet first, and read it twice

`values.get` returns **`values`**, NOT `valueRanges` — `valueRanges` is the
`spreadsheets.get` shape. Keying off the wrong one raises `KeyError: 'valueRanges'`
and looks like an empty sheet.

Reading the sheet directly (API) rather than the gviz CSV export gives you an
independent count. If the two disagree, the CSV export is stale or the sheet has
rows below your read range. Fetch `A1:F1000` even for a 700-row sheet: the grid is
often 998 rows and stale rows sit below your data silently.

## The write that works

`values.update` needs the array wrapped:

```json
{"range": "Лист1!A1", "majorDimension": "ROWS", "values": [[...], [...]]}
```

A bare `[[...]]` returns `400 Root element must be a message`. Use
`valueInputOption=RAW` so Sheets does not re-interpret formulas, leading `=`, or
numbers as typed content.

**The `range` in the body must be byte-identical to the range in the URL**, both
bounds included. Sending `'Лист1'!A754` in the body under a `.../A754:F792` URL
returns `400 INVALID_ARGUMENT: Request range['Лист1'!A754] does not match value's
range['Лист1'!A754:F792]` — the API reads the body range as the declared shape of
the payload, not as a hint. Build one string and use it for both:

```python
full = f"'{title}'!A{start}:F{start+len(rows)-1}"
res = call(API + "/values/" + urllib.parse.quote(full) + "?valueInputOption=RAW",
           {"range": full, "majorDimension": "ROWS", "values": rows}, "PUT")
```

## Appending a layer: anchor the start row on a live read

Writing a new layer is an append, and the start row must come from a read taken
immediately before the write — not from a count computed earlier in the session,
and not from the local CSV copy, which goes stale the moment anyone else edits.
`start = <live non-empty data rows> + 2` (one for the header, one because sheet
rows are 1-indexed). Get the real `sheetId` and the real sheet title from
`spreadsheets.get` in that same read; a title typed by hand is how a layer lands on
the wrong tab.

Verify the append by row identity on a full re-read, then again through the
consumer (gviz CSV). Assert both the start row's `id` and the last row's `id` —
an append that lands one row high silently shifts the whole layer and every row
still looks present.

## Deleting rows: `deleteRange` does not work

Reached four consecutive 400s on this. What the API actually says:

- `deleteRange` requires a `dimensions` field — but the JSON schema rejects it
  (`Unknown name "dimensions"`), and omitting it gives `No dimension specified`.
- A fully-specified GridRange (all four bounds) still gives `No dimension specified`.
- `values:clear` returns **404 from the Google front-end, not the API** — a
  Cyrillic sheet name in the `range` query param breaks URL resolution. The 404
  body is an HTML error page, which is the tell.

**What works — overwrite the tail with empty `userEnteredValue` cells:**

```python
blank = [{"userEnteredValue": {}} for _ in range(rows_to_clear * cols)]
{"requests": [{"updateCells": {
    "range": {"sheetId": sid, "startRowIndex": N, "endRowIndex": M,
              "startColumnIndex": 0, "endColumnIndex": C},
    "rows": [{"values": blank[i*C:(i+1)*C]} for i in range(rows_to_clear)],
    "fields": "userEnteredValue"}}]}
```

Get the real `sheetId` from `spreadsheets.get` — it is often `0` but do not assume.

## A short write does not delete what follows

`values.update` on `A1:F659` over a sheet that held 712 rows leaves rows 660–713
**intact**. The write returns `200` with `updatedRows: 659` and the stale rows are
still there. Assert on **row identity**, not on the row count: after any write
that changes the row count, re-read the whole grid and check the last non-empty
row's `id` equals the last `id` you sent. A count alone passes while 54 stale
records are still live:

```python
vals = sheet_values  # re-read A1:F1000, not just your write range
rows = [r for r in vals[1:] if any(str(x).strip() for x in r)]
assert str(rows[-1][0]) == str(rows_sent[-1][0]), "stale tail survived"
assert len(rows) == len(rows_sent)
```

The same assert applies after the `updateCells` blank-tail trick: confirm the old
tail ids are gone rather than trusting the batchUpdate 200.

## Verify from the reader's view, not the writer's

After writing, confirm through whatever the consumer actually uses (a gviz CSV
export, a parse step, a downstream query) — not just `spreadsheets.get`. A 200 on
the write plus a 200 on an API read can still hide a row-count mismatch.

## Non-ASCII sheet names break the request URL, not the API

A Cyrillic sheet name in the URL raises
`UnicodeEncodeError: 'ascii' codec can't encode characters` from
`http.client.putrequest`, whose traceback names `encode_ascii` — so it reads like a
header problem but the failure is in the **URL path**. Percent-encode the range
before it goes into the request line, and encode the body as UTF-8 with a matching
charset on the header:

```python
rng = urllib.parse.quote("Лист1!A1")        # -> %D0%9B...
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{rng}?valueInputOption=RAW"
req = urllib.request.Request(url, data=body_bytes, method="PUT", headers={
    "Authorization": f"Bearer {tok}",
    "Content-Type": "application/json; charset=utf-8"})
```

Both halves are required: `quote` on the range and `.encode("utf-8")` on the body.
Encoding only the body still dies in `putrequest`. Serializing with
`json.dumps(..., ensure_ascii=False).encode("utf-8")` handles the Cyrillic content
itself — it is the URL and the body bytes that need the encoding above.

## CSV traps when the sheet is consumed as CSV

- **Single quotes inside a field break naive parsers.** `Метка"<” ... метка"11"`
  has two lone `"`; an RFC 4180 parser treats the first as a field opener and
  swallows every following comma and newline, collapsing N rows into one giant
  row. This is not cosmetic — it can hide hundreds of records. Fix the parser
  (quote is special only when it *starts* a field) or escape the data.
- **Non-ASCII sheet names** break `range` in query params. Prefer the values API
  path in the POST body over a URL query param, and encode explicitly.
- A `{digit}` style comma (`{,}5`, `84{,}0`) is a LaTeX artifact: the braces hold
  an empty group containing a comma, and the digit follows *outside* the braces.
  A regex written as `{,(\d)}` silently misses every one of them.

## Reporting

State the before/after row counts from a re-read, and name the backup file path.
Never report a write as done off the HTTP 200 alone.