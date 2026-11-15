---
name: standalone-llm-agent-pattern
description: Use when building a standalone LLM agent script.
---

# Standalone LLM Agent Pattern

A reusable shape for a small, durable agent that runs outside the Hermes session: one script, task files in, outputs out, a log, and a balance/usage account. Use it for any provider the user wires up (AnyModel, OpenRouter, a self-hosted endpoint).

## When to Use

- The user says "make an agent that works through <provider>" or asks for a reusable worker over a new LLM API.
- A one-off script needs to become something that survives across sessions and can be re-run with a new task file.
- You are wiring a provider that charges per token and needs spend accounting.

## Layout

```
/root/<name>-agent/
├── scripts/<name>_agent.py   # engine: parse task, rotate models, write output, log
├── tasks/task-1.md           # one file per job (see Format)
├── output/                   # results, named <slug>_<ts>.md
└── logs/agent.log            # append-only, timestamped
```

Plus a KB page at `/root/kb/agents/<name>-agent.md` describing what it does, the model rotation, the secret path, and the pitfalls.

## Task file format

```markdown
task: Название задачи
model: ds/deepseek-v4-flash
output_format: text
system: Ты — копирайтер

Тело задачи текстом. Поля парсятся регуляркой `^([a-z_]+):\s*(.*)$`
по известному списку ключей; всё остальное — тело.
```

## Procedure

1. **Load the key, never the value into a prompt.** Read the env var, falling back to the vault files (`/root/.secrets/*.env`, `~/.hermes/.env`). Print only the fact that a key was found, never the value.
2. **Parse the task file** into a dict (task, model, output_format, system, body) and build `messages` as `[system?] + [user: body]`.
3. **Build the model list** as `requested_model` first, then the rotation chain deduped. Always include a cheap fallback so one dead model does not kill the run.
4. **Call the API per model in order.** On success, stop and return. On failure, log the error and try the next model — a 401/429 means the model is unusable for this run, not that the whole task failed.
5. **Diagnose an empty answer before falling back.** `content` empty with `finish_reason: "length"` means the model's thinking trace consumed the whole budget — retry that model with a bigger budget; do not return the `reasoning` text as the deliverable. `content: null` with `finish_reason: "stop"` and the answer sitting in `reasoning` is a provider quirk: there the fallback is correct.
6. **Write the output file and log the balance delta.** Balance before the run, balance after, report the difference as spend. Do not guess spend from the token count alone when the provider exposes a balance endpoint.
7. **Verify by running a real task**, not by reading the code. Paste the actual output and the actual spend.

## HTTP transport — a browser User-Agent is the requirement

A plain `urllib.request` POST carrying the Python default User-Agent to a WAF-fronted API returns `HTTP 403: error code: 1010` (Cloudflare) or a bare `403 Forbidden` (other WAFs). This is neither a bad key nor a wrong endpoint: it is the UA string. Two transports work — put the header on urllib, or shell out to `curl`:

```python
req = urllib.request.Request(url, data=body, method="POST", headers={
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) <agent>/1.0",
})
```

Keep the `curl` variant for providers that also filter on TLS fingerprint — shell out to `curl -s` and parse stdout:

```python
result = subprocess.run(["curl", "-s", "--max-time", "180"] + args,
                        capture_output=True, text=True, timeout=200)
data = json.loads(result.stdout)
```

Use the same transport for the balance check and for every call. One `_curl()` helper keeps the error path uniform.

## Multi-provider fallback: floors, not just rotation

A list of models inside one provider is not a chain of providers. Model each provider
as an object — base URL, key, model list, minimum token budget, timeout — and iterate
providers outer, models inner, so one exhausted provider cannot end the run.

- **Token floor per provider.** Reasoning-first models spend the budget thinking: at `max_tokens=4000` a full page comes back empty with `finish_reason: length`. Give that class of provider a floor (7000) and send `max(requested, floor)`.
- **Quality floor per answer.** A weak free model can return a 700-character "page" that passes every structural check and ships empty. Reject anything under a length threshold (`len(raw) < 2500`) and continue to the next provider; exempt explicitly tiny tasks, or the floor breaks "make me a stub".
- **Record who answered.** Set `LAST_MODEL = "provider:model"` on success. Without it "it works" hides which route paid, and you never learn how often the free tier fails silently.
- **Timeout scales with the floor.** A provider that legitimately thinks for 80–115 s needs 300 s; the 120 s that suits a fast free model aborts it mid-answer.
- **Make escalation visible in the report.** Say which provider carried the run and what the rejected attempt looked like (size, finish reason) — not only the final status.

## Delivery: cron job → Telegram topic

An agent that runs on a schedule delivers through Hermes cron in `--no-agent`
mode: **stdout IS the message**. Empty stdout is a silent run, not a failure.

1. **Wrapper in `~/.hermes/scripts/`.** `hermes cron create --script` takes a
   file path only — it does not accept arguments. `--script "foo.py --days 7"`
   fails with `Script file not found`, because the whole string is treated as
   the filename. Bake the flags into a thin wrapper that re-execs the real
   script under `sys.executable` and forwards the exit code.
2. **Give the interpreter every import the script needs.** Point
   `--interpreter` at the venv (`~/.hermes/installs/*/environments/*/venv/bin/python3.x`),
   not the tools Python — a missing third-party module is a failed run on every
   tick, and the wrapper will look like it ran.
3. **Derive the topic id from the link the user pastes.**
   `t.me/c/<internal>/<topic>` → `chat_id = -100<internal>`,
   `message_thread_id = <topic>` (the LAST number in the path). Never guess or
   reuse a remembered id: a wrong thread posts successfully and reports `OK`
   while landing somewhere else.
4. **Thread the topic through as a parameter.** The send helper must take
   `topic` as an argument and `main()` must pass `args.topic` into it. A
   `--topic` flag that is parsed but never forwarded keeps sending to the
   hardcoded default — the classic shape of "delivered, but to the wrong place".
5. **Use the bot that is actually in the chat.** `TELEGRAM_BOT_TOKEN` from
   `~/.hermes/.env` is the bot that joined the work chat. A token borrowed from
   another project's `~/.secrets/*.env` is a *different* bot: `getMe` succeeds
   and `sendMessage` returns `400 chat not found`.
6. **Verify with a real send and read the id back.** `sendMessage` returns
   `message_id`; a bot cannot see its own messages through `getUpdates`, so that
   is the only confirmation available. State the topic and id you actually
   delivered to, not just `OK`.

Telegram accepts roughly 4096 characters per message — cap the number of
sections or split, otherwise the tail disappears. Use `parse_mode: HTML` with
`<b>`/`<i>`; Markdown `#`/`##` headings render as literal text.

Aggregation, dedup and ranking depth for digest-style agents:
`references/digest-agents.md`.

## Dry-run must not spend money or change state

A generation agent's default run is a PLAN. Make the write path require its own
explicit flag (`--apply` / `--send` / `--publish`) and nothing else — do not
infer "go" from a selector flag such as `--make <name>` or `--make-all`. That
inference is how a dry-run silently produces paid output.

Test the boundary on the real flag, not by reading the condition:

```bash
agent --make <name>            # must print the plan and stop
agent --make <name> --apply    # the only thing that may generate
```

Count what actually happened — `applied`, not `attempted` — and print both a
"changed" and an "applied" number, or a dry-run reports 0 changed while having
found work. Budget is part of the plan output whenever the provider exposes a
balance endpoint: show the cost of the planned work before the user commits.

## Pitfalls

- **Slugify with ASCII before naming the output file.** A Cyrillic task name run through a `[^a-z0-9_-]+` filter becomes an empty string and produces `_<ts>.md`. Apply `.encode("ascii", "ignore").decode()` first and fall back to `"task"`.
- **Do not create placeholder task files or env files.** An empty `task.md` or a key file with no value is a trap for the next run; declare not-yet-supplied keys in the KB page instead.
- **One key per provider file, but read the vault too.** The script's own key load order matters: env var first, then the vault, then `~/.hermes/.env`. State the resolution order in the KB page so the next session does not hunt.
- **Rotation is the resilience mechanism, not an optimisation.** Put the cheapest capable model first and a universal router last; a 401 on the primary should never abort the task.
- **Balance is not raw tokens.** When the provider bills in an internal unit (e.g. AnyModel's balance tokens with per-model coefficients), the reported delta is the real spend — raw `usage.total_tokens` from the response is only a lower bound.
- **Never let the model write client-facing text.** Asked to classify or respond, it invents business facts (opening hours, prices) it has no data for. The model picks a category; the text comes from a fixed template. See `max-inbound-longpoll-support-triage`.
- **Key idempotency on a NORMALIZED form of the user-supplied string.** An agent that re-runs a task and overwrites the previous result must match the key the way the user will type it, not the way it was typed last time — `topic=eq.<value>` treats a case difference or a stray space as a different record and silently creates a duplicate. Normalize before comparing (strip, lowercase, drop separators) and keep the raw value for storage.
- **Do not heuristically repair corrupted model text.** When the model mangles a field in a way that needs semantic knowledge to fix — mixed scripts inside one word, a dropped character that changes meaning — a transliteration or character-swap "fix" produces something worse than the original, and you cannot tell from the diff whether it helped. Revert the attempt, ship the raw output, and record it as a known model defect to be fixed in the prompt. A documented defect is worth more than a plausible-looking corruption.
- **Probe a provider's catalogue before recommending a model.** Ids and prices move; a model recommended last month may be gone, and a "cheap" model's coefficient is what actually sets its cost. Re-read `/v1/models` (or the provider's own list) and say which list you checked and when. The same check applies to the ids your own fallback chain calls, not only to advice: a chain of dead ids fails silently as `no-model-response`, and nobody notices for weeks.
- **`curl` needs `--compressed` for gzip feeds.** Without it the body arrives as
  raw bytes and the parser dies on `UnicodeDecodeError: 0x8b ... invalid start
  byte`. Same flag fixes both `ET.fromstring` on RSS and `json.loads` on an API
  response that sets `Content-Encoding: gzip`.
- **Report in the user's language, not the source's.** Pasting raw English
  descriptions from an upstream API into a Russian-language digest makes the
  report unusable at a glance. Paraphrase through the LLM in the same pass —
  one short line per item, saying what it is and why it matters — and keep the
  original only as a fallback when the model call fails.
- **Cap items per source before they reach the LLM.** One high-volume feed (a
  vendor blog that publishes 1300 entries) fills the prompt on its own, and the
  model then reports only that vendor's marketing as if it were the day's news.
  Balance the batch by source and print the cap in the run log.

## Reporting

Give the user: the script path, how to write a task, the exact run command, the model rotation chain, the secret path, and the real verified output with real spend. Do not describe the agent as working without pasting a run.