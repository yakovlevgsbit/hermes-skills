# Package integrity gate for self-verifying bundles

Use when the deliverable is a multi-file script bundle that must prove its own
integrity before running anything, especially when it goes to an independent
auditor who will re-verify the submission.

## 1. A manifest inside the package is transport, not trust

Verification arranged inside the package (A hashes B, B hashes A) proves only
self-consistency: replace a file, recompute the manifest, and the circle closes
cleanly. State the trust root explicitly and put it outside the package.

```
L0  anchor file outside the package (anchor.sha256)      <- only root of trust
      |
      +-- manifest.json inside the package (transport; its own sha256 is an
      |     anchor entry, authenticated BEFORE the schema is parsed)
            +-- class A: enforced,    mismatch is a fatal refusal
            +-- class B: prep-exec,   verified against the anchor before it runs
            +-- class C: test,        mismatch is a warning
```

- Publish the anchor as literal `sha256sum -c` lines so a third party can verify
  with no code from the bundle: `cd pkg && sha256sum -c ../out/anchor.sha256`.
- Say plainly in the deliverable what the anchor does NOT cover: if the anchor is
  compromised together with the package, no protection exists. A signature
  (GPG/minisign) is a different mechanism — do not imply one is present.

## 2. Split the file set into enforced and prep

| Class | Contents | On mismatch | Why |
|---|---|---|---|
| A enforced | shared library, stage scripts, gates, the gate script itself | refusal against the anchor, nothing runs | these are the bytes that decide the outcome |
| B prep-exec | extractor, manifest builder | refusal against the anchor, checked BEFORE the tool runs; each tool also re-verifies its own sha256 against the anchor at startup | they execute before the gate exists, so a warn-after-the-fact verdict is worthless |
| C test | the test suite itself | warning only | it never participates in the production path; a fatal class would let a test edit block an operator run |

The manifest builder cannot be its own guarantor, and the extractor cannot
validate the package it just unpacked — the anchor checks them at operating
time, and the delivered procedure starts with `sha256sum -c` on the anchor
before any tool runs. A prep tool's `--self-check-anchor` is self-attestation:
an edited tool that always passes it will. State that residual risk; the
external command is the real gate.

- Compare the manifest's key set against `EXPECTED` **exactly**: a missing entry
  and an unknown entry are both refusals. A subset check lets an attacker drop a
  file the gate never asked about.
- Keep the `EXPECTED` list in the gate module, not imported from the builder.
  If the builder defines what is checked, tampering with the builder changes the
  check.
- Refuse unexpected objects in the package directory as well — a stray
  `backdoor.py` beside a valid manifest must not pass silently.

## 3. Protect the manifest before reading it

`lstat` first, then read through a single descriptor:

| Check | Reject when |
|---|---|
| type | not a regular file |
| symlink | `S_ISLNK` |
| hardlink | `st_nlink != 1` |
| owner | `st_uid` not in `{euid, 0}` |
| mode | any write bit for group/other |
| size | zero, or above the manifest cap |
| JSON | parse error, or duplicate keys |
| open | `O_NOFOLLOW` fails, or `fstat` dev/ino differs from `lstat` |

`st_nlink != 1` matters because a second name for the same inode can be edited
after the check. Use `json.loads(..., object_pairs_hook=...)` raising on repeats:
after a plain load, `{"a":1,"a":2}` is indistinguishable from `{"a":2}`.

## 3b. Validate the manifest schema strictly

"It parsed" is not "it says what was asked". Refuse on any of: top level not an
object; key set not exactly the expected set (no extras, no omissions); wrong
format / version / generator / algorithm values; sections not exactly the three
expected, or any section empty; file names failing a conservative regex; entry
keys not exactly `{sha256, size}`; `sha256` not 64-char lowercase hex (uppercase
is a refusal, even though it hashes the same); `size` not an int (reject `bool`)
or outside a sane range. Serialise the manifest canonically (`sort_keys=True`)
so its own hash is reproducible. Every schema failure is a controlled refusal
naming the field — wrap the whole gate body so an unexpected exception becomes
`internal error` + refusal code, never a traceback, and never a controller start.

## 4. Verify, then materialize, then execute

1. Read each enforced file once, hash the buffer you will execute, compare to the
   manifest (size first, then sha256).
2. Write the verified buffers into a fresh `0700` directory owned by the runner.
3. Execute from that directory, not from the submitted path.

This removes the window where the submitted file changes between check and
`exec`. It does not remove the window where the same UID or root edits the
private directory — say so instead of claiming a sandbox.

A gate hashing itself and matching its own manifest entry is
`self_consistency: ok`, not authenticity. Label it that way in the output.

## 5. Distinct refusal codes, and prove the gate did not start

- Package rejection gets its own code (e.g. `65`), distinct from generic error
  (`1`) and timeout. Tests assert the specific code; "exited non-zero" hides a
  crash that happened to be non-zero.
- Map `FileNotFoundError` and `PermissionError` inside the gate to the refusal
  code. A missing enforced file must produce the documented refusal, not a
  traceback with rc=1.
- Every negative test also asserts that no run artefacts exist (`final.json`,
  `rc.txt`, stage outputs). A gate that refuses after starting the controller is
  not a gate.

## 6. Test harness for the gate

One mutation per case; copy the package fresh for each. Assert code + failure
marker + absence of run artefacts, and count the passes explicitly (`N/N`).

**Make the harness idempotent.** A case that chmods a shared directory (0777 on
the anchor dir, a world-writable dir used as an attack vector) leaves permissions
the NEXT run inherits — and then the honest gate refuses its own fixtures with
`anchor chain: group/other writable`, producing a wall of failures that looks
like a regression. Normalise permissions at the START of every run (`chmod 0700`
on the anchor/fixtures dirs, unlink stray world-writable test dirs) and restore
them in a `finally` inside each such case.

| Case | Mutation | Trap |
|---|---|---|
| happy path | none, manifest rebuilt | controller must reach its final status |
| enforced tampered | flip one byte, **same size** | changing length lets the size check fire and the hash check stays untested |
| enforced missing | delete a file | must be refusal code, not `FileNotFoundError` |
| unexpected object | add a file to the package dir | |
| manifest symlink | replace manifest with a link | |
| manifest hardlink | `os.link` and keep **both** names | unlinking one restores `nlink=1` and the case tests nothing |
| manifest mode | `chmod 0666` | |
| manifest duplicate key | repeat a top-level key | |
| manifest invalid JSON | truncate it | |
| manifest missing entry | remove one enforced file from it | |
| manifest unknown entry | add `evil.py` | |
| prep-extract tampered | flip a byte in the extractor | refusal code, controller not started — the extractor is never trust-on-warn |
| test runner tampered | flip a byte in the suite | must SUCCEED with a warning — this proves the split from prep-exec is real |
| anchor entry missing / extra | delete or add an anchor line | refusal; coverage compared exactly |
| file + manifest replaced together | tamper a file, rebuild the manifest, leave the anchor | refusal on the manifest entry (`manifest: sha256 mismatch`) |
| manifest replaced after build | append one byte to the manifest | refusal on the manifest entry |
| schema type errors | `size` as string, `sha256` as int, uppercase hex, extra entry or top-level field | controlled refusal naming the field, no traceback, controller not started |
| authorization flag absent | omit it | refusal, controller not started |

Run the suite as an unprivileged UID when the controller legitimately refuses
root, otherwise the happy path cannot be exercised at all:

```sh
setpriv --reuid=65534 --regid=65534 --clear-groups \
  /usr/bin/python3 ./test_bundle.py --workdir /srv/work/tests
```

Clear build artefacts before generating the manifest. `python3 -m py_compile` and
any import of a library module leaves `__pycache__` inside the package directory;
the gate then refuses it as an unexpected object, which is CORRECT behaviour.
Delete the cache, do not teach the gate to ignore it — an allowlist for
`__pycache__` is an allowlist for arbitrary `.pyc` payloads. Prevent it at the
source: the gate sets `sys.dont_write_bytecode = True` before importing any
sibling module from the package directory.

Tamper one byte so the file keeps BOTH its size and its syntax: swap a byte
inside the docstring (a space to `'.'`, or a letter to the next letter). Editing
code bytes risks a `SyntaxError`, which the runner reports as a generic failure
and masks the behaviour under test; a same-size edit also keeps the size check
from firing, so the sha256 check is what actually gets exercised.

## 7. Extracting an archive before any gate exists

- Target must be empty, not a symlink, and outside protected trees; the anchor's
  own directory chain (and the launcher's) must be root/euid-owned with no
  group/other write bit, or an unprivileged UID can rewrite the anchor it is
  being checked against. Prove that with a real write attempt as uid 65534, not
  an inference from `ls -l`.
- Validate member paths before writing: reject absolute, `..`, empty components,
  backslashes, over-long segments.
- Reject symlink, hardlink and special members outright.
- Two independent limits: a declared-size preflight (cheap refusal) and a capped
  read per member during extraction, because declared sizes can lie and a
  decompression bomb declares little and expands much.
- Print the sha256 of every extracted file — that listing becomes the L0 anchor
  for the audit report. When an anchor already exists, verify every extracted
  file against it in the same run (`--anchor`): a swapped archive then fails at
  extraction, before any gate exists. The extractor also accepts
  `--self-check-anchor` and re-verifies its own bytes first.

## 7a. The launcher is the trust root — keep it out of the package

1. The entry point is a **shell** script in its own root-owned directory, and a
   minimal stage-0 validator sits before it. Any interpreter — Python included —
   executes the file's body before the first statement of that body runs, so a
   `launch_*.py` cannot check its own hash in time. Stage-0 therefore only
   hashes the launcher with `sha256sum` and `exec`s it on a match; it never
   reads, sources or interprets the launcher's text.
2. Both launcher and stage-0 are anchor entries. The manifest builder takes an
   explicit list of launcher-contour paths and refuses a path inside the
   package. The package anchor and the launcher entries live in the same file
   but are verified from different working directories (see 7b).
3. Gate and bootstrap must tolerate those extra anchor lines: whitelist exactly
   the launcher contour's filenames when comparing the anchor's key set, or the
   “unexpected entries” check refuses every legitimate run.
4. The launcher checks the anchor chain, its own owner/mode/nlink, verifies the
   package against the anchor, copies the verified bytes into a private `0700`
   directory (`0400` files), re-verifies that copy, rejects any unexpected
   object in it, and only then starts the gate.
5. **The tamper test must be falsifiable.** "Any non-zero exit" also passes when
   the tamper broke the shell syntax or when the run failed for an unrelated
   reason. Create a modified copy that is still root-owned with the correct mode
   and chain, has a malicious line right after the shebang, and assert three
   things: the refusal names THAT file (`audit-launch/verify_launcher.sh`), the
   output carries a hash-mismatch marker, and the marker file the malicious line
   would create does not exist. Run it in a sandbox with a freshly generated
   path-qualified anchor so the anchor is genuinely the thing that catches it.
6. Stage-0 attests itself only through its root-owned directory and the
   operator's external check — say that plainly instead of implying the
   arrangement is self-protecting. A hand-run `sha256sum -c` before first
   execution remains mandatory.

## 7b. Anchor layout for reproducible external verification

A single anchor file with bare filenames only verifies from the one directory
that holds those files. Once the contour spans two directories (package +
launcher) the operator's command either fails with `FAILED open or read` or,
silently worse, verifies half the set.

Emit a **path-qualified** anchor beside the short-name one: entries are relative
to a common root, so one `cd` covers everything.

```sh
# generation: walk the EXPECTED lists, never a glob
python3 make_paths_anchor.py --root /srv --out /srv/audit-anchor/anchor.paths.sha256

# verification of the whole contour (14/14, exit 0, zero FAILED)
cd /srv && sha256sum -c /srv/audit-anchor/anchor.paths.sha256

# verification of the package subset only (13/13, exit 0)
cd /srv/audit-v61-work/pkg
grep -v -E '  (launch_v61\.sh|verify_launcher\.sh)$' \
  /srv/audit-anchor/anchor.sha256 | sha256sum -c -
```

Rules that keep this honest:

- Put the exact verify command in the anchor's own header comment.
- Print the entry count next to the hash so a truncated anchor is visible.
- Show the actual command, its real output and its exit code in the report. A
  report that says "anchor verified" without the pasted output is an assertion,
  not evidence — and padding the set with a missing result is the failure the
  auditor will catch.
- Keep both anchors regenerated by the same builder run; a hand-edited anchor is
  a new unaudited trust root.

## 7c. The commit marker: full validation order

The reader of a result must treat `STATUS.json` as data and `COMMIT.json` as the
only proof that this run actually finished. Validate in this order and return a
distinct reason for each failure, so a test can assert WHICH check fired:

| # | Check | Reason code |
|---|---|---|
| 1 | `STATUS.json` exists, readable, JSON object | `status_missing` / `status_unreadable` / `status_not_object` |
| 2 | required STATUS fields present with correct types | `status_missing_run_id` / `status_field_not_string` |
| 3 | `COMMIT.json` exists, readable, JSON object | `commit_missing` / `commit_unreadable` / `commit_not_object` |
| 4 | required COMMIT fields present with correct types | `commit_missing_field:<name>` / `commit_field_wrong_type:<name>` |
| 5 | `STATUS.status == COMPLETE` | `status_not_complete:<value>` |
| 6 | `COMMIT.status == COMPLETE` | `commit_status_not_complete:<value>` |
| 7 | `STATUS.run_id == COMMIT.run_id` | `run_id_mismatch` |
| 8 | `status_sha256` is 64 lowercase hex | `commit_sha_format_invalid` |
| 9 | `sha256(raw bytes of STATUS.json) == COMMIT.status_sha256` | `status_sha256_mismatch` |

Check 6 is the one that gets skipped: the marker itself carries a status field,
and a commit written as `INCOMPLETE` next to a `COMPLETE` status file is a
contradiction, not a pass. Check 9 must hash the BYTES on disk, not a
re-serialised object — `json.dump(load(f))` normalises whitespace and makes a
tampered file hash correctly.

Test matrix (each case mutates a real, freshly produced COMPLETE run):

| Case | Mutation | Expected |
|---|---|---|
| bytes changed | bump any STATUS field, keep COMMIT | `status_sha256_mismatch` |
| one field changed, same run_id | add a reason string | `status_sha256_mismatch` |
| hash replaced | set `status_sha256` to zeros | `status_sha256_mismatch` |
| commit not complete | set `COMMIT.status = INCOMPLETE` | `commit_status_not_complete` |
| foreign run | prefix `run_id` | `run_id_mismatch` |
| status not complete but self-consistent | set STATUS to INCOMPLETE, recompute `status_sha256` in COMMIT | `status_not_complete` |
| corrupt JSON | truncate either file | `*_unreadable` |
| marker absent | delete `COMMIT.json` | `commit_missing` |

## 8. What the gate does not give you

State these in the deliverable rather than letting a green run imply more:

- no content/secret scanning of the files themselves;
- no signature, so a compromised anchor plus package is undetectable;
- prep tools' `--self-check-anchor` is self-attestation — an edited tool can
  pass its own check; the external `sha256sum -c` step is the real gate;
- no protection against the same UID or root;
- residual TOCTOU between materialisation and `exec`;
- `rsync -A -X` ACL/xattr fidelity depends on the target filesystem;
- ACL verification needs `getfacl`; without it, ACL status is `unsupported`,
  which must be a warning, not a pass.
