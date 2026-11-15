---
name: hermes-cron
description: "Use when managing or debugging Hermes cron jobs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, cron, scheduled-jobs, operations, telegram]
    related_skills: [hermes-custom-provider]
---

# Hermes Scheduled Jobs

## When to Use

Use this skill when:
- Creating, editing, pausing, resuming, or removing a Hermes scheduled job
- Debugging a job that runs but delivers nothing (silent failure)
- Migrating a script to a different Python interpreter (e.g. to gain third-party deps)
- Adding a new cron job that must deliver to Telegram or another channel

Do NOT use this skill for n8n workflows — those are a different runtime with their own skill (`n8n-workflows`).

Hermes cron runs scripts on a schedule and delivers stdout to a target (Telegram by default). This skill covers the operational workflow — creating jobs, editing them, fixing silent failures, and the Python interpreter trap that catches many production jobs.

## Job Anatomy

`hermes cron list` shows each job with:

- **Script** — file under `~/.hermes/scripts/` (real path, not symlink)
- **Interpreter** — Python executable used to run the script (controls which site-packages are visible)
- **Mode** — `no-agent` means script stdout becomes the delivery message (empty stdout = silent)
- **Delivery** — `telegram:<chat_id>:<topic>` for the work chat, `local` for log-only
- **Schedule** — `every 30m`, `0 9 * * *`, etc.

Job records live in SQLite; `hermes cron list` reads them.

## Workflow: Change a Production Cron Job

1. **Backup first**:
   ```bash
   hermes cron list > /tmp/cron-pre-edit.txt
   ```
2. **Identify the failure** (if fixing):
   ```bash
   hermes cron runs <job_id>      # last ~20 runs with stderr
   ```
   Look for `failed` runs and read the stderr — this is the diagnostic gold for silent failures. "N failures in a row" with no chat reply is the classic symptom.
3. **Dry-run the new pipeline by hand** with the exact Python the cron will use:
   ```bash
   /path/to/interpreter /path/to/script --once
   ```
   Do NOT trust `hermes chat` for this — it runs under Hermes' own Python. Match the cron interpreter exactly.
4. **Make the change**:
   ```bash
   hermes cron edit <job_id> --script <name> --interpreter <path>
   ```
   The schedule is a POSITIONAL argument to `create`, not a `--schedule` flag,
   and there is no `--description` — the human label is `--name`:
   ```bash
   hermes cron create "0 9 * * *" --name "my-agent" --script wrapper.py \
     --no-agent --deliver "telegram:<chat_id>:<topic>"
   ```
   Passing `--schedule` or `--description` is rejected as unrecognized
   arguments before the job is written.
   **Re-targeting an existing job is a one-flag edit** — `hermes cron edit <id>
   --deliver "telegram:<chat_id>:<topic>"` — no need to delete and recreate,
   and the run history is preserved. Change the wrapper's hardcoded topic in the
   same pass, or a manual run will keep posting to the old thread.
5. **Verify**: wait one tick or trigger with `hermes cron tick`. Watch the chat for the delivery. Then `hermes cron runs <job_id>` should show `completed` with no error.

## Pitfalls

1. **`--script` is a bare path — it takes no arguments.** The value is treated
 as the filename in full, so `--script "agent.py --days 7 --telegram"` fails with
 `Script file not found: /root/.hermes/scripts/agent.py --days 7 --telegram`.
 Put the flags inside a wrapper under `~/.hermes/scripts/` and pass the plain
 filename to cron. The wrapper then also holds the interpreter choice, so the
 schedule and a manual run execute the identical command.

 **`--script` also rejects symlinks**. `hermes cron edit --script X` validates that X's realpath stays under `~/.hermes/scripts/`. A symlink to `/root/<some-agent>/script.py` fails with "Script path escapes the scripts directory via traversal". Fix: write a thin wrapper in `~/.hermes/scripts/` that re-execs the real script under `sys.executable`.

 ```python
 #!/usr/bin/env python3
 import subprocess, sys
 # forward argv: without it a --dry-run flag is ignored and the wrapper runs the
 # full pipeline, spending real money on a "free" test
 rc = subprocess.call([sys.executable, "/root/real-agent/agent.py", "--once"] + sys.argv[1:])
 sys.exit(rc)   # forward the child's exit code — see pitfall 8
 ```

 **The wrapper must do both of these.** Forwarding only `sys.executable` and
 hardcoding the flags is the trap: the scheduler invokes the wrapper with no
 arguments, so every manual `--dry-run` test silently becomes a production run.
 Forward only the path and ignore the exit code, and a crash 30 seconds in is
 reported as `ok` with an empty delivery. Test both directions before trusting
 the schedule: run it by hand with `--dry-run` (must stop early) and force a
 failure (must exit non-zero).

2. **`--interpreter` must have all script's imports**. The Python in `--interpreter` is the one that actually runs the script. If the script does `from playwright.sync_api import sync_playwright` and the interpreter is Hermes' tools Python (no third-party deps), every tick fails with `ModuleNotFoundError`. To find a Python with the deps, probe `~/.hermes/installs/*/environments/*/venv/bin/python3.14` with `python -c "import X"` and pick the one that imports cleanly.

3. **`hermes cron list` may show a masked Python path** with literal asterisks in the directory name (e.g. `python-3.14.7+202****0901-linux-x64`). The stars are real characters in the directory name, not a glob. To resolve: `ls -d /root/.hermes/tools/python-3.14.7+2*`. Don't copy-paste the literal masked path into a script — the asterisks are part of the name.

4. **`no-agent` mode = stdout IS the message**. With `--no-agent`, the script's stdout becomes the Telegram message. Empty stdout → silent run that looks like a failure. If `hermes cron list` shows `Last run: ok` but no chat message arrived, the script printed nothing.

5. **`hermes cron run <id>` is NOT immediate**. It marks the job to run on the next scheduler tick. To fire it now, run `hermes cron tick` after. For instant manual runs while debugging, just run the script directly with the same interpreter — see Workflow step 3.

6. **Backup before edit**. `hermes cron edit` is a SQLite write with no atomic undo. Before any production change, dump `hermes cron list > /tmp/cron-pre.txt`. If the edit goes wrong, the previous state is preserved for manual rollback — no `hermes cron revert` exists.

7. **`hermes cron runs <id>` is the diagnostic command for silent failures**. Shows recent runs with `failed` / `completed` / `unknown` status and the stderr for each. If `hermes cron list` shows only the most recent `Last run:` line, scroll back through `hermes cron runs` output — past failures are still there even after recovery.

8. **`completed` is the SCHEDULER's status, not the job's.** It means the job was
   handed off and the process exited — it does not mean the work happened. A run that
   crashes 30 seconds in is still `completed` with `delivery_outcome: delivered`, and the
   delivery carries the script's own traceback. Confirm by reading the per-run output
   file under `cron/output/<job_id>/` and by querying the artifact store for the row the
   run should have created. A `completed` execution with no new row is a crashed run
   reported as healthy.

9. **`hermes cron runs <id>` truncates long stderr.** It surfaces the recent history,
   but a full traceback or a long pipeline log is not all in that view — open the
   `cron/output/<job_id>/<timestamp>.md` file for the whole thing. That file is also the
   only place the stdout that was delivered to Telegram is preserved, so it is the
   record of what the user actually saw.
