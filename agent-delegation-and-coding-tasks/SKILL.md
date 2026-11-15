---
name: agent-delegation-and-coding-tasks
description: "Use when coordinating agents through a manager."
version: 1.1.0
author: curator
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [agent-delegation, multi-agent, manager, subagent, coding-tasks, task-management]
---

# Agent Delegation and Coding Task Management

## When to Use

Use when building a multi-agent system where a manager (you) delegates coding tasks to sub-agents, with task files, result outputs, and logs. Also use when you need to structure a project with clear separation between the manager's review and the sub-agent's execution.

This skill covers the workflow the user built for the Web-Coding Assistant: manager accepts tasks, delegates to sub-agents, sub-agents execute and write results to output/, logs to logs/, and the manager reviews and integrates.

For a multi-agent dashboard/control plane such as Paperclip, load [references/control-planes.md](references/control-planes.md). Application roles, hiring approvals, runtime permissions, accounting and completed deliverables are separate boundaries.

## Roles: Manager vs Sub-agent

You are either the **manager** or a **sub-agent**. Never do both in one turn without the user deciding.

| Role | Responsibility |
|---|---|
| **Manager** (you) | Accepts tasks, breaks them into subtasks, writes task files, delegates, reviews outputs, integrates results, reports to the user. |
| **Sub-agent** | Reads a task, executes it, writes results to output/, writes logs to logs/, reports completion. |

If the user says "you are the manager", you do NOT execute the coding tasks yourself. You delegate.

## Project Structure

```
/root/web-assistant/           # project root
├── tasks/                     # task files (task-N.md)
├── output/                    # results from sub-agents
├── logs/                      # logs from both sides
├── agents/                    # sub-agent definitions
├── scripts/                   # executable code
├── .env                       # secrets (mode 600)
├── requirements.txt
├── README.md
├── TASK.md                    # global task list
└── MANAGER.md                 # manager instructions
```

## Task File Format

Every task file follows this shape:

```markdown
# Task N: Title

**Статус:** In progress | Waiting | Done
**Срок:** Expected time

## Задача

What the sub-agent must do. Be concrete: file names, functions, expected outputs.

## Инструкции суб-агенту

1. Read TASK.md first
2. Return missing context or a blocker to the manager; do not ask the user directly
3. Execute, save to output/
4. Write log to logs/

## Сдача (Delivery)

List the files and what the user should verify.

## Критерии

Checklist for the manager to confirm completion.
```

### Rules
- **Be concrete**: name every file the sub-agent must create.
- **Define the delivery**: what output file, where, what format.
- **Define criteria**: how the manager verifies completion.
- **Do not embed secrets**: never put tokens in the task file.

### Pitfall
The task file is the contract between manager and sub-agent. If it is vague, the sub-agent will improvise and report success without doing the work. Always include a `Сдача` (delivery) section listing exact files. This is the single most common failure mode: the sub-agent reports "done" while only checking the directory structure, not creating the files the task names.

## Sub-agent Script Requirements

The sub-agent script must:

1. Parse `--task` argument (or equivalent)
2. Read the task file
3. Execute the work
4. Write results to `output/{task_id}.output`
5. Write logs to `logs/subagent.log`
6. Print a one-line summary to stdout

**Key rules for the sub-agent:**
- **Deliver working content, not only paths.** Creating a file or directory is only a step; the requested artifact and acceptance checks must actually exist and pass.
- **Return verifiable execution evidence.** Keep relevant commands, exit status, output and artifact paths. The manager inspects artifacts and logs; neither stdout nor a status label alone proves completion. Exclude secret values and unnecessary client data from logs.
- **Scope credentials explicitly.** A role prompt does not block filesystem or environment access. Use only the authorized credential mechanism for the task; do not browse, copy or print unrelated secrets, and never ask a child to dump environment values.
- **Report honestly.** If a step cannot be done, say so. Do not fabricate results to appear helpful.

## Execution Sequence

1. Write the task file (manager only)
2. Run the sub-agent: `python3 scripts/subagent.py --task /root/web-assistant/tasks/task-1.md`
3. Wait for the sub-agent to exit before reviewing
4. Verify the output files exist in `output/`
5. Check `logs/subagent.log` for step-by-step completion
6. Integrate and report to the user

## Verification Checklist

| Check | How |
|---|---|
| Output files exist | Locate the declared artifacts with `search_files` or a verified artifact handle |
| Log files exist | Locate the declared logs without assuming a default filename |
| Content is real | Read the artifact and exercise the relevant acceptance checks |
| Execution is supported | Inspect actual commands, exit codes and relevant logs |
| Secrets are protected | Scan locally; report only redacted finding type/location, never raw matched values |

## User Preference Encoding

This user's preferences for how results should look:

- **Short reports with real output.** Not claims of success, but actual tool output pasted.
- **Tables for structured data.** Markdown tables for model lists, file trees, task lists.
- **Verifiable claims.** Every statement about what was built must be backed by a file or log path.
- **Dependency-aware execution.** Verify prerequisites before dependent work; batch independent reads and use parallel agents only with non-conflicting write scopes.
- **Explicit delivery.** Always state what the user should verify at the end.

## Error Handling

- **Sub-agent exits with error**: inspect its saved artifacts and run the existing scoped checks before restarting. A failed final response does not prove its files are missing or broken; preserve complete work and reassign only the actual gaps.
- **Provider token-rate or peak request-size limit**: reduce fan-out rather than immediately adding replacement workers. Keep prompts and source reads scoped, checkpoint small batches, and resume missing units in fresh bounded contexts when capacity permits. Do not change the user's provider, billing tier, or global fallback configuration as an unapproved workaround.
- **Authentication failure (401)**: verify endpoint, credential selection, expiry and request format without exposing the value. Do not infer a wrong token from the status alone or rotate production credentials without authorization.
- **Package missing**: first confirm installation is in scope and identify the actual project environment. Use its supported isolated package workflow; do not repair Hermes's managed environment with raw pip. A research-only task does not authorize installing the candidate.
- **Permission denied**: inspect the exact file, ownership/ACL and intended access. `.gitignore` is not access control. Do not broaden permissions, change unrelated ownership or bypass the error merely to complete the task.

## When to Escalate to the User

- When the task touches production systems (live bots, live databases, live web panels)
- When the user must provide a secret (Telegram token, API key)
- When the error persists after a retry
- When the task is beyond the scope defined in the task file

Resolve ordinary problems within the authorized scope without unnecessary questions: fix your own isolated script, use approved dependencies, and recover a test process when safe. Production restarts, credential changes, wider permissions and repeated failures need a reviewed plan or an explicit decision; do not turn recovery into an uncontrolled retry loop.
