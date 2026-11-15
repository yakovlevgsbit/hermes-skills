---
name: telegram-llm-agent-bot
description: "Use when building a Telegram LLM intake bot."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [telegram, bot, aiogram, llm, agent, intake, order-collection, json-output]
    related_skills: [prompt-engineering, telegram-bot-payments, bot-knowledge-base-quality]
---

# Telegram LLM-Agent Bot (structured intake)

Build a Telegram bot whose core is an LLM agent: it holds a free-form dialog with
a client, consults a knowledge base, extracts a fixed set of fields, accepts
files, and hands a structured card to a human. Load when an order is «бот с
ИИ-агентом», «собирает ТЗ в диалоге», «квалифицирует лидов», or any intake bot
that must fill fields from conversation rather than from a form.

## When to Use

- A bot must collect order/lead parameters in natural dialog, not an anketa.
- A bot must answer from a knowledge base and never invent prices or specs.
- Files (layouts, specs, scans) arrive in chat and must reach a manager.
- The dialog result must land as a card in a manager chat and/or a sheet.

Don't use for: payments (see `telegram-bot-payments`), or pure prompt design
without a bot (see `prompt-engineering`). For a bot that answers the owner's **own**
private chats on his behalf (Telegram Business, Secretary Mode), see
`references/business-secretary-mode.md` — different rights model, no cold-first
sending, connection id on every send.

## Always-on rules

1. **Fields, not a questionnaire.** The model asks one or two questions at a
time, driven by what the client already said. A numbered list of questions in
the first message kills the dialog and the client answers half.
2. **The model never states a final price** unless the order says it should.
   Encode that as a hard rule in the system prompt AND verify it in a test —
   «менеджер рассчитает» must survive a direct «сколько стоит?».
3. **Never overwrite a collected field with an empty value.** Merge only
   non-empty values back into state, or the model «forgets» what was already
   established on the next turn.
4. **Keep the knowledge base and the system prompt as separate files.** The
   client must be able to edit materials, terms and rules without a developer;
   the bot reads them at startup.
5. **Hand files to the manager by forwarding, never by downloading** — see the
   20 MB rule below.
6. **Verify the dialog core without Telegram before wiring the bot.** A script
   that runs the LLM turn against a canned dialog is the only cheap way to see
   field extraction and price-leak behaviour.

## Stack

Python 3.11+ with `aiogram` 3 (long polling), `openai` (any OpenAI-compatible
endpoint — OpenRouter works), SQLite for dialog state. No framework beyond that.

## The JSON contract

Ask the model for one JSON object per turn: `reply` (what the client sees),
`fields` (all target fields), `ready` (all fields filled). Rules that make it
hold:

- Pass `response_format={"type": "json_object"}` on every call — a prompt-level
  «return only JSON» is ignored by cheap models. Measured on gpt-4o-mini: every
  turn came back as fluent prose with the contract silently ignored, so parsed
  fields stayed empty and the logic looked broken when the prompt was at fault.
  This is the highest-value line in the skill: the failure is silent and
  masquerades as a parser bug.
- Keep a strict retry that resends a one-line «answer ONLY with this JSON shape»
  turn when the reply is not parseable, and log when it fires.
- Strip ```json fences and fall back to the first `{...}` block before parsing.
- Put the already-collected fields into the prompt each turn, so the model knows
  what is left to ask.

## File handling — the 20 MB rule

**The Bot API will not let your bot download a file larger than 20 MB** via
`getFile`; sending and `file_id` reuse are capped at 50 MB. Layout sources (CDR,
DXF, TIFF) routinely exceed 20 MB, so «download then re-upload» fails on exactly
the files the order cares about.

- To get a file to the manager: **`bot.forward_message(manager_chat,
  from_chat_id, message_id)`**. Forwarding preserves the original with no
  re-compression and no practical size limit — the bytes never route through
  your server.
- To *store* originals on your own disk (for the archive): that needs a
  self-hosted local Bot API server, which raises the download cap to ~2 GB and
  returns a local file path. Treat it as a separate deliverable and say so.
- A `file_id` is permanent and free to resend; a `getFile` download URL expires
  in about an hour.

## Dialog memory

One SQLite row per user: `user_id, username, history (JSON), fields (JSON),
files (JSON), done, timestamps`. Keep the last ~12 messages in the context
window, not the whole history. The `files` list holds `{name, type, message_id}`
so the manager card can name them and forwarding can reuse `message_id`.

## Manager handoff

Build one card string from the fields and send it to the manager chat(s); in dev
with no manager configured, print it to the log so the flow stays testable.
Forward each stored file after the card. If the order also wants Google Sheets,
append the same fields as a row (see `google-sheets-writes`).

**In demo mode with no manager chat, send the card to the client instead** — the
card is the bot's headline feature, and a demo that swallows it into a log shows
the client nothing. Wrap it in `<pre>` (HTML-escape the content first: the card
carries client-typed text, and a stray `<` breaks the message) with one line
noting that in production it goes to the manager chat and the sheet.

## Deploy the demo live (when the demo IS the bid)

A running bot with a real link beats any description, so when the deadline allows,
deploy before submitting rather than only offering to. Run it under a systemd
unit, not a bare background process — the client will test over several days and
a reboot must not kill it.

- Unit file in the project dir, `Type=simple`, `Restart=always`, `RestartSec=5`,
  `ExecStart` pointing at a small `run.sh` that sources the secret env files and
  `exec`s the interpreter that actually has the packages. `systemctl enable --now`
  for autostart; read logs with `journalctl -u <unit>`.
- Set the bot's public face over the API before sending the link: `setMyName`,
  `setMyDescription`, `setMyShortDescription`, `setMyCommands`. A demo named
  «test» reads as unfinished.
- Keep the token in the secrets dir (`600`), never in the project or the chat.
  A token pasted into chat is already exposed — for the real build, issue a fresh
  bot and say so.
- Verify liveness from the API side: `getWebhookInfo` shows
  `pending_update_count: 0` once the poller is consuming, and `getMe` confirms the
  username you are about to publish.

## Test without Telegram

Write `test_dialog.py` that imports the bot module, sets a dummy bot-token env
var, and runs a canned client dialog through the LLM turn function, printing each
reply, the filled-field count, and the final card. Assert two things: all fields
fill by the end, and no reply matches a price pattern. This catches the two
defects that matter (prompt ignored, price leaked) in seconds and without a live
bot.

Also write `test_handlers.py` with a **stub bot** — a class recording
`send_message` / `forward_message` calls — and call the handoff function directly
with a completed state. This exercises the send path (card built, files counted,
message actually emitted) with no live user account, which the dialog test alone
does not reach. Assert the stub recorded at least one message.

## Pitfalls

- **Prompt-only JSON fails silently** — the reply looks perfect and the fields
  are empty. The symptom masquerades as a parser bug; see above.
- **Empty-overwrite loses fields.** Merge non-empty values only.
- **Cheap models are enough and cost cents.** gpt-4o-mini handles intake well;
  estimate roughly 0,3–0,5 ₽ per dialog and give the client the monthly figure.
- **`forward_message` needs the message id, not the file** — store it when the
  file arrives, or you cannot forward it later.
- **Do not let the model invent specs or prices.** Anything factual comes from
  the knowledge base; the prompt must forbid invention and say what to do when
  the base is silent.

## Verification

- Run the no-Telegram dialog test: all fields fill, no price leak.
- Run the stub-bot handler test: the card is emitted, files are counted.
- Send a real file over 20 MB through the live bot and confirm the manager
  receives the original, not a re-encoded copy.
- Confirm the KB and prompt files are edited by changing one line and restarting
  — no code change required.
- With the bot deployed: `systemctl is-active` is `active`, `is-enabled` is
  `enabled`, and `getWebhookInfo` reports `pending_update_count: 0`.

## References

- `references/business-secretary-mode.md` — Telegram Business bot (Secretary Mode):
  enabling via @BotFather + client, the rights/limits table (`can_reply`, 24 h window,
  no first message, no groups), update types, the stdlib long-poll bridge with
  draft-first replies, and the traps (`business_connection` arrives once, `timeout`
  kwarg collision, skipped chats must be marked answered).
- `references/intake-bot-implementation.md` — working code for the LLM turn
  (JSON mode + strict retry + non-empty merge), file forwarding, prompt
  template slots, the multi-Python interpreter gotcha, and the systemd unit +
  Bot-API profile setup for a live demo.
