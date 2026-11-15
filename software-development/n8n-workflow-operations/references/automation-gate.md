# Automation Gate — before you build it

A workflow that saves ten minutes a week and pages you at 3am is a net loss.
Run this gate before building a new workflow and before extending an existing one.
The answers go in the report to the user, not in your head — a gate answered
silently is a gate that was not run.

Distilled from `agency-agents` / `automation-governance-architect` (MIT).

## The eight questions

### 1. Value vs fragility

What breaks if this stops silently for a day? If nobody would notice, it is not
worth owning — a manual step costs less than a system nobody watches.

If it moves money, messages clients, writes to a live table, or touches a
schedule, it needs every item below and it needs an error branch.

### 2. Owner and failure path

Who is told when it fails, through which channel, and what does the system do
meanwhile — retry, queue, fall back to manual, or stop cleanly?

A graph with no error branch already has an answer: **it silently stops.** That
is not a failure path, it is a coin flip. Concretely: an `Error Trigger`
workflow, or an `onError: continueErrorOutput` branch wired to a notification
node, plus the decision of what the user sees when the chain aborts.

### 3. What stays human

Name the steps that must not be automated. The usual set, in this order of
danger:

- deleting rows or files;
- sending anything to a client or a public channel;
- changing prices, quotas, or access rights;
- publishing (site, post, release).

A human-in-the-loop node (`Wait` on webhook approval, a draft row with
`status='pending'`, a confirmation message) belongs **in the graph**. A comment
saying "review before sending" is not a control.

### 4. Idempotency

Firing twice must not post twice or insert twice. Every replay path does it:
webhook retries, manual re-runs, `catch-up` executions after downtime, a
re-activated workflow replaying queue.

Key the write on a stable id — `message_id`, row id, a hash of the source event —
never on arrival time and never on "it probably did not run yet". Where the API
has no natural key, keep a processed-ids table and check it in the same node that
writes.

### 5. Uncapped spend

Every loop, retry and paid API call gets a cap **and** a timeout.

An LLM node inside a loop with no limit is a bill, not a feature. A retry without
a cap turns a one-hour provider outage into a week-long one. Check the count, not
just the presence of a `maxRetries` field — some nodes accept the key and ignore
it.

### 6. Secrets

Credentials live in the credential store and are referenced by `{id, name}`.

A key pasted into a node body lands in plaintext in every workflow export and
every backup you take. After the first publish, assert the secret appears zero
times in the re-fetched workflow JSON.

### 7. Rollback

Before the first publish: the full graph in `/root/n8n-backups/` (that is the
house convention), plus **one sentence** on how to disable the thing — which
node to deactivate, which file to restore, what the manual procedure is while it
is down.

A rollback plan you cannot execute at 3am is not a rollback plan.

### 8. Boundaries

One line on what this workflow deliberately does NOT do.

This is the guard against scope creep on every future edit: read that line out
when someone asks for "just one more branch", and say whether the request is
in scope or a new workflow.

## Verdicts

One of three, stated plainly:

- **build** — all eight answered, error branch and rollback in place.
- **build with a human gate** — value is real, but one of the steps in §3 must
  stay manual; the approval node is part of the deliverable.
- **do not build** — the manual process is cheaper. Say so and name what would
  have made it worth it (volume up, error rate down, an API appearing).

## Non-negotiable

A live production graph is changed only after an explicit yes from the operator,
with the diff shown first. No "done" on a write you cannot read back.
