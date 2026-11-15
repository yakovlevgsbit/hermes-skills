# Telegram JSON exports

## Acquire only what the review needs

For an offline history review, prefer a selected Telegram Desktop export over creating a full-control account session. First check the data already available; a connected bot's stored messages and a personal account's historical export are different sources.

For user instructions, keep the path short:

- Whole-account selection: **Telegram Desktop → Настройки → Продвинутые настройки → Экспорт данных из Telegram**.
- One conversation: open it → **⋮ → Экспорт истории чата**.
- Select **machine-readable JSON**, not HTML. For a text-only review, omit media and unrelated account categories. The main file is `result.json`.
- Explain that excluding media excludes its contents from analysis. Ask for specific relevant audio or images later rather than indiscriminately expanding the whole archive.
- A fresh desktop login may require approval from another device or a waiting period. Follow the client's prompt; this does not mean the export is broken.

Authoritative format and acquisition references:
- https://core.telegram.org/import-export
- https://bugs.telegram.org/c/60

Verify current UI wording if the user's client differs; do not turn an old menu description into a claim that the feature is unavailable.

## 1. Detect the container before counting

A full export commonly holds `chats.list` and a separate `left_chats.list`; a single-chat export places `messages` directly at the root. Some optional account sections may be omitted. Detect the actual shape instead of assuming the file is a flat message array.

Use local stdlib JSON parsing; a multi-megabyte file can be cheap to parse even when its estimated model-token size is enormous. Print an allowlisted summary, not the entire object.

Capture:
- source byte size and a source hash;
- root field names;
- section counts and chat types;
- ordinary/service entry counts;
- number of empty chat records;
- date ranges by source type;
- media references and missing-content markers;
- repeated IDs and whether their payloads agree.

Keep `left_chats` separate in the user-facing inventory. It can contain many old, empty records and must not inflate the apparent current circle of contacts.

## 2. Flatten rich text without losing words

The same message's `text` may be a string or an array mixing strings with entity objects. The following extraction pattern preserves the text while avoiding a dump of unrelated fields:

```python
def flatten(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(flatten(part) for part in value)
    if isinstance(value, dict):
        return flatten(value.get("text"))
    raise TypeError(f"Unexpected text representation: {type(value).__name__}")
```

Use this in a task-local script created with `write_file`, then run that script through `terminal`. Keep nontrivial parsing in a reviewable file instead of repeatedly composing long inline interpreter commands.

Retain message ID, date, `date_unixtime`, `from_id`, media markers, `reply_to_message_id` and forwarding indicators alongside extracted text. Keep the original untouched so omissions can be adjudicated against source.

## 3. Deduplicate actual duplicate records

Message IDs are conversation-scoped. Do not globally deduplicate by message ID, text, sender name or redacted phone-like values.

Within one confirmed chat, use the complete record for the equality test:

```python
from collections import Counter

def deduplicate(messages):
    seen = {}
    retained = []
    removed = Counter()
    for message in messages:
        message_id = message["id"]
        if message_id in seen:
            if seen[message_id] != message:
                raise ValueError("Conflicting records share a message ID")
            removed[message.get("type", "unknown")] += 1
        else:
            seen[message_id] = message
            retained.append(message)
    return retained, removed
```

Apply this to service records as well as ordinary messages. Exact repeats can occur in departed-chat history; they are not necessarily repeated user actions.

For cross-section or cross-file merges, first establish canonical peer identity and preserve source provenance. Public/private labels and display names can change, while numeric identifiers belong to different peer namespaces. Do not silently merge merely because a number or title matches.

Reconcile each entry class:

```text
raw entries = retained entries + removed identical copies
retained ordinary messages = sum(per-chat ordinary message counts)
```

A conflicting duplicate is an explicit data-quality issue, not permission to discard one arbitrarily.

## 4. Attribute senders and time correctly

If `personal_information.user_id` is included, use its machine ID to identify the owner, typically against `from_id == "user" + str(owner_id)`. If it was omitted, establish identity from reliable user-provided context or leave direction unresolved; never guess from a familiar display name.

Keep at least these sender classes:

```text
owner user ID
other user ID
channel/anonymous sender ID
unknown sender
```

In groups, a `channel…` author may represent posting as a channel rather than another person. The test `from_id != owner` is insufficient to label every record as an incoming human message.

Convert epoch timestamps with an explicit timezone:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

shown = datetime.fromtimestamp(int(message["date_unixtime"]), ZoneInfo(report_timezone))
```

Compare the export's displayed `date` with its epoch representation before assuming the timezone. Consider daylight-saving changes when a source spans years. Preserve the original date for evidence and label the chosen report timezone.

Anchor retrospective windows explicitly to a declared snapshot or reporting time. Do not call the newest message the creation time of the export, or use an old conversation's last message as proof of its current real-world state.

## 5. Measure missing content instead of interpreting it

Telegram may retain a `file` or `photo` field whose value explains that the attachment was not exported. Recognize that marker as unavailable content, not a path to download or evidence of a successful media read.

Report text-bearing messages separately from attachment-only records. A conversation with many voice messages may be semantically sparse even when its entry count is high.

Check group coverage before inferring interaction patterns: an export can show only the owner's messages or channel-authored posts. The missing replies prevent conclusions about response rates and whether requests were ignored.

For channels, distinguish a subscription record from exported posts. A channel title can support inventory categorization, not readership, attention, beliefs or endorsement.

## 6. Preserve business notifications without exposing leads

Do not discard every bot conversation as noise. Separate:
- operational notifications such as form submissions and order events;
- the user's commands and tests of their own tools;
- assistant-generated responses;
- promotional broadcasts.

For Tilda form notifications, inspect the source message locally and recognize localized labels:

```python
transaction_pattern = r"(?m)^(?:Transaction ID|Код заявки):\s*(\S+)"
form_pattern = r"(?m)^(?:Form Name|Форма):\s*(.+)"
```

1. Extract the complete transaction identifier before display redaction.
2. Reconcile recognized notifications with total candidate messages; keep unrecognized formats visible rather than silently skipping them.
3. Count distinct transaction identifiers, then aggregate form labels, source domains, page paths and calendar periods in code.
4. Inspect expected URL fields; if a notification contains multiple URLs, identify the form source rather than counting every link as a different submission.
5. Keep query strings, phone numbers, names and email addresses out of aggregate reports unless specifically needed for an authorized follow-up.
6. Label the result **form submissions**. Distinct transaction IDs do not prove distinct customers, completed appointments, payments or unhandled requests.

Do not infer lost leads from a one-way notification feed. A useful proposed action is to reconcile its IDs with the client's actual processing system; performing that external reconciliation is a separate authorized task.

## 7. Validate the review, not only the parser

Before quoting measurements, exercise a small fixture covering mixed text entities, identical/conflicting duplicates, missing media, multiple sender namespaces and timestamp conversion. Re-run deterministic extraction and compare results; verify aggregate counts by an independent traversal of the original.

For semantic findings, retain:

```json
{
  "chat_key": "stable-source-key",
  "message_id": 123,
  "quote": "short exact excerpt",
  "finding": "evidence-based observation",
  "status": "needs_status_check",
  "later_context_checked": true
}
```

The example is an output shape, not observed conversation data. Validate actual IDs and quotes against the selected corpus and original, and manually examine later context for the recommendations that matter.

Keep completed and cancelled examples during review; they test whether a follow-up detector merely flags every historical request. Do not invent a deadline, diagnose a relationship, or claim a semantic review is complete merely because structural totals reconcile.
