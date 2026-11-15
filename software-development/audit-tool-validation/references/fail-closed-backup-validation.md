# Fail-closed backup validation

Use for reviewing a backup controller or an executable operations plan. These
are design and acceptance rules, not a prevalidated backup implementation.

## 1. Freeze the scope and classify confidentiality

1. Resolve source, destination, approved exclusions, and required files before
   copying. Refuse an existing destination; preserve a partially created one
   for manual investigation rather than silently reusing it.
2. Build one authoritative inventory. Record ordinary files, directories,
   symlinks, special objects, read failures, and explicitly excluded subtree
   boundaries. Prune declared exclusions before descending. Never turn a read
   error into an implicit exclusion.
3. Discover SQLite by its header, including hidden directories and files without
   extensions. Keep unreadable candidates separate from confirmed databases;
   an unreadable header does not prove the file is SQLite.
4. Derive the transfer list and verification set from that same inventory.
   Exclude discovered SQLite files and their WAL/SHM/journal sidecars from raw
   file copying. Never rely only on `*.db` exclusions.
5. Gate static copying on individual review of the exact bytes. Check config,
   skills, integration data, and metadata as well as obvious key files. Treat
   conversation/state databases as potentially sensitive even if the source
   filename does not suggest credentials. Keep credential backups outside the
   ordinary category and require explicit authorization for their scope.

Use NUL-delimited path transport or structured JSON; never recover filenames
with whitespace splitting. When generating rsync filters, escape literal glob
characters and verify the installed version's `--from0` semantics. Build a
fixture with spaces, Unicode, brackets, and newlines in filenames.

## 2. Capture a defined static snapshot

- Read an atomically replaced JSON store through one open descriptor, validate
  the complete bytes, and hash those exact bytes. Verify the writer really uses
  atomic replacement in the installed version; a comment claiming atomicity is
  not evidence.
- Require a valid schema, unique record IDs, and timezone-aware timestamps.
  Reject truncated JSON and duplicate object keys rather than letting a parser
  silently select the last value.
- Compare captured bytes against the inventory snapshot. If the live store
  advances later, report added/removed/modified records and parsed timestamps.
  Equal record counts or the presence of `updated_at` does not establish
  integrity. Different bytes with the same or an earlier timestamp require
  investigation.
- Compare the destination hash to the captured source hash, not to an unrelated
  later live version. Otherwise a valid concurrent update becomes an unexplained
  mismatch, or corruption is excused as drift.
- Treat every nonzero rsync result as failure by default, including rc=24.
  Relax that rule only with an explicitly approved vanished-file policy and
  complete inventory evidence; loosely parsing diagnostic text is not proof.

## 3. Back up SQLite through its API

- Use `sqlite3.Connection.backup` for active SQLite databases, not raw copying.
  Query and record each database's actual journal mode at execution time.
- Open the source with `mode=ro`, but do not promise zero locking or zero
  auxiliary-file activity. WAL readers can interact with the shared-memory
  index and checkpoint progress; disk load still affects other processes.
- Do not use `immutable=1` for a live changing database. Reserve it for a closed,
  verified offline snapshot when the caller really guarantees immutability.
- Read every row returned by `PRAGMA integrity_check` and require exactly the
  success result. An exception or any other result blocks the stage. Independently
  recheck each saved snapshot, its hash, and its identity before finalization.
- Do not copy old live WAL/SHM files onto a restored snapshot. Test restoration
  in a separate authorized directory; compare logical data and integrity.
  SQLite Backup API does not promise byte-for-byte identical destination files
  across independent backup operations.

### Python backup progress and deadlines

`Connection.backup(pages=N)` uses N as the step size **inside one Python call**;
it is not an externally resumable N-page operation. The progress callback's
return value is ignored. Raise an exception to abort cooperatively; returning
`True` does not cancel the backup.

Treat the connection busy timeout, Backup API's own BUSY/LOCKED retry loop,
callback cancellation, and an external watchdog as distinct mechanisms. Define
which failures are retryable, total attempts, intervals between attempts, and
whether validation and hashing consume the same budget. Three attempts have
two between-attempt delays, not three.

For bounded supervision, use a separately spawned worker, an overall monotonic
budget, explicit termination/reaping, and no continuation while a worker remains
unaccounted for. Calculate the nominal budget including retries and cleanup.
Do not promise a hard wall-clock maximum: an uninterruptible kernel operation
or delayed scheduling can outlive a user-space timeout. Record the owned worker
PID when cleanup cannot be confirmed; never kill unrelated gateway processes.

### 3a. Sidecars are not databases; the API call direction is `source.backup(target)`

A WAL/SHM/journal suffix belongs to a main database and must never become an
target for its own backup. Classify by role, not by extension:

- an object is a **sidecar** only when `<base>.db` exists next to it and the base
  name matches an actual database; an orphan `x.db-wal` with no `x.db` is an
  ordinary file and must stay in the file list instead of silently vanishing
  from the report;
- write the classification into the inventory (`disposition: sqlite` vs
  `disposition: sidecar`, plus the owning base path) and emit an explicit
  targets file next to it; the backup stage must read targets from that file,
  never re-derive them from names;
- assert `found == saved`, that no sidecar path appears among the targets, and
  that the target count equals `found`; a sidecar fed to the API produces a
  garbage “database” that still passes a nominal copy.

`sqlite3.Connection.backup` is a method ON THE SOURCE that writes INTO the
argument: `source.backup(target, pages=N)`. Written as `target.backup(source)`
the call makes the source ingest the target's contents — for a fresh empty
target that wipes the data, and against a `mode=ro` source it raises
`attempt to write a readonly database`. Keep a regression test that runs the
wrong form and asserts the copy does not carry the source's tables, so the
mistake cannot come back silently.

### 3b. WAL reality in tests

- A connection must stay OPEN while the backup runs, or SQLite deletes `-wal`
  and `-shm` on close and the fixture silently tests a rollback-journal DB.
- SQLite removes or truncates the WAL on the last close, and a checkpoint
  changes the main file's bytes. Do NOT assert the source file's sha256 is
  unchanged for a WAL database — it will legitimately differ. Assert integrity
  instead: same tables and row counts before and after, `integrity_check == ok`
  on the copy.
- Take the “before” snapshot AFTER every read-only probe that opens the
  database; the probe itself can move WAL state.

### 3c. Two snapshots of a live store must both be real reads

Copying snapshot one to make snapshot two compares a file to itself and always
reports “unchanged”. Read the source twice, at two different points in the run
(before and after the copying stages), record sha256 + size + `mtime_ns` for
each, and record an explicit `source_changed_between_snapshots` flag. A live
cron rewriting its store during the run is a normal event, not a failure — but
it must be stated, never absorbed into a green “unchanged” verdict. Expect the
staging-vs-source checksum step to fail honestly in that case (staging is now
stale); that is correct fail-closed behaviour, and the recovery is a re-run, not
a relaxed check.

## 4. Verify completeness and permissions independently

- Compute `found` from the frozen inventory, not from log lines or destination
  files. Account for every confirmed database as saved, failed, or not started.
  Preserve unreadable inventory objects as a separate blocking category.
- Allow `COMPLETE` only when every required object was processed and verified.
  An explained unreadable required file is still a missing backup, not a warning
  that permits success. Explicit out-of-scope objects are not successful copies.
- Compare expected and actual destination sets in both directions before hashes:
  identify missing and extra objects, then compare every expected file's bytes.
- Interpret `diff` rc=0 as equality, rc=1 as differences, and rc=2 as an error.
  Neither nonzero result is success. Use explicit `if command; then ...; else
  rc=$?; ...; fi`; `set -e` can exit before an unconditional subsequent `$?` read.
- Make owner, group, exact file/directory mode, ACL, symlink, and object-type
  violations produce nonzero status. Printing a list from `find` is not an
  assertion; command failure or unreadable ACL output is also a failure.
- Distinguish metadata preservation from backup privacy. If rsync preserves
  original metadata with `-aHAX --numeric-ids`, define whether original metadata
  stays only in a protected manifest and copied objects are then restricted.
  Do not require preserved public modes and exact private modes simultaneously.

## 5. Finalize once, from evidence

Record each stage's actual result and stop later stages on failure. Exercise the
controller under `set -euo pipefail`, conditional commands, interrupted children,
failed result writes, and failures during initial directory creation. Do not
pre-record a zero before a step has completed.

Use one finalizer which validates stage evidence, inventory coverage, hashes,
integrity, and permissions before publishing `COMPLETE`. Missing, duplicated,
malformed, stale, or unreadable evidence must refuse completion. Preserve partial
artifacts; if a crash or full disk prevents status publication, absence of valid
completion evidence means `INCOMPLETE` rather than an assumed success.

Publishing the status is itself two writes, and the failure mode is subtle:
writing `COMPLETE` to `final.json` first and then failing on `rc.txt` leaves a
false `COMPLETE` on disk. Wrap publication in one function that writes both
files, then READS BOTH BACK and compares their content (`status` field and the
status line must agree, not merely exist). On any write or readback error,
republish `INCOMPLETE` with a `finalization_error` field and return the error
code even if that retry succeeded. Test it by making `rc.txt` un-writable (a
directory of that name in the output dir is a clean, filesystem-independent way
to force the failure) and assert that neither file reads `COMPLETE` afterwards.

### 5a. Pick ONE contract for status vs return code and write it down

Two defensible contracts exist; keep them separate and never half of each:

- **Derived files are mandatory** — a failure to write `rc.txt` or `final.json`
  cancels `COMPLETE`, the status is rewritten to `INCOMPLETE`, the commit marker
  is removed, and the exit code is non-zero.
- **Derived files are optional** — their failure is logged, the exit code stays
  zero, and nothing claims otherwise.

Mixing them produces the worst state: `COMPLETE` on disk with a non-zero exit
code, and neither the operator nor the auditor knows which to believe. State the
chosen contract as a formula in the report, e.g.
`COMPLETE ⇔ rc == 0 ⇔ STATUS == COMPLETE ∧ COMMIT == COMPLETE ∧ run_id match ∧
sha256(STATUS) == COMMIT.status_sha256 ∧ derived files written AND read back`.
Order the writes so the marker is published LAST — derived files first, then
`COMMIT.json`.

### 5b. One registry of fault steps, proven to match the code

Keep the step names in a single module-level constant used as the CLI
`choices`, and add a test that every declared name appears in the code that
raises it. A hand-maintained `choices` list drifts: steps can be advertised,
tested, and never implemented, and the test still passes because the run
succeeds for another reason. The per-step test asserts all of: earlier stages
at `rc=0`, the finalization stage non-zero, `effective_status() != COMPLETE`,
and the stage's own error text naming the injected step.

Place `temp_create` **immediately before** `os.open()` of the temporary file —
injecting it earlier turns the test into "publishing failed", which any broken
path would satisfy. Steps worth having: `unlink`, `temp_create`, `write`,
`fsync`, `replace`, `fsync_dir`, `readback`, one per derived file
(`derived_rc`, `derived_final`), `derived_readback`, `commit_publish`,
`commit_unlink`.

### 5c. Rollback that cannot roll back

`commit_unlink` cannot fire on its own during a clean run, because nothing has
been removed yet. Test it as the late-failure scenario: publish `COMMIT.json`,
then trigger a rollback in which deleting the marker also fails. The expected
result is still `INCOMPLETE` and a non-zero code, because `STATUS.json` was
rewritten to `INCOMPLETE` and check 5 of the commit validation now rejects it.
If the implementation returns `COMPLETE` here, the marker — not the status — is
deciding the outcome; fix the reader, not the test.

Keep process manifests on an explicit field allowlist (PID, UID/GID, state and
approved service properties). Omit full argv, environment values, raw unit
Environment/ExecStart fields, and credential-bearing URLs; regex redaction of
arbitrary command lines is not a reliable secret boundary.

## 6. Acceptance fixtures before live use

Test on an explicitly separate fixture source and a fresh destination: a valid
run repeated twice; a hidden extensionless SQLite database; an active WAL;
BUSY/LOCKED; invalid JSON and duplicate IDs; missing and extra source/destination
files; symlinks and unexpected types; unreadable files; stale manual-review hashes;
modified snapshot bytes; wrong UID/GID/mode; named/default ACLs; failed report
writes; interrupted stages; and a pre-existing destination. Verify refusal with
an independent assertion, not only the tool's own success summary. Do not label
these tests executed until they actually ran under the authorized conditions.
