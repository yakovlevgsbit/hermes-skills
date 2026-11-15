---
name: audit-tool-validation
description: "Use when you build a script that reports findings."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [validation, false-positives, false-negatives, fixtures, audit, scripts, verification]
    related_skills: [systematic-debugging, dogfood, requesting-code-review]
---

# Audit Tool Validation

A script that inspects something and reports findings (audit, linter, scraper,
monitor, parser, health check) is only worth what its output is worth. Wrong
output looks exactly like right output: plausible, specific, formatted. This is
the procedure for proving a findings-producing tool before anyone acts on it.

## When to Use

- You just wrote or edited a script whose output is a list of problems, matches,
  measurements, or anomalies.
- A monitor or scraper reports counts, and someone will make a decision from them.
- A prompt or instruction set tells another agent what to look for and report.

Don't use for: scripts whose output you directly observe and eyeball each run
(one-off reports), or anything where a wrong answer is immediately obvious.

## The three-direction rule

The failure modes are opposite, and a check that catches one is blind to the other:

| Direction | Looks like | Caught by |
|---|---|---|
| False negative | The tool misses a real defect | Fixture with known defects |
| False positive | The tool flags something that is not a defect | Running on real input |
| Non-reproducible | The output differs between runs on identical input | Run the same command twice and diff the output |

**No pass is optional.** A fixture cannot expose over-reporting — it contains
no realistic markup to misjudge. Real input cannot expose under-reporting — you
do not know what it failed to find. On one real page, a first-pass audit reported
32 findings of which 14 were artefacts; the fixture pass had already declared the
script correct.

## Measurements must repeat

When the tool's output is a *number* (a distance, a duration, a count, a score),
an unstable number is worse than no number: it reads as data, gets quoted, and
drives decisions. Run the identical command twice and diff before quoting
anything as a result.

- **Time-based limits make a tool non-deterministic; iteration/depth limits do
  not.** A search that stops on wall-clock seconds does different amounts of work
  on different runs. Use a fixed depth/iteration budget for anything you intend
  to measure, and keep the time-limited mode for interactive use only.
- **Thread count and cache size are part of the measurement.** Pin them
  explicitly (one thread, fixed cache) rather than inheriting defaults.
- **A feature that exists to make a tool behave more humanly makes it a bad
  instrument.** Strength limiters, temperature, top-k sampling and similar
  options introduce randomness *by design* — that is how they weaken or vary
  output. Do not measure with them enabled, and do not assume turning the
  setting to its maximum disables them: the enable flag usually stays on. If a
  weaker variant is needed, implement a *seeded* one yourself (choose among the
  near-best candidates with a seeded RNG).
- **Seed per unit of work, not per session.** Derive the seed from the step index
  so a choice is a function of the state, not of how many calls came before it —
  otherwise the same position gives different results depending on call order.
- **Sort before making a seeded choice.** Candidates with equal scores can arrive
  in an unstable order; an unsorted pool makes the seeded pick depend on that
  order rather than on the seed.
- **Report an aggregate over N runs, not one run**, and have the CLI print a
  warning when the user selects a non-reproducible mode.
- **Write a test that asserts reproducibility.** Running the same input twice and
  asserting identical output is the only thing that catches this regressing; the
  test also documents that the behaviour was deliberate.

## Calibrate a metric before trusting verdicts built on it

When the tool compares an estimated quantity against a threshold — text width,
rendered extent, element bounding box, predicted duration — the estimate is part
of the tool, and a wrong estimate produces wrong findings at scale.

- **Measure the constant from real output; never guess it.** Render one known
  sample and derive the factor from what came out. A guessed text-width constant
  that was 3.2x too wide made every item look like a collision, and the wall of
  false positives buried the single real defect underneath.
- **A metric that is wrong in the permissive direction is the dangerous one.**
  Over-estimating floods the report (annoying, self-revealing). Under-estimating
  makes the check silently miss the defect it exists to catch.
- **A relative score inherits the denominator's failure modes, and a tiny denominator
  manufactures an enormous score.** Normalising a measurement against a baseline
  (`x / baseline`) is only as trustworthy as the baseline: when the baseline is near
  zero the ratio explodes, and the explosion reads as a spectacular finding. A channel
  whose typical throughput was ~31 views/day reported a 4,216x multiple for a video that
  merely got lucky — the extreme value was an artefact of the denominator, not a
  signal. Before trusting any ratio, floor the baseline at a documented minimum and
  treat values below it as "no baseline, not comparable" rather than dividing by them.
  Then check that the ratio's spread is plausible: a field of implausibly large
  multiples means the denominator, not the subject, is broken.
- **Sanity-check the estimate against a known case before running the real
  pass**, so a calibration failure surfaces on one item instead of a hundred.

## Checks that compare two artifacts

- **Bind educational math oracles to the delivered givens, not duplicated test constants.** Read the exact assigned map subset, invoke the real schema validator, parse the lesson's stated data, and independently reconstruct lengths, angles, areas, and all choice outcomes. Test a synchronized corruption of answer, expected value, and arithmetic expression: schema agreement alone must not pass it. Keep these checks scoped to owned lessons and mutate only in-memory copies.
- **Validate intermediate worked-example equalities, not just the answer display.** Evaluate each numerical term in a checked equality chain against an oracle derived from the stated givens; compare exact symbolic values and explicitly requested approximations separately. A correct final answer must not hide an invalid intermediate calculation.
- **Keep unrelated valid claims intact in a semantic mutation fixture.** When corrupting a caption's angle, retain its correct disclosures about undrawn objects; otherwise a different guard can reject the fixture before the intended geometric comparison runs. Require the specific failure code and inspect which assertion produced it.
- **Parse whole mathematical identifiers before comparing values.** A substring parser can confuse `tg` with `ctg`, `AB` with `∠CAB`, or `b` with `a + b`, falsely rejecting correct content. Tokenize compound declarations first, require one unambiguous match per requested quantity, and keep these collisions in the real-input regression cases. Treat inverse-trigonometric boundary roundoff explicitly before counting distinct geometric solutions; never change the expected solution count to accommodate numerical noise.

A check asserting that a generated artifact agrees with its source of truth (a
diagram against firmware constants, a config against code, docs against a
schema) is itself a findings-producing tool and needs the same proof.

- **Parse BOTH sides from the files the code actually reads.** Derive one side
  from the source of truth and the other from the generator's parameters, then
  assert equality per key. Do not hardcode the expected values in the test —
  that only proves the test agrees with itself.
- **Guard against a parser that silently returns nothing.** An empty result set
  makes every comparison pass vacuously. Assert the parse produced at least the
  expected number of entries, and assert one known value, before comparing.
  Anchor the parse on a section marker, not on the first occurrence of a
  construct that appears several times in the file.
- **Prove the check fails on a deliberate mismatch.** Inject a wrong value, run
  the check, confirm it fails with a message naming both sides, then revert. A
  consistency check that has never been seen to fail is not evidence.
- **Never blanket-catch around the comparison or the parse.** A swallowed
  exception turns a mismatch into a pass.

## Procedure

0. **Establish the authorized phase before validation.** Architecture approval is
   not execution approval. If the user forbids server commands, do not run even
   read-only probes, create temporary files, update memory, or start a fixture
   there. Prepare the document and distinguish static review from execution.
   Stop after each approved phase; do not roll backup, runtime installation,
   account creation, and agent startup into one approval.
1. **Build a fixture with one deliberate instance of every check.** Not a
   representative page — an adversarial one: every defect class the tool claims
   to detect, present once and unmistakably. Ship it beside the script so the
   next edit can re-run it.
2. **Run the fixture and compare the summary against the fixture's defect list.**
   Every declared class must appear. A class that vanishes means the edit broke
   that check — that is the test failing, not the fixture.
3. **Run on real input and read every finding against its source.** For each one,
   open the cited selector/file/record and ask "is this actually the defect the
   label claims?" Bucket the answers: true finding, artefact, or unknown. Only
   then is the count meaningful.
4. **Explain the delta.** If the real-input run produces N findings and you
   expected M, account for the difference before reporting. An unexplained count
   is an unvalidated tool.
5. **Re-run both passes after every edit to the detection logic.** A change that
   fixes one artefact commonly introduces another; the fixture guards the
   opposite direction.

## Pitfalls

- **Validate suspected masked identifiers against raw data in code.** Secret/PII redaction can display a valid public phone URI or Telegram URL as `****` in tool output. Before declaring a source link malformed, check the raw file for asterisks and its required format programmatically and report booleans. Do not reconstruct a masked string from chat, disable redaction, or copy the displayed placeholder into an artifact; use the actual source value after validation. Verify the target independently when needed.

- **Set the classifier key AFTER the payload spread** — `{**payload, "type": ...,
  "severity": ...}`, never `{"type": ..., **payload}`. Any source record with
  its own `type` key (a log entry, a form control) silently overwrites the
  category, so findings get mislabelled and a per-category tally looks doubled.
  Keep payload keys disjoint from classifier keys for the same reason
  (`inputType`, not `type`, on a form-control record). The failure is invisible:
  the report still renders and the totals still add up to the wrong thing.
- **Composite translucent values instead of taking the first opaque one.** For
  colour, alpha, or layering checks, a value at 15% over a dark parent is not the
  value at 100% — flatten the whole stack before comparing. First-match wins
  reports a false extreme.
- **Refuse to measure what cannot be reduced to one number, and say so.**
  Gradient-filled text, values over images, and computed styles with no single
  answer should be listed as unmeasurable with the reason, not guessed. A
  fabricated number is worse than a stated gap, because it is actionable and
  wrong.
- **Check the standard's level before setting a threshold.** One number rarely
  means one thing: a minimum target size is 24px at AA and 44px at AAA. Picking
  the stricter figure as a default flags most real input and buries the true
  findings. Cite which level the threshold comes from, and make it a flag.
- **Know the standard's exemptions and honour them.** Rules have carve-outs
  (e.g. links inline in a text block are exempt from target-size minimums).
  Flagging exempt cases inflates the report and trains the reader to ignore it.
  Move them to a separate "exempt" list rather than dropping them silently.
- **Document from output, never from expectation.** Run the command, then paste
  what it returned. Drafting the report with the numbers you expect produces a
  document that is right until it isn't, and the discrepancy is invisible
  because both versions look equally plausible. If the run is still going, the
  report is not written yet.
- **When the measured numbers change, correct every place they were quoted** —
  README, docs, the summary you already gave. A stale figure in one file is
  indistinguishable from a current one in another.
- **Never blanket-catch an error around a configuration call that changes
  measurement semantics.** A swallowed exception turns the setting into a silent
  no-op: the tool keeps running at its default and the numbers look fine. Assert
  the setting took effect instead of trusting the call — if the point of an option
  is to widen a candidate pool, assert the pool is wider than one.
- **Some options cannot be set through the generic setter.** Libraries that
  manage an option themselves reject it with an error and require passing it to
  the call that uses it. Read the error rather than catching it.
- **Testing against a local `file://` path skews network, fetch and font
  behaviour.** Use it for the fixture only; never for a verdict about real input.
- **A test that loads a module by path can read a stale bytecode cache.**
  `importlib` and friends consult `__pycache__`, and the cache key is source size
  plus mtime — so an edit that keeps the file the same size within the same mtime
  second leaves the old `.pyc` in use. The test then passes or fails against code
  that is not on disk, which is how a one-character change to a pin number kept a
  consistency check green. Read the source text and `compile()` + `exec()` it into
  a namespace instead, or clear the cache in the test. Prefer the former: it
  removes the failure mode rather than papering over it.
- **A findings-producing tool must not be the only thing checking itself.** When
  the tool also generates the artifact it inspects, a bug in the tool makes the
  artifact and the verdict wrong together, consistently. Keep an independent
  check (a test, a fixture, a second parse) that does not go through the same code
  path.
- **A red check is a finding, not a defect in the check — triage before touching
  the assertion.** When the tool reports a failure, reproduce the condition with
  an independent call (curl / a direct request / the raw endpoint) and decide who
  is wrong: the tool's expectation or the system. Edit the assertion ONLY when
  the expectation is proven wrong (the endpoint is intentionally open, the shape
  is a documented platform quirk, the value was never meant to be gated). Weaken
  a check to green and you have deleted the finding — the report now lies in the
  permissive direction, which is the dangerous direction. State in the output
  that the case was adjudicated and which side was wrong, so the next reader can
  re-adjudicate instead of re-litigating.
- **A check nested inside a loop that fails on the FIRST item fakes green.** An
  early `return` in an iteration body, or an assertion that skips when its input is
  empty, leaves every later item unverified while the run still reports success.
  Assert the count of items actually adjudicated equals the count expected before
  trusting the verdict, and make the skip-path an explicit finding rather than a
  silent continue.

## Same rule for instructions, not just scripts

When the artifact is a prompt or instruction set rather than a script, the
failure is identical: it asserts what was never verified.

- **Name only capabilities the runner actually has.** An instruction that assumes
  a tool the runner lacks does not fail loudly — the agent invents output to
  satisfy it (a "visual spacing audit" with no way to see pixels becomes
  confident prose about whitespace). List the tools the runner gets, then grep
  the instructions for anything else (browser drivers, GUI control, screenshot
  tools, MCP servers) and rewrite or delete those sections. Renaming the tool is
  not enough when the whole METHOD depends on it — replace the method.
- **Fix the generator, not the generated file.** When the artifact comes out of a
  conversion or template step, correct the converter so the fix survives the next
  regeneration; a hand-edited output is silently reverted on the next run.
- **A regeneration script must not delete what it did not create.** Clearing the
  whole output directory before rebuilding wipes anything else living there —
  including the script itself when it sits beside its output, which then removes
  the file that would rebuild the tree. Remove only the paths the generator owns
  (match its own output naming, e.g. a category-dir prefix), and never `rmtree`
  the output root.
- **State the boundary in the output.** A report should carry what it did NOT
  assess, so a clean result is not mistaken for a passing grade.

## Auditable operational plans

- Deliver the complete requested source, controller, materialization commands,
  inputs, outputs, exit codes, and stop conditions in one auditable package.
  Do not substitute ellipses, comments promising code, or references to an
  earlier response for a requested executable file.
- Pin the bytes submitted for review and compute their hashes independently of
  deployment. Hashing an arbitrary installed script against itself proves
  consistency, not that it is the reviewed artifact.
- Trace the whole execution path, including failure recording and finalization.
  Missing evidence, read/write errors, unexpected object types, skipped required
  checks, and interrupted steps must prevent a successful final status.
- Keep expected output, observed output, syntax validation, fixture execution,
  and production validation separate. A parsed AST or a review of selected
  functions does not establish that the complete controller works.
- Send the exact reviewed scope to the independent auditor and identify any
  omitted source or unexecuted tests. Report an audit as dispatched only after
  an actual handoff; do not call a quick critic-role invocation an independent
  persistent agent.
- Preserve failed-run artifacts for manual investigation. Never make automatic
  deletion or a retry into an existing backup directory the error-recovery path.
- **Revise an audit rejection in staged, prioritized passes.** Return the
  prioritized finding table first and stop; fix every P0 in one pass with a
  finding → fix → file → test table backed by an actual run; stop before P1.
  Closing a finding means the test ran, not that the code was written;
  acceptance of a level belongs to the independent auditor — present code,
  tests and actual output, then stop. When a
  requirement cannot be met, say so and propose a safe alternative — never
  relax the check until it goes green, because a green test after relaxation
  means the finding was deleted.
- **Every re-audit round ships the same artifact set, not a prose summary.**
  1. finding table: `# | finding | status | file:function | test that proves it |
  actual result`;
  2. diff against the previous version for every changed file;
  3. full source of each changed file inline (a reference to an earlier message
  is not code);
  4. raw per-suite result files attached beside the report, with
  `PASS= / FAIL= / SKIPPED=` printed separately and privileged-only cases in a
  second, root-run block;
  5. an “open items” section that names what was NOT closed and why.
  State plainly that the author ran the tests: a suite the author ran is
  self-checked by the author, and calling it an independent verification is the
  claim the auditor will attack first. Close with the stop point — awaiting
  review — never with a verdict.
- **A submission that fails on provider limits is split, not resent.** Cut it
  into independent stages, keep each stage's result on disk, and on a repeat
  failure report which stage stopped instead of restarting from scratch.
- **A hash manifest shipped inside the package is transport, not a root of
  trust.** An in-package checker that hashes its siblings proves consistency:
  replace a file, recompute the manifest, and the check passes. Publish the
  anchor outside the package as literal `sha256sum -c` lines, and state that a
  compromised anchor plus package is undetectable without a signature. Put the
  manifest's OWN sha256 into the anchor and verify it against the anchor before
  parsing its contents — otherwise replacing a file and recomputing the
  manifest passes every downstream check. A `--self-check-anchor` inside a prep
  tool is self-attestation (an edited tool that always passes it will); say so
  and point at the external command as the real gate.
- **Split the bundle into three classes: enforced, prep-exec, test.** Enforced
  (shared library, stage scripts, the gate itself) — mismatch against the
  external anchor is a fatal refusal before anything executes. Prep-exec
  (extractor, manifest builder) — verified against the anchor BEFORE the tool
  runs, and each tool also re-verifies its own sha256 against the anchor at
  startup (`--self-check-anchor`); a warn-only class for tools that run before
  the gate exists is worthless, because they have already executed by the time
  the gate looks at them. Test (the suite itself) — informational, mismatch is a
  warning, kept explicitly separate so a test edit can never block an operator
  run. Compare the manifest's key set against the expected list EXACTLY: a
  missing entry, an unknown entry, and a stray file in the package directory are
  all refusals, and the expected list lives in the gate, not in the manifest
  builder.
- **A bundle cannot bootstrap itself; the trust root is a launcher that is not a
  Python file.** Any self-check living inside the gate script dies with the same
  stroke that edits it: by the time the check runs, the tampered code already
  executed. And a Python launcher is no better — the interpreter runs the file's
  body before the first statement. Write the launcher as a **shell** script whose
  every executed line is a call to an OS utility (`sha256sum`, `stat`, `awk`), so
  no byte of it is interpreted before verification:
  1. **stage-0 validator** (`verify_launcher.sh`): hashes the launcher file and
     NEVER reads or sources its body; on match it `exec`s the launcher. A
     malicious line inserted right after the shebang is therefore never executed —
     that is the only arrangement where the test's claim "marker absent" is true.
  2. **launcher** (`launch_v61.sh`): checks the anchor chain and its own file's
     owner/mode/nlink, verifies the package against the anchor, then copies the
     verified bytes into a private `0700` dir (`0400` files), re-verifies that
     copy, rejects any unexpected object in it, and only then starts the gate.
  3. `run_v6.py` accepts `--exec-dir` (that copy), re-verifies every byte in it
     against the anchor and requires mode `0700` before spawning stages.
  A hand-run `sha256sum -c` stays a documented manual step, never presented as
  automation. State that stage-0 attests itself and is protected only by its
  root-owned directory plus the operator's external check.
- **Anchor protection must extend to its parent directories, and the check must
  skip the anchor file itself.** For every component above the anchor, refuse a
  symlink, a non-directory, an owner outside `{euid, 0}`, and any group/other
  write bit without the sticky bit. Walk the path components and compare by
  component, not by longest common prefix: the final component IS the anchor
  file, so testing it as a directory refuses every valid run.
- **Verify the bytes, then execute those bytes.** Hash the buffer you read,
  write verified buffers into a fresh `0700` directory, and run from there — the
  submitted path can change between check and `exec`. A gate matching its own
  manifest entry is `self_consistency`, not authenticity; label it so.
  Parse the manifest from the SAME buffer whose sha256 you just verified; a
  separate read for authentication and for parsing reintroduces the swap window
  (`read_manifest_once(path, expected_sha)` — hash the buffer, then validate that
  buffer). `run_v6.py` must delay importing ANY package module until after the
  external bootstrap passed — before that, parse the anchor with an inline copy
  of the parser only.

  **Publishing a final status needs one authoritative artifact AND a commit
  marker.** Two files that both claim to be the verdict (`final.json` +
  `rc.txt`) can disagree: write `COMPLETE` to the first, fail on the second,
  and a stale COMPLETE survives on disk even after a retry with `INCOMPLETE`
  fails too. Publish a single `STATUS.json` atomically (temp + fsync +
  `os.replace`), read it back and compare the status, and derive
  `final.json`/`rc.txt` from it afterwards. Delete the derived files BEFORE
  publishing the new truth, so a failure at any later step can never leave the
  *previous* `COMPLETE` behind.

  Atomic rename alone does not protect the *current* run: `fsync` of the
  directory and the read-back happen AFTER `os.replace`, so `STATUS.json`
  already holds `COMPLETE` while the function returns an error. Add a marker
  written last — `COMMIT.json` with the run's `run_id` and the sha256 of
  `STATUS.json` — and let a verdict count only when the marker exists and both
  fields match; otherwise report `INCOMPLETE`. Give each run a unique `run_id`,
  publish `INCOMPLETE` with it in the FIRST stage before any work, and move a
  previous run's files into `runs/<old_run_id>/` rather than reading them: a
  `COMPLETE` left by an earlier run must never be attributable to this one.
  Commit to ONE contract and state it as a formula: either the derived files are
  mandatory — a failed `rc.txt`/`final.json` write rewrites `STATUS.json` to
  `INCOMPLETE`, removes the marker and returns non-zero — or they are optional
  and the exit code stays zero. Leaving the status at `COMPLETE` while returning
  an error code is the contradiction itself: the operator cannot tell which
  artifact is the verdict. With the mandatory variant, test it by placing
  DIRECTORIES named `rc.txt` and `final.json` in the output dir — a
  filesystem-independent way to force both failures — and assert that no file in
  the tree contains `COMPLETE`.

  Prove each finalization step by injected fault instead of reasoning:
  `unlink`, `temp_create`, `write`, `fsync`, `replace`, `fsync_dir`,
  `readback`. Every case asserts the earlier stages at `rc=0`, the final stage
  non-zero, and the effective status not `COMPLETE`. Inject only into the FINAL
  publication — a fault that also fires on the start-of-run `INCOMPLETE` stops
  the controller in the first stage, so the test never reaches the step it
  claims to exercise.
- **Negative tests assert the refusal code, the failing stage and the absence of
  run artifacts** — never just a non-zero exit, which a crash also produces.
  Run the suite as an unprivileged UID when the controller refuses root. Keep
  `__pycache__` out of the package by setting `sys.dont_write_bytecode = True`
  before any in-package import inside the gate itself, and clear stale caches
  before building the manifest: the gate rejecting a stray `__pycache__` is
  correct behaviour, not a bug to tolerate — never teach the gate to allowlist
  it.
- **Test the checked function, not a re-implementation of it.** A test helper that
  rebuilds the validation logic asserts that the helper is right and says
  nothing about the code under test — the two drift apart and the copy keeps
  passing. Import the module and call the real function. If the import fails
  (module-level side effects, `dataclasses` needing `sys.modules[__name__]`,
  relative imports), register the module in `sys.modules` before executing it;
  do not fall back to duplicating the logic in the test.
- **Declare the injection steps once and prove the declaration matches the
  code.** A CLI `choices=[...]` list maintained separately from the code that
  raises the faults drifts silently: advertised steps can have no
  implementation at all, and a test of such a step passes because the run
  succeeds for other reasons. Put the step names in one module-level constant,
  use it as `choices=list(FAULT_STEPS)`, and add a test asserting each declared
  name appears in the source that raises or compares it. Also assert the stage
  under test actually ran (earlier stages at `rc=0`, the final stage non-zero),
  never only the process exit code.
- **A bare-filename `sha256sum -c` anchor verifies only from the one directory
  that holds those files.** With the package in one directory and the launcher in
  another, `cd launcher_dir && sha256sum -c anchor` prints `FAILED open or read`
  for every package entry — the check either reports a false failure or gets
  quietly ignored. Emit a second, path-qualified anchor whose entries are
  relative to a common root and verify it with one command:
  `cd <root> && sha256sum -c <root>/anchor.paths.sha256`; for the package subset
  filter the anchor with `grep -v -E '  (launch\.sh|verify\.sh)$' anchor |
  sha256sum -c -`. Quote the real output and exit code of BOTH commands; "no
  FAILED lines" is a claim about text you have to show.
- **A stage is proven only if that stage runs.** Place the fixture's hook so the
  stage under test is the NEXT one to execute. A hook placed before an earlier
  stage makes that stage fail, the target stage is skipped with its own skip
  code, and the test then "passes" by comparing files itself — that is
  self-certification, not evidence. Assert the stage's `rc` from the run record
  and read the artifact the controller wrote; never accept a value the test
  derived on its own.
- **Count SKIPPED separately from PASS.** Privilege-gated cases (a `chown`, a
  `chmod` on a root-owned tree) report `SKIPPED` under an unprivileged UID, and
  the summary must print `PASS= / FAIL= / SKIPPED=` as three separate numbers;
  then run them again under root in a second pass instead of letting a skip
  read as success. Keep the root-only sandbox under a root-owned parent —
  creating it inside the unprivileged workdir makes the privilege check fail
  for the wrong reason and produces a false failure.
- **Pass an absolute system interpreter when running the suite as another UID.**
  `sys.executable` can point into the agent's own root-only tree, so the child
  either cannot start or cannot reach its stdlib; `setpriv ... /usr/bin/python3`
  is deterministic. Export `TMPDIR` for that UID as well — `mktemp` inherits it,
  and the agent's private `0700` scratch is unreadable to the test user. Do not
  add `-I` to a relocated interpreter's invocation: it can drop the stdlib path
  (`ModuleNotFoundError: encodings`); `-B` is enough to suppress bytecode.

For a self-verifying multi-file bundle that must prove its integrity before
running, load `references/package-integrity-gate.md`.

For backup scripts and live-data consistency (SQLite backup direction, WAL
sidecars, jobs snapshots, fail-closed finalization), load
`references/fail-closed-backup-validation.md`.
For independent auditor boundaries and safe bootstrap tests, load
`references/auditor-isolation-validation.md`.

### Required backup report format

For Георгий, keep these seven blocks separate; do not compress them into a
single success summary or invent values for an unexecuted check:

1. Sizes of all backup subdirectories from `du -sh`.
2. File counts separately for the static copy and SQLite snapshots.
3. One row per discovered SQLite database: name, actual `journal_mode`, full
   `integrity_check` result, table count, `SHA256[:16]`, size, and elapsed time;
   separately reconcile found, saved, and unprocessed databases with reasons.
4. SHA256 summary: record counts in both source/destination manifests and the
   actual `diff` return code and result.
5. Each approved stage's return code on its own line; retain requested labels
   such as S0–S8. Mark unexecuted stages `NOT_RUN`, never zero.
6. Exact final `STATUS.txt` value: `COMPLETE` or `INCOMPLETE`. Treat absent or
   unverifiable completion evidence as incomplete, including after interruption.
7. Separate `WARNING` and `ERROR` lists, including an explicit empty result when
   the corresponding list was actually checked.

## Verification

Before reporting a tool's findings as trustworthy:

- [ ] Fixture exists and every declared defect class appears in its summary.
- [ ] Real-input run performed; every finding read against its source and
      bucketed true / artefact / unknown.
- [ ] Artefacts found on real input were fixed in the detection logic, then both
      passes re-run.
- [ ] Thresholds cite their standard's level; exemptions are separated, not
      silently dropped.
- [ ] Unmeasurable cases are listed with a reason rather than given a number.
- [ ] The identical command was run twice and produced identical output; any
      non-reproducible mode is labelled as such in the output.
- [ ] Every option that changes what is measured was asserted to have taken
      effect, not merely requested.
- [ ] Any estimated metric was calibrated against real rendered output, and the
      estimate was sanity-checked on one known case before the full pass.
- [ ] If the tool also generates what it inspects, the consistency check was
      proved to fail on a deliberately injected mismatch.
- [ ] If the bundle verifies itself, the anchor lives outside it, the enforced /
      prep split is stated, and each negative test asserts the refusal code,
      the failing stage and the absence of run artifacts.
- [ ] A path-qualified anchor was verified from the common root, and the real
      output plus exit code of every `sha256sum -c` command is in the report —
      no `FAILED open or read` anywhere in it.
- [ ] No test re-implements the function it checks: the module was imported and
      the real function called.
- [ ] The fault-injection step list is declared once, used as the CLI choices,
      and a test asserts each step exists in the code.
- [ ] Status/exit-code contract is stated as a formula, and the commit marker is
      published last and validated before any result is trusted.
- [ ] The output states what was not checked.
