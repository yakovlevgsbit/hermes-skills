---
name: second-brain-kb
description: "Use when managing project KB or Honcho agent memory."
version: 1.1.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kb, second-brain, notes, projects, ops, knowledge-management]
---

# Second Brain — /root/kb/

Durable knowledge base for projects, infra and clients. Hermes memory holds only one-line pointers; this holds the substance.

## When to Use
- A fact is asked for a second time, or will be needed next week → write it here, not to memory.
- Starting or deep-diving any project: read the relevant `/root/kb/projects/*.md` first.
- Touching infra (n8n, nginx, secrets, Supabase) — read `/root/kb/ops/` first, especially before production writes.
- After any production change: update the project note in the same session.

## Layout
```
/root/kb/
├── INDEX.md      # map, single entry point
├── README.md     # rules and note format
├── projects/     # one file per project/service
├── ops/          # infra: n8n, nginx, secrets, vps
├── clients/      # per-client notes
└── _archive/     # dead projects, moved not deleted
```

## Rules
1. **One project, one file.** Cross-link with `[[projects/other]]` / `[[ops/thing]]`.
2. **Facts, not chronology.** Write how it works *now*; no "in October we discussed".
3. **Never store secret values.** Paths only (`token in /root/.secrets/tokens.env`).
4. **Update `updated:` frontmatter on every edit.**
5. **Memory keeps one pointer per project.** If a memory entry duplicates a KB file, shrink it to `Project X: details in /root/kb/projects/x.md`.
6. **Dead projects go to `_archive/`,** stay searchable, out of INDEX's active table.
7. Git-tracked; commit after substantive edits.

## Honcho and shared conversation memory

Keep verified project facts in this KB and repeatable procedures in skills. Honcho is an optional conversation-recall layer, not a replacement for either. For evaluation or integration, read [references/honcho-memory.md](references/honcho-memory.md): identity mapping, local/API/MCP egress, safe pilots, updates and forgetting. The evidence-backed research note is `/root/kb/projects/honcho-second-brain.md`; verify runtime state separately.

## Automatic episodic memory capture

Treat an automatic observer as an additional data system, not as proof that every event is remembered. Distinguish capture, enqueue, durable write, summary generation and successful recall. Test long tool outputs, truncation, queue overflow and restart recovery before relying on it.

Map local storage, embeddings, observer inference, telemetry and cloud sync separately. Verify failover destinations as well as the normal provider; a local database or one disabled cloud flag does not imply no external processing. Check paid-trial allowance exhaustion, automatic upgrades and overages before enabling hosted observation.

Verify privacy filters against the target host's actual tool names and payload fields before capture/storage/network. A filter for `Bash` may not cover `terminal`. Project labels and retrieval filters are not tenant access controls.

Trace replacement/deletion across every copy: native memory, observer notes, vector indexes, transcripts, backups, sync and logs. Native `memory` deletion does not prove a mirrored record was deleted. Keep curated KB facts authoritative over generated summaries, with source provenance and explicit corrections.

Current example and source audit: `/root/kb/projects/claude-mem.md`. A real host adapter proves an integration path, not tested compatibility with the active runtime.

## Before a production write
Read the project note + relevant ops note, make a backup (/root/n8n-backups/ for n8n workflows), then write. Present the diff to the user first.

## Recovering a project named by a path or slug

Treat `/project-name/` as a project or deployed route first, not as a skill name. Search the actual filesystem with `search_files` (including `/root/` and known executor output directories), then the KB and `session_search`; an absent skill or KB note is not evidence that the project does not exist.

Read the project's contract, approvals, artifacts and actual target before reporting status. Separate source completion, saved test evidence, independent review, live-provider testing and publication. Count test rows and compare stored hashes to current files rather than repeating a child summary. Preserve expired/cancelled production approvals as gates; a status question does not renew them.

Add a missing project note and INDEX link during recovery so the next session can find the project directly. Record current facts and remaining gates there, not in always-loaded memory.

## Answering "what agents do I have?"

**Agent executables live in `/root/`, NOT in `/root/.hermes/`.** Searching only
`.hermes` (skills, plugins) returns a false "there are no agents" — that exact
mistake produced a wrong answer to the user in a Telegram session, twice.

Always resolve the list from the filesystem before answering:

Use `search_files(path="/root", target="files", pattern="*agent*", limit=100)` and a scoped search for `web-assistant`; inspect executable project directories rather than treating every matching dependency or skill as an agent.

Then read `/root/kb/INDEX.md` (section «Агенты») — it carries the full table with
paths and roles. The list as of 2026-10-16: **maps-agent (Крыса)**, **web-assistant**,
**content-agent**, **artists-agent**, **research** (lead scanner), **prompt-demo**.

Three distinct things the user may mean by "agents" — say which one you are listing:
1. **Agent executables** — real programs with code, tasks/ and output/ (`/root/*agent*`).
2. **Delegation roles** — 163 expert prompts at `/root/.hermes/subagents/`, pasted into
   a `delegate_task` brief. Not programs; a menu of expertise (skill: `subagent-library`).
3. **Role teams** — multi-agent pipelines like `designer → frontend-dev → qa-verifier`
   in `/root/kb/agents/web-dev/`.

When a new agent is built, add it to `INDEX.md` **in the same session** — an agent
missing from the index is an agent the next session will deny having.

## Pitfalls
- Obsidian skill resolves its own vault path via `OBSIDIAN_VAULT_PATH`; this KB is NOT the Obsidian vault. Do not use the obsidian skill here — use plain file tools.
- `/root/kb` was verified present on 2026-10-09 with 11 notes and a git repo initialised.
- Honda Stepwgn is Георгий's production project (`projects/honda-bot.md`), despite older notes calling it foreign. Its workflow shares the n8n instance with other bots; never edit it as collateral work on another project, and require an explicit Honda-scoped request before changing it.
