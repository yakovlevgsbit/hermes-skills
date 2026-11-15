---
name: deploy-agents
description: "Use when building an agent that deploys to production."
version: 1.0.0
author: Hermes Agent (Мария)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [deploy, agent, production, rollback, dry-run]
    related_skills: [n8n-workflow-operations, qa-agent-production-suites]
---

# Deploy agents

## When to use

Building or running an agent whose job is to push a change into a live system —
a workflow, a service, a config, a panel. The class-level question is not "how
do I write this file" but "how do I make the deploy safe enough to run on
production, and honest enough to trust".

The concrete REST surface belongs to the platform skill (see
`n8n-workflow-operations` for n8n); this skill is the deploy procedure, the
safety gates and the reporting shape.

## Non-negotiable: dry-run by default

A deploy tool that writes unless you pass a flag will eventually write when you
meant to look. Invert it:

- **Default = plan/diff.** No flag, no write.
- **Write requires an explicit opt-in** (`--apply`, `--yes`).
- Print the count of what *would* change and the report path, so the reader can
  see the run was inert.

The plan and the apply must share one comparison function. Two code paths
means the plan lies about what apply does.

## Source of truth + history

Pick one authoritative location for what should be deployed, and version it.

- Local `workflows/` (or `configs/`) directory + a git repo inside the agent
  folder is enough when the projects themselves are not git-tracked. Check
  first: `git -C <project> rev-parse --is-inside-work-tree`.
- Provide an `--export` command that pulls live state into the source of truth.
  The first export is the baseline; without it there is no diff to reason about.
- Compare against the **comparable** part only. Strip read-only/platform-managed
  fields before diffing, or every run reports a difference that is not a
  difference and the tool becomes noise.

## Restore state on failure — the rule that matters most

Any deploy that changes *state* (active/inactive, enabled/disabled, running/
stopped) must put it back when the step after it fails.

The failure that teaches this: deactivate succeeds, the write fails, the tool
reports an error and exits. The service is now down and the error message says
nothing about it. On a production trigger this is an outage, not a failed deploy.

Wrap the sequence in try/except and **re-apply the previous state on any
exception**. Report both the original error and the restore result, and fail the
run if the restore itself failed — a silent restore failure is the worst case.

## Back up before the first write of a run

Snapshot the current live state to a timestamped file before any mutation. Name
it so the ordering is obvious (`<ts>-<id>-PRE-deploy.json`). Then the revert is
one copy plus one apply, and you never reconstruct the old state by hand.

## Verify against live state, never against your own success code

After a write, read the entity back and assert the field you changed. A 200 from
the writer plus a green log line is not evidence the value landed — platforms
merge defaults, drop keys, or normalise on read. State what you read back.

## Destructive actions: resolve scope before touching anything

"Удали всё", "удали его", "снеси" — a request whose scope is the whole machine
reaches live credentials, running services and money paths that the user
mentioned nowhere. Deletion is irreversible; a wrong deletion costs credentials
that can only be reissued by a third party (a bot token, a payment-provider
API key), which is a client-facing outage, not a local annoyance.

**Before executing, inventory what the request would touch and split it into
three tiers:**

1. **Clearly in scope** — the thing under discussion, named by the user.
   Delete it.
2. **Adjacent and live** — a secrets file that also holds OTHER providers'
   keys, a running systemd unit, a database with real rows. Do NOT delete
   silently. Name it, and say what is irreversibly lost.
3. **Unrelated but caught in the blast radius** — a directory the command
   happens to sit inside, a shared volume. Leave it.

Then state the three tiers in the reply and get the tier-2 decision confirmed.
The cost of asking is one exchange; the cost of guessing wrong is a payment
bot whose token no longer exists.

**Secrets files are multi-credential.** A file named for one provider often
holds the Telegram token, the admin id, the payment-provider key and the
crypto key together. Deleting the file destroys all of them at once, and the
names the user remembers («удали KIE») point at only one of the four. Split
the file or delete only the line that matches.

**An approval timeout is a STOP, not a no-op.** Destructive commands gated by
user approval can time out with the command still unrun — the tool reports
"not consented" and the filesystem is untouched. Do not re-fire the same
command in a loop hoping it lands: a timeout means the confirmation never
reached the user, so state what is still present and wait. Two attempts at
the same gated deletion is already a smell that the scope is wrong.

**"Всё" is not a scope, it is a mood.** When the user says everything, ask
which tier they mean — but do the tier-1 work FIRST and describe tier 2 in
the same message, so the answer is a single confirmation rather than a
round-trip that stalls the obvious part.

**Before deleting a directory, check what is inside it that is not a
generated artifact.** Generated caches and build output go; a secrets dir, a
database, or a directory with a `data/` that grew today is not. The
timestamps tell you: a file modified minutes ago is someone's live work.

## Report shape

- JSON for the machine, Markdown for the human, both timestamped.
- Per item: state (`in-sync` / `changed` / `not-found`), the diff, whether it was
  applied, the backup path, and any error.
- **Count changes separately from applies.** `changed=1 applied=0` in a dry-run
  is correct; a summary line that prints `0` because it only counts successful
  applies makes a detected change look like nothing happened.
- Non-zero exit on any error, zero only when the run was clean.

## Interpreter and environment

Pick the interpreter that has the HTTP deps rather than assuming `python3`.
A bundled/agent python without `requests` turns every deploy into
`ModuleNotFoundError`, which reads like a broken script and sends you debugging
the code instead of the environment.

```python
PYTHON_CANDIDATES = ["/usr/bin/python3", "/usr/bin/python3.12", "python3"]
def pick_python():
    for cand in PYTHON_CANDIDATES:
        r = subprocess.run([cand, "-c", "import requests"], capture_output=True)
        if r.returncode == 0:
            return cand
    return sys.executable
```

## Keep the deploy idempotent and test it that way

Prove idempotency by exporting, planning (expect zero changes), then planning
again after a real change. If a no-op run reports differences, the comparison is
wrong — usually because a read-only or platform-normalised field was included.

## Test the tool on a non-critical target

Exercise the full write path on something disposable or low-traffic before it
touches the production-critical item. A deploy tool is code that mutates live
state; treat it like production code and run it once where a mistake is cheap.
Revert your own test change and confirm the revert lands.

## Pitfalls

- **Never leave the service in the mutated state after a failed step.** See the
  restore rule above — this is the one that causes outages.
- **Do not trust your own summary line.** Print the per-item state alongside the
  count so a wrong counter cannot hide a real change.
- **A `200` from the writer is not a read-back.** Re-fetch and assert.
- **Exported state is not a stable identifier.** Platform-managed fields
  (`id`, `active`, version counters, timestamps) change between reads; match
  items by a stable key and compare only the fields you intend to own.
- **A setting you add may be impossible to remove.** Verify the revert path
  before shipping a change that introduces a new field, or the tool will drift
  the live system away from its own source of truth.
- **An export taken after ad-hoc probing is not a baseline.** While debugging you
  will poke live state by hand — a curl here, a setting flipped there. If you then
  run `--export`, the source of truth silently captures the *modified* state, and
  a later "revert by re-export" does nothing. Keep the earliest pre-change backup
  as the revert source, and when you cannot tell which snapshot is pristine, say
  so rather than reverting from the newest export.
- **Clean up your own debug artifacts.** Every probe that writes (a test row, a
  temp job, a debug backup) belongs in an inventory you remove and read back, the
  same discipline as a live test. A debug backup left in `backups/` becomes the
  baseline the next session trusts; a probe row left in the DB is a defect
  someone else will chase.
