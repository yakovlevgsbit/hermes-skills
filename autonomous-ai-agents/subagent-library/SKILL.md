---
name: subagent-library
description: "Use when delegating work to a specialist subagent."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [delegation, subagents, delegate-task, specialists, catalog, roles]
    related_skills: [agent-delegation-and-coding-tasks, subagent-driven-development, requesting-code-review]
---

# Subagent Library

163 specialist role prompts, converted from
[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
(MIT) into Hermes form. They live at `/root/.hermes/subagents/<category>/<name>.md`.

Each file is a **role prompt**, not a runnable program. You use it by pasting its
body into a `delegate_task` brief. The library is a menu of expertise, not an
executor — nothing here runs on its own.

## When to Use

- A task needs domain depth you would otherwise improvise (payment flows, Docker
  hardening, SQL tuning, conversion copy, competitive teardown, security audit).
- You are about to write a long brief and would rather start from a vetted one.
- The user names a role ("запусти code-reviewer", "нужен аудитор безопасности").

Don't use for: a single tool call, mechanical multi-step work (`execute_code`),
or anything needing user interaction — subagents cannot ask questions.

## Procedure

1. **Pick the role.** Match the task to a name in the selection table below, or
   browse the full list with `skill_view('subagent-library', 'references/full-catalog.md')`.
   When two fit, prefer the more specific one.
2. **Read the prompt**: `read_file(path='/root/.hermes/subagents/<category>/<name>.md')`.
   Skip the frontmatter; the body from the first line after `---` is the prompt.
3. **Compose the brief** with the template below. The subagent sees ONLY what you
   pass — no conversation history, no memory, no skills, no context files.
4. **Spawn** via `delegate_task`. Independent roles go in the SAME call so they run
   in parallel (max 10 per call).
5. **Verify before reporting.** Open the artifacts it named and check them yourself.
   A subagent saying "tests pass" is a claim, not evidence.

## The brief template

A subagent that improvises is a subagent that fabricates. Fill every slot:

```
GOAL
<one paragraph: what must exist when you are done.>

ROLE
<the body of the chosen subagent file, pasted in full.>

CONTEXT
<absolute paths to read, the stack, the constraints, what is already known.
Include the production-vs-test distinction explicitly.>

DELIVERABLE
<exact absolute output paths, or the exact command to run.>

VERIFY
<how the parent will check it: command to run, file to open, expected shape.>

DO NOT
- Touch <production system / live DB / other directories>.
- Report success you did not verify. If blocked, stop and say so.
```

## Selection table (recommended for this stack)

| Need | Role | Path under `/root/.hermes/subagents/` |
|---|---|---|
| Code review, ship/no-ship verdict | `surgeon-reviewer` | `04-quality-security/` |
| Broad code review w/ standards | `code-reviewer` | `04-quality-security/` |
| Root-cause a bug | `debugger` | `04-quality-security/` |
| Security audit | `security-auditor` | `04-quality-security/` |
| Performance bottlenecks | `performance-engineer` | `04-quality-security/` |
| Tests | `test-automator` | `04-quality-security/` |
| Clean up messy code | `refactoring-specialist` | `06-developer-experience/` |
| Build a web panel / mini-app | `frontend-developer`, `fullstack-developer` | `01-core-development/` |
| Backend / bot API | `backend-developer`, `fastapi-developer` | `01-core-development/`, `02-language-specialists/` |
| Python work | `python-pro` | `02-language-specialists/` |
| Telegram/MAX webhooks | `webhook-engineer` | `01-core-development/` |
| n8n / cron / deploy pipelines | `devops-engineer`, `deployment-engineer` | `03-infrastructure/` |
| Docker | `docker-expert` | `03-infrastructure/` |
| Supabase / Postgres / SQL | `postgres-pro`, `database-optimizer`, `sql-pro` | `05-data-ai/`, `02-language-specialists/` |
| Google Sheets / data pipelines | `data-engineer` | `05-data-ai/` |
| LLM prompts for a client order | `prompt-engineer` | `05-data-ai/` |
| Payments (Stripe/TG/MAX) | `payment-integration` | `07-specialized-domains/` |
| Landing page copy | `landing-page-copywriter` | `08-business-product/` |
| Strip AI-isms from client text | `content-quality-editor` | `08-business-product/` |
| SEO | `seo-specialist` | `07-specialized-domains/` |
| Telegram ad vetting | `telegram-ads-analyst` | `08-business-product/` |
| Idea go/no-go | `project-idea-validator` | `10-research-analysis/` |
| Competitor teardown | `competitive-analyst` | `10-research-analysis/` |
| Plan a multi-agent workflow | `agent-organizer`, `multi-agent-coordinator` | `09-meta-orchestration/` |
| README / docs | `readme-generator`, `documentation-engineer` | `06-developer-experience/` |

78 of the 163 are marked `recommended: true` in their frontmatter. The rest are
legit but niche for this stack (PowerShell, Azure, .NET, healthcare, blockchain,
quant) — usable, just rarely worth the token cost.

## Pitfalls

- **The subagent has zero shared context.** It cannot see this conversation, the
  memory file, or the skills. Every path, constraint, and definition it needs goes
  into CONTEXT. This is the #1 cause of a subagent inventing a solution to the
  wrong problem.
- **Paste the role prompt, do not summarize it.** The converted files are 3-11 KB
  of accumulated expertise; a one-line paraphrase throws that away.
- **Subagent summaries are self-reports.** For any external side effect (upload,
  remote write, publish, deploy), require a verifiable handle — URL, ID, absolute
  path — and check it yourself before telling the user it succeeded.
- **A subagent cannot close tracked work or ask a question.** If the brief has a
  genuine fork, decide it yourself before spawning.
- **Converted files are clean of Claude-isms but still generic.** They assume a
  fresh greenfield project unless CONTEXT says otherwise; say "this is a live
  production bot, back up first" when it is.
- **Do not let the library pick the agent.** You choose the role; the library is
  not an auto-router. Guessing a role because it sounds close wastes a spawn.

## Verification

After a delegation, confirm all three before reporting done:

1. Every artifact path in DELIVERABLE exists — `search_files(target='files')` or
   `terminal(command='ls -la <path>')`.
2. The content is real work, not a stub — `read_file` the output.
3. Any claim about a command's result is backed by output you ran yourself.
