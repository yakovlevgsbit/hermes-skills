# Reference implementation — intake bot core

Condensed from a working demo. Python 3.11+, aiogram 3, any OpenAI-compatible
endpoint (OpenRouter used here), SQLite for state. Adapt names to the order.

## Layout

```
project/
├── bot.py               # handlers, LLM core, DB, manager card
├── knowledge_base.md    # client-editable: materials, terms, services
├── system_prompt.txt    # client-editable: role, rules, JSON contract
├── test_dialog.py       # runs the dialog without Telegram
└── dialog_state.sqlite3 # created at runtime
```

## The LLM turn

```python
FIELDS = ("product_type", "dimensions", "material", "urgency", "contacts")

async def llm_turn(state, user_text):
    messages = [{"role": "system", "content": build_prompt(state)}]
    messages += state["history"][-HISTORY_LIMIT:]      # ~12 messages, not all
    messages.append({"role": "user", "content": user_text})

    resp = await client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.4, max_tokens=700,
        response_format={"type": "json_object"},        # <-- the load-bearing line
    )
    data = parse_llm_json(resp.choices[0].message.content or "")

    if data is None:                                   # strict retry, once
        messages.append({"role": "user", "content": STRICT_JSON_NUDGE})
        resp2 = await client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.2, max_tokens=700,
            response_format={"type": "json_object"})
        data = parse_llm_json(resp2.choices[0].message.content or "")

    if data is None:                                   # never silently pass prose
        log.error("LLM never returned JSON: %s", raw[:300])
        return {"reply": raw.strip() or "Уточните, пожалуйста, ещё раз.",
                "fields": {}, "ready": False}

    merged = dict(state["fields"])                     # non-empty merge only
    for f in FIELDS:
        val = str(data.get("fields", {}).get(f, "") or "").strip()
        if val:
            merged[f] = val
    data["fields"] = merged
    data["ready"] = all(merged.get(f) for f in FIELDS)  # ready is computed, not trusted
    return data
```

`ready` is recomputed from the merged fields rather than taken from the model —
the model will otherwise report `ready: true` with fields still empty.

## Robust parse

```python
def parse_llm_json(raw: str) -> dict | None:
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict) or "reply" not in data:
        return None
    return data
```

## File handling

```python
@dp.message(F.document | F.photo)
async def on_file(message: Message):
    state = db_get(message.from_user.id)
    doc = message.document
    name = (doc.file_name if doc else "фото.jpg") or "файл"
    ftype = (doc.mime_type if doc else "photo") or "document"
    state["files"].append({"name": name, "type": ftype,
                           "message_id": message.message_id})   # id, not bytes
    db_save(...)
    await message.answer(f"📎 Принял файл: {name}. Передам менеджеру вместе с заявкой.")
```

Forwarding to the manager (no download, no size limit):

```python
await bot.send_message(manager_chat, card)
for fl in state["files"]:
    await bot.forward_message(manager_chat,
                              from_chat_id=user_id,
                              message_id=fl["message_id"])
```

## Prompt template shape

The system prompt is one `.format()`-able string with three slots:
`{company}`, `{knowledge_base}` (whole KB file inlined), `{collected_fields}`
(a bullet list of `label: value | — не выяснено`). Hard rules go in the prompt
as numbered «ЖЁСТКИЕ ПРАВИЛА», with the price rule first.

## Environment

```bash
export TELEGRAM_BOT_TOKEN="..."
export OPENROUTER_API_KEY="..."
export MANAGER_CHAT_IDS="-100..."   # empty = dev mode, card goes to log
python3 bot.py
```

## Live demo deploy (systemd + Bot API profile)

`run.sh` — sources secrets and execs the interpreter that has the packages:

```bash
#!/usr/bin/env bash
set -a
. /root/.secrets/<project>.env
. /root/.secrets/openrouter.env
set +a
PY=$(ls -d /root/.hermes/tools/python-3.14.*/bin/python3 | head -1)
cd /root/<project> || exit 1
exec "$PY" bot.py
```

Unit `/etc/systemd/system/<project>.service` (`cp` the file in — direct writes
to `/etc/systemd/system` are refused, use the terminal):

```ini
[Unit]
Description=<project>
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/<project>
ExecStart=/root/<project>/run.sh
Restart=always
RestartSec=5
StandardOutput=append:/root/<project>/bot.log
StandardError=append:/root/<project>/bot.log

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload && systemctl enable --now <project>
systemctl is-active <project>     # active
journalctl -u <project> -n 20     # startup + errors
```

Bot API profile (curl with the token; all return `{"ok":true}`):
`setMyName`, `setMyDescription`, `setMyShortDescription`, `setMyCommands`
(JSON body with a `commands` array). Liveness from the API side:
`getWebhookInfo` → `pending_update_count: 0` once the poller consumes;
`getMe` → confirms the username before you publish the link.

Stub-bot handler test (no live user account needed):

```python
class StubBot:
    def __init__(self): self.sent = []
    async def send_message(self, chat_id, text, **kw): self.sent.append((chat_id, text))
    async def forward_message(self, chat_id, from_chat_id, message_id):
        self.sent.append((chat_id, f"[forward {message_id}]"))

await B.notify_managers(StubBot(), 12345, "test_user", completed_state)
assert stub.sent
```

## Interpreter gotcha

On a box with several Pythons, `pip install aiogram` can land in a different
interpreter than the one that runs the script. If `ModuleNotFoundError: aiogram`
appears right after a successful install, find the interpreter that has it
(`ls -d /root/.hermes/tools/python-*/bin/python3`) and run the script with that
explicit path, or make a project venv (`python3 -m venv .venv`). A venv creation
that fails with «Failing command: .../bin/python3» usually means `ensurepip` is
missing — use the interpreter that already has the packages instead of fighting it.
