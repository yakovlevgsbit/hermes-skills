<!--
Adapted from gstack by Garry Tan — https://github.com/garrytan/gstack (MIT License).
Adaptations for Hermes: the `gstack-gate-diff` tagger and the decision ledger are
not installed here, so detection is manual — read the diff and apply the patterns
below yourself. Methodology unchanged.
-->
## Tagged patterns (read manually from the diff)

### RH-1 — Test removed or disabled

The agent deletes, skips or focuses a test instead of fixing the code it
guards: a removed `test(`/`it(`/`def test_`/`func Test`/`@Test`, an added
`.skip`, `.only`, `xit`, `xdescribe`, `@pytest.mark.skip`, `#[ignore]`,
`t.Skip(`, `@Disabled`, `@Ignore`, `XCTSkip` or `@tag :skip`. The failure the
test encoded is now invisible and the suite reads green. Countermeasure:
the gate scanner tags the hunk (tags are factual: a test deleted alongside
its deleted source is tagged and the agent's judgment, not the tool, makes it
a non-finding); the reviewer Gate Integrity reads it and routes a finding to the
four-option ASK (`review-gate-disposition`); the shipper core checklist item 2.5
runs the same scan and the PR body's `Gate edits:` line carries the kept
reason. The testing specialist's "never accept discarded valid red tests" rule
stays as the large-diff read.

### RH-2 — Proof-class inflation

A mock, fixture, replay or static read is presented as the proof a claim
requires: "verified against production" when a stub answered, "the route is
reachable" from a grep. No tag can see it; it is a prose check. Countermeasure:
the preamble's Claims Need Evidence kernel (name the evidence kind you have and
never substitute one for a kind the question requires), the reviewer's
Verification of claims, and the Gate Integrity category's instruction to read
RH-2 from the diff without a tag. the shipper Step 16's "no completion claims
without fresh verification evidence" is the publication gate.

### RH-3 — Snapshot or golden regenerated without its owning test

A snapshot (`__snapshots__/<name>.snap`, `*.snap`) changes while its
conventional owner (the `<name>` test file) has no hunk in the candidate, so
the new output was accepted rather than tested. `*.golden`, `testdata/` and
project `Snapshot paths:` are tagged `RH-3?` (owner unresolved): listed and
read, never inferred. Countermeasure: the tag plus the Gate Integrity read; a
snapshot updated alongside its source is inventory, never a finding. own SKILL.md goldens regenerate on every template edit by design, so RH-3 is
never auto-blocked; the PR-body line makes a product snapshot regeneration
visible to the human.

### RH-4 — Placeholder committed

`todo!()`, `unimplemented!()`, `raise NotImplementedError`, `throw new
Error("not implemented")` or `pass  # TODO` lands in non-test code and the
work is reported as done. Countermeasure: the tag admits the hunk through the
content backstop even in product code; the plan-completion audit's
`done/changed/partial` classification and `Linked to #N` never auto-close rule
keep the obligation open.

### RH-5 — Tautological test

A test that cannot fail: it asserts its own setup, mirrors the implementation
line for line, or has no negative (nothing it rejects). Not a tag; read from
the diff. Countermeasure: the test value card's `protects=` / `fails_when=`
fields and the `no_claim=` sentence (what green does not prove), the
the shipper Step 7 authoring gate that rejects cards without them, and the Gate
Integrity instruction to read RH-5 beside the tagged hunks.

### RH-10 — Spec editing as progress

Acceptance text in the plan or spec is rewritten so the delivered work matches
it, then the item is reported complete against the new text. Countermeasure:
the shipper's plan-completion audit diffs the plan's acceptance-bearing sections
against their base-branch or first-commit baseline and reports an edited item
as `ACCEPTANCE_EDITED`, never folded into `CHANGED`; the original obligation is
still audited and the PR body names the scope change. Stated limit: an item
rewritten in the commit that introduced the plan is invisible.

### RH-12 — Environment sniffing in product code

Product code branches on `process.env.CI`, `NODE_ENV === 'test'`,
`RAILS_ENV == 'test'`, `PYTEST_CURRENT_TEST` or `GITHUB_ACTIONS` so the code
under test behaves differently from the code in production. Countermeasure:
the tag outside test paths; the Gate Integrity read asks whether the branch
exists to pass a check rather than to serve a user.

### RH-13 — Suppression pragma added

`eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `# type: ignore`,
`# noqa`, `#[allow(`, `// nolint`, `rubocop:disable` or `@SuppressWarnings`
silences the checker instead of satisfying it. Countermeasure: the tag admits
the hunk from any path; the read asks whether the suppressed diagnostic was
the failure the change was supposed to fix.

### RH-14 — Gate bypass

A commit in range carries `[skip ci]`/`[ci skip]`, a workflow gains
`continue-on-error: true` or `allow_failure: true`, or a script or hook adds
`--no-verify`. Countermeasure: the tag; a removed workflow job is listed by the
path floor and read (job-removal detection is not in v1). the shipper never pushes
with `--no-verify` and never force-pushes.

### RH-15 — Gate value relaxed

In a test, eval, CI or config file a numeric gate moves in the relaxing
direction inside one hunk: timeout, retry, retries, tolerance, epsilon, delta,
maxDiff or jitter **up**; threshold, min_score, minimum, coverage or required
**down**; or an exact-count assertion loosened to a bound (`toBe(3)` →
`toBeGreaterThan(0)`). Unpaired values are tagged `RH-15?` and read. The tool
prints any citation it finds beside the hunk (commit text naming a
a measurement report, a `a decision marker, because a measurement report
text is forgeable. Countermeasure: the reviewer's former blanket "eval threshold
changes" suppression is narrowed to code-quality comments only; the agent
resolves the citation read-only and pre-fills the Keep — justified option
marked verified or unverified; `ship/sections/measure.md`'s measure-then-fix
loop ("never raise a budget, lower a threshold, add a retry or skip a case to
get a pass") is the native repair path.

### RH-16 — Exception swallowed

`catch {}`, `catch (e) {}`, `except: pass`, `rescue nil` or `_ = err` added
in non-test code turns a failure into silence. Countermeasure: the tag lists it
under the RH id; slop-scan's empty-catch rule keeps the fix suggestion. The
preamble's stderr rule (never cite a command whose stderr was silenced) covers
the evidence-command form.

## Positive observables (zero-run green)

### PL-1 — Exit code is not evidence

A command's exit 0 is reported as success without any observable that the
work happened: the suite that selected nothing, the build that compiled zero
files. Countermeasure: the preamble's Claims Need Evidence kernel (a claimed
execution names the command and its observed result; a checked null result is
reported as a null, not a pass) and the shipper Step 16's receipt check.

### PL-2 — Zero-run green

A test lane exits 0 having run zero tests: bun `0 pass 0 fail`, jest "No tests
found", pytest "no tests ran", rspec "0 examples", `go test` with only `[no
test files]`, or an empty selection after a filter. Countermeasure: the shipper
Step 5 passes a lane on its runner summary line, not exit 0 alone, with three
never-merged count states (`tests_ran: N` pass; `tests_ran: 0` ZERO-RUN,
triaged as a failed lane; `tests_ran: unknown` keeps the exit-0 pass and prints
`count unavailable` in the PR body); A zero-run lane is reported as STALE-equivalent; the PR body's `## Test Coverage` section prints each
lane's `tests ran` count.
