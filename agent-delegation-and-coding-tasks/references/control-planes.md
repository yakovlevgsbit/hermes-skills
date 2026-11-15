# Evaluating and using agent control planes

Use when an application coordinates agent roles, tasks, schedules, approvals and costs. Keep the project-specific source review in `/root/kb/projects/paperclip.md`; the rules below are reusable.

## Separate the control plane from the work

A role, org chart or company goal does not provide the executor's expertise, a correct strategy, customers or completed work. Identify the actual runtime and how it receives task context, reports progress, persists a session and proves completion.

Compare a new dashboard with existing agents and deterministic workflows before proposing a migration. Add it for a demonstrated coordination, audit or accounting gap, not merely to rename scripts as employees.

## Make the adapter contract explicit

Check the implemented adapter, not only a compatibility logo. A local CLI, managed sandbox, remote agent API and generic webhook have different permission and cancellation boundaries. Source support is not a tested installation on this host.

A process exit or HTTP 2xx may mean only that a command finished or a job was accepted. Long-running services need task/run IDs, idempotency, completion callbacks or polling, evidence paths, error states and usage attribution. Do not mark the task done from an acceptance receipt.

Verify API availability separately from UI availability; an adapter can exist while its dropdown entry is disabled. A health probe does not prove the real authenticated work/cancellation path.

## Inspect runtime authority

Inspect actual command flags, inherited environment, profile/home resolution, tool sets, workspace selection and helper processes. Noninteractive adapters may add approval-bypass flags automatically. A comment saying agents run in a sandbox is not proof a sandbox is configured.

Use separate operator-approved profiles/credentials/workspaces for independent agent workers. Do not reuse the production manager's home merely because a CLI can find it. Conversation/session keys do not isolate all persistent memory, files or secrets. Git worktrees and checkpoints are not OS/network isolation.

Do not restart or replace a live gateway as incidental onboarding. Use only explicitly authorized API access and verify API identity, transport security and run correlation. A dashboard URL is not proof its agent-run API is configured.

## Verify governance in the effective policy

Trace an approval from request through authorization, pending state, decision and activation. Determine whether the rule is always enforced or controlled by a company/project flag; inspect stored values after setup/import instead of trusting a walkthrough's defaults.

A CEO title is not a security boundary. Hiring authority, changing configuration, spending, external messages and production writes need separate grants. An approved task does not automatically authorize arbitrary local shell actions or third-party side effects.

Read the full hire request: adapter, working directory, environment/secret references, reporting line, budget and tool permissions, not just its friendly role name. Test that an unapproved hire cannot run and that rejection/resume behave as intended before relying on the workflow.

## Account for spend and stop semantics

Identify the accounting basis: provider-reported dollars, estimated token prices, subscription allocation, prepaid credits or separate account invoices. Subscription usage is not necessarily an incremental per-call fee, and a dashboard estimate is not a provider invoice.

Trace warning thresholds, admission checks, active reservations, in-flight usage, delayed receipts, unknown/unpriced work and actual cancellation. A pause that blocks future runs is not necessarily an immediate stop of an already charged request. Check cancellation at the executor and descendant/remote-job boundary.

Require explicit caps, concurrency limits, task/turn timeouts and permitted destinations for a pilot. Verify zero-value and disabled-policy semantics: a zero budget may disable enforcement rather than prohibit spending. Do not promise an exact external bill ceiling without a provider-side mechanism and verified reporting/overshoot behavior. Treat unknown cost explicitly; do not convert missing usage to free work.

Keep a safety margin below the real spending ceiling and reconcile invoices when cost matters. Do not rerun an expensive task merely to recover a lost accounting receipt.

## Deploy and verify narrowly

Research stays read-only. For an authorized pilot, use a separate instance/store and non-sensitive work, inspect the installation/first-run footprint, and verify cleanup. A single controller container is not automatically per-agent isolation.

Check bind address, authentication, TLS, secret storage, telemetry and backups separately. Private exposure settings are not a firewall; published container ports may listen more broadly than expected.

Completion means the original acceptance criteria passed, including correct output and external read-back where relevant. Logs, green status and generated summaries are evidence to inspect, not substitutes for verification.
