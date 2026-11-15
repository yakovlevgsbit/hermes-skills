---
name: telegram-bot-runtime-debugging
description: "Use when a live Telegram bot misbehaves or crashes."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [telegram, bot, python-telegram-bot, debug, handlers, live-service, systemd]
    related_skills: [telegram-bot-payments, telegram-llm-agent-bot, deploy-agents, qa-agent]
---

# Telegram Bot Runtime Debugging

Fix a live Telegram bot that misbehaves, without breaking the paths that
work. The class is not "write bot code" — it is: a running bot on a production
host shows the wrong behaviour, one bug is often several bugs wearing one
symptom, and the bot bills real users' credits while you work.

## When to Use

- The user pastes a transcript showing a wrong reply, a crash message, or a
  feature that silently does nothing.
- A bot handler does not fire for an obvious input.
- A fix touches a path that spends money (stars, credits, paid API calls) and
  needs verifying without burning the user's balance.

## The triage order (do not skip step 1)

**1. Read the bot's own log before reading any code.** The traceback names the
file and line; the log also shows the sequence of updates, which tells you
which handler ran and which did not.

```bash
journalctl -u <unit> --since "-30 minutes" --no-pager | grep -iE "error|traceback|exception" -A 20
tail -60 /root/<bot>/logs/bot.log        # if the bot writes its own file
```

**2. Identify the unit and the interpreter.** `systemctl list-units --type=service
| grep <name>`, then `systemctl cat <unit>` — the unit tells you the exact
`ExecStart` interpreter and whether the env comes from a file. Restarting with
the wrong interpreter is a classic self-inflicted outage: `python3` in PATH may
be a different Python than the one the bot was installed under.

**3. Find the handler that owns the symptom** by grepping for the message text
the user saw (`grep -rn "<the reply string>" handlers/`). The user's visible
output is usually a literal in the source.

**4. Then, and only then, read the handler.** Reading code first produces
theories about code you have not confirmed ran.

## python-telegram-bot: the traps that cause most of these bugs

### `.text` vs `.caption` — one bug, two symptoms

Telegram puts the text of a photo/video/file/document in
`update.message.caption`; for those messages `update.message.text` is `None`.
Code that reads only `.text` breaks two ways at once:

- `AttributeError: 'NoneType' object has no attribute 'text'` wherever the
  code touches `.text` on a message that carries media;
- **silently** — any validation reading the field gets `""`, so a valid email
  is rejected as «не похоже на email», and a prompt is rejected as empty.

Read both, through ONE helper that every handler calls:

```python
def message_text(update) -> str:
    msg = getattr(update, "message", None)
    if msg is None:
        return ""
    text = getattr(msg, "text", None)
    if text:
        return text.strip()
    caption = getattr(msg, "caption", None)
    return caption.strip() if caption else ""
```

Put the helper in the module that owns the shared handlers and import it
everywhere. The same defect otherwise has to be fixed separately in the text
handler, in a capture flow (email/code), and in any command that parses
free-form input — three sites, three chances to miss one.

### `filters.TEXT` also matches captions

`filters.TEXT` passes any message carrying text, including a photo with a
caption. So `MessageHandler(filters.TEXT & ~filters.COMMAND)` swallows
media-with-caption before the `filters.PHOTO` handler sees it, and the media
pipeline never runs.

Exclude captions explicitly:

```python
filters.TEXT & ~filters.COMMAND & ~filters.CAPTION
```

**The casing is load-bearing.** The filter instance is `filters.CAPTION`
(upper case); `filters.Caption` is the CLASS, and `~` on a class raises
`TypeError: bad operand type for unary ~: 'type'` at import time — the bot
fails to start, and the traceback points at your filter line rather than at
the real mistake. Verify the expression in a REPL before restarting a live
service:

```bash
python -c "from telegram.ext import filters; print(filters.TEXT & ~filters.COMMAND & ~filters.CAPTION)"
```

### Fixing a paid bot: confirm before charging

When the bot spends the user's money (stars, credits, paid API calls), the
DEBATE is the deliverable, not the call. The failure mode is a bot that
charges 60⭐ for a generation the user never asked for, or charges for a
misfire. Three rules, in order of how often they bite:

**1. Separate the intent question from the execution.** When an input is
ambiguous (a photo could mean «edit this» OR «use this as a video frame»),
ask which — do not pick one and charge. Two inline buttons cost nothing;
a wrong 60⭐ charge costs a refund, a support message and trust.

**2. Never charge on the FIRST interpretation of an ambiguous input.** Show
what you understood (the prompt, the price, what will be spent), then wait
for an explicit confirm. The state machine is:

```
photo arrives → save it → ASK intent → (user picks) → SHOW prompt + price
              → ASK confirm → (user confirms) → CHARGE → generate
```

Each step stores its own flag in `context.user_data` and each step is
reachable from a button. The charge happens at exactly one place.

**3. Validate that the free-text input IS an instruction before charging.**
A photo caption of «привет», «тест», «+» or «ok» is not a prompt. Charge
60⭐ for «привет» and the user will rightly complain. Reject short, empty
and stop-word-only inputs and ask for a real instruction instead. A cheap
heuristic (stop-word set + minimum word count + minimum length) is enough.

**The generalizable rule: the moment a flow can spend money, the charge
must be the last thing that happens, and it must be reachable only from an
explicit user action.** A handler that reaches `spend_stars()` on the
arrival path has no confirmation step, no matter how careful its prompt
handling is.

## A flow that asks for input has ONE owner for that flag

A flow that says «now write the instruction» sets a flag
(`awaiting_edit_prompt`, `awaiting_email`) and then waits. The handler that
sets the flag is NOT the one that consumes it — the message router is.
If the router does not check that flag, the input the user carefully typed
is silently dropped into a generic fallback («this looks like a prompt, what
should I generate?») and the flow appears broken with no error anywhere.

**Every waiting flag must be read in the shared text handler, before the
generic free-text fallback.** The flag check belongs in the router, near
the top, so it wins over reply-keyboard matching and over the
«looks like a prompt» heuristic.

```python
# in the shared text handler, BEFORE the generic fallback
if context.user_data.get("awaiting_edit_prompt"):
    path = context.user_data.get("edit_image_path")
    ...
    await img.ask_confirm_from_text(update.message, context, text, path)
    return
```

**Check for orphaned flags when auditing a flow:** grep for every
`user_data["awaiting_*"] = True` and confirm each one is READ somewhere.
A flag written but never read is a silent input sink.

## A callback is not a message: `update.message` is None there

A generation path that replies via `update.message` works when it is
entered from a command, and breaks when the same path is entered from an
inline button — because in a `CallbackQueryHandler` the update carries
`callback_query`, and `update.message` is `None` (the message lives at
`update.callback_query.message`). The failure is an `AttributeError` on
`None`, usually AFTER the money was already spent.

**Pass the reply target explicitly.** Give the generation function a
`target=None` parameter and resolve it in this order:

```python
async def _generate_edit(update, context, prompt, image_path, target=None):
    if target is None:
        target = update.message
    if target is None:
        return          # nothing to reply to — do not charge
    ...charge here, after the target check...
    await target.reply_text(...)
```

From a callback, pass `query.message` as the target. **Resolve the target
BEFORE charging** — an unresolvable target means there is nowhere to show
the result, so the charge must not happen.

## One update, one handler — registration order decides the winner

PTB runs ONE handler per update: the first registered handler whose filter
matches takes it, and nothing else in that group is called. Consequences:

- A broad text handler registered before the media handler eats every photo.
- The same applies to callbacks: a `CallbackQueryHandler` without a pattern
  swallows callbacks that a later pattern-matched handler should have got.
  Register one general handler and dispatch on `callback_data` inside it.

### `Update` and `Message` are immutable

`update.message = stub` raises `AttributeError: ... can't be set!`. You cannot
patch the object to intercept replies in a test. Instead subclass `Message` and
override `reply_text`, or capture at the boundary you own.

## Verify the fix without Telegram and without spending the user's money

Build a loop that is red on the user's exact symptom and green after the fix.
Two layers, both needed:

**1. Filter and routing assertions, on real PTB objects.** Build genuine
`Update`/`Message`/`Chat`/`User`/`PhotoSize` instances (not dicts) — a
hand-rolled fake omits attributes the SDK dereferences, and the failure looks
like a filter bug. Assert which handler each input reaches:

```python
from telegram import Update, Message, Chat, User, PhotoSize
from telegram.ext import filters

f_text = filters.TEXT & ~filters.COMMAND & ~filters.CAPTION
cases = [
    ("обычный текст", Message(message_id=1, date=now, chat=chat, from_user=user,
                              text="yakovlevgs@yandex.ru", entities=[]), f_text),
    ("фото с подписью", Message(message_id=2, date=now, chat=chat, from_user=user,
                                caption="yakovlevgs@yandex.ru", photo=[photo], entities=[]), None),
]
for name, msg, expect in cases:
    got = f_text.check_update(Update(update_id=1, message=msg))
    assert got is (expect is not None), name
```

Cover at least: plain text, text with a command entity, media with a caption,
media without a caption, and an empty message. Assert the ROUTING (which
handler wins), not just "it does not crash" — routing is where the order bug
lives.

**2. The handler itself, with a stubbed context.** Call the handler directly
with a fake `context` carrying `user_data` / `bot_data`, and a `Message`
subclass that records replies. Assert the OUTCOME the user cares about: the
valid email is accepted (no «не похоже» reply), the junk email is still
rejected, and no exception escapes.

**Never spend the user's real credits to test a message-parsing fix.** The
credits path is a different code path; the bug you are fixing is upstream of
it. If the fix genuinely requires a paid call, say so and ask before making
it — and if a paid call IS needed, spend the minimum (one image, not a
series) and refund immediately on failure the way the bot already does.

## Restarting a live bot safely

```bash
cp handlers/<file>.py /root/<bot>-backups/<date>/     # before editing
systemctl restart <unit>
sleep 8
systemctl is-active <unit>                            # must print: active
journalctl -u <unit> --since "-30 seconds" --no-pager | grep -iE "error|traceback"   # must be empty
```

Confirm the new PID actually replaced the old one and that `NRestarts` did
not increment — `Restart=always` means a crash-loop looks like a healthy
service until you check the log.

Never restart a service as the first diagnostic step of a debugging session:
it destroys the traceback in the log you were about to read.

## Backup before editing, and say where it went

The project may not be a git repo (`git -C <project> rev-parse` says so) —
then a timestamped copy directory IS the rollback path. Name it in the report.

## Pitfalls

- **A wrong reply is not a wrong handler.** Before assuming the handler is
  broken, check WHICH handler ran: in the log, a message from the user appears
  right before the bot's reply. A reply that comes from an unexpected place is
  a registration-order problem, not a logic problem.
- **A flow that asks for input may be reading a flag nobody reads.** «The
  bot ignores my instruction» is usually a flag the router does not check,
  not broken prompt parsing. Grep every `awaiting_*` write and confirm each
  has a read.
- **The charge must be last.** If `spend_stars()` runs on the arrival path
  of a flow, there is no confirmation step, whatever the code says.
- **Verify a paid fix without spending.** Stub the balance DB and assert
  the spend count is zero on every pre-confirmation path — a test that only
  checks the reply text will pass while the money still moves.
- **Two bugs, one symptom.** A crash in the text handler AND a validation that
  reads the same missing field are one root cause with two expressions. Fix the
  helper, not each symptom; otherwise the next surface (promo code, another
  capture flow) shows the third symptom.
- **The traceback line is not always the bug's origin.** The exception may
  surface in a shared handler while the cause is upstream in how the message
  was built.
- **Do not "fix" a validation that was never the problem.** If the field was
  empty because the text lived elsewhere, tightening the validator hides the
  real defect behind a clearer error message.
- **A bot can be alive and still broken.** `systemctl is-active` proves the
  process runs, not that the handler works. The routing assertions are what
  prove the handler.
- **Check whether the fix you are making was already made.** Grep the source
  for the fix pattern before editing — a second copy of the same bug in a
  sibling handler is the common remainder after the first fix.

## Verification

- [ ] Bot's own log read before any code was changed.
- [ ] Unit and interpreter identified from the systemd unit.
- [ ] Routing assertions pass on real PTB objects: text → text handler,
      media+caption → media handler, media alone → media handler.
- [ ] Handler-level assertions pass: valid input accepted, junk rejected, no
      exception escapes.
- [ ] Backup taken and its path reported.
- [ ] After restart: `is-active` = active, new PID, zero errors in the log.
- [ ] No real credits spent to verify a parsing fix.
- [ ] If the flow spends money: every pre-confirmation path asserts a zero
      spend count, and the confirmation shows the prompt and the price.
- [ ] Every `awaiting_*` flag written is read by the router before the
      generic fallback.
- [ ] Reply target resolved (and checked non-None) BEFORE the charge.
