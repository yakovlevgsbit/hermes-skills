---
name: message-archive-analysis
description: "Use when analyzing message archives. Verify evidence."
version: 0.1.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [messages, archives, privacy, evidence, telegram, analysis]
    related_skills: [document-to-action-items, audit-tool-validation]
---

# Message Archive Analysis

Analyze user-supplied conversation exports for communication circles, recurring topics, business opportunities and possible unfinished commitments. Keep account inventory, message statistics and semantic conclusions separate. This is an offline review, not an account integration or permission to contact correspondents.

## When to use

- A user supplies a messenger export and wants an overall or focused analysis.
- A large conversation archive must be reduced without loading it wholesale into model context.
- Questions concern contacts, communication patterns, client requests or follow-ups evidenced by messages.

Do not use this as a live bot polling, bulk outreach or account-authentication procedure.

## Procedure

### 1. Establish the source and question

1. Use the attachment's actual local path. If a usable archive is already supplied, inspect it before requesting a different export or account access.
2. Parse locally through `terminal`; initially print only structure, record counts, date ranges and coverage limitations. Do not begin by dumping contacts or message bodies with `read_file`.
3. If the analysis objective is still genuinely unspecified, show the verified inventory and ask one focused scope question with `clarify`. Do not repeatedly ask for a goal the user already selected.
4. Distinguish selected chats, a whole-account export and records about departed chats. A structurally valid file does not establish complete history.

For Telegram acquisition, JSON shapes and notification parsing, load [references/telegram-json.md](references/telegram-json.md).

**Gate:** the input is parseable, the intended analysis is known, and missing content is identified before conclusions.

### 2. Prepare a private, traceable working corpus

- Leave the supplied source unchanged. Keep derived excerpts in a restricted task workspace, not a public deployment, shared KB, skill or global memory.
- Construct display excerpts from needed fields. Exclude contact lists, credentials and unrelated private details; an ordinary messenger export can contain bot tokens and integration secrets inside messages.
- Compute identifiers, timestamps and deduplication keys from source fields before display redaction. Masked phone-like strings can also be transaction IDs; never count the masked representation as the original identifier.
- Preserve source section, chat index/key, message ID, timestamp and direction with every excerpt. Flatten rich-text arrays without dropping their embedded text entities.
- Preserve missing-media and forwarded-message flags. A caption is not the attachment's contents, and a forwarded statement is not automatically the sender's own position.
- Treat regex redaction as best effort, not an anonymization guarantee. Review report-bound quotes separately and omit unnecessary third-party details.

**Gate:** excerpts remain resolvable to the original without exposing the raw archive to every reviewer.

### 3. Establish the accounting before measuring behavior

1. Count ordinary messages, service events, empty chat records and missing-media records separately.
2. Deduplicate within a confirmed conversation identity. Collapse repeated message IDs only when their payloads are identical; conflicting copies require investigation. Report raw, removed and retained counts.
3. Keep humans, bots, groups, channels and saved messages in separate categories. Do not turn a count of archive records into a count of people or current conversations.
4. Use sender IDs for attribution, not display names. Preserve channel/anonymous authors as a separate class; a non-owner ID in a group does not necessarily mean another human sent it.
5. Derive time from the machine timestamp, verify its relationship to displayed dates, and state the report timezone. Label recent windows relative to their actual anchor; the newest message is not necessarily the export creation time.
6. Repeat deterministic accounting and reconcile it with an independent flatten/count of the source. Keep numeric output on disk for later aggregation rather than recomputing totals in prose.

**Gate:** counts reconcile, retained records have provenance, and the report cannot confuse bot traffic or departed channels with personal activity.

### 4. Review in bounded, complete units

- Read each chosen conversation with enough later context to interpret commitments. Measure rendered excerpt size, not just raw file size or chat count, when making batches.
- Prefer preserving whole conversations. If a large conversation must be split, record message-range boundaries and inspect subsequent ranges before deciding whether a request remained open.
- Record a manifest of assigned chat keys and message counts. Persist each batch's findings with the keys actually reviewed; reconcile the union and any deliberate overlap before claiming exhaustive coverage.
- For delegated semantic work, provide only the assigned redacted corpus and an evidence contract: `chat_key`, `message_id`, short exact quote, finding, uncertainty. Keep computation and final source verification with the parent.
- Label samples as samples. Full metadata inspection plus a few bot examples is not a complete semantic review of all bot history.

**Gate:** every scoped conversation is either reviewed or explicitly excluded with a reason.

### 5. Separate findings from interpretations

**Communication circles and topics**
- Describe behavior visible in messages, not permanent personality, diagnoses or motives.
- Treat message volume as volume, not time spent, relationship closeness or current social activity.
- Treat channel names as inventory, not proof of readership, agreement or beliefs. Empty or one-sided histories cannot support conclusions about the missing side.

**Business opportunities**
- Separate genuine requests, the user's own tests, incoming promotions and general professional discussion.
- Inspect operational notification bots separately from promotional bots; forms and order notifications may carry the clearest business evidence.
- Keep unique submissions, unique people, paid orders and unresolved requests as different measures. A missing completion status in a notification stream does not prove lost revenue.

**Possible unfinished commitments**
- Read later messages for completion, cancellation, rescheduling or a move to another channel before suggesting a follow-up.
- Use `needs_status_check`, `possibly_open`, `closed_in_export` or `insufficient_data`. Leave owner and deadline unknown unless explicitly established.
- Do not turn the last visible question into a proven unanswered request. Missing audio, screenshots and offline conversations can contain the resolution.
- Preserve conditional language: an offer, tentative plan and binding commitment are not interchangeable.

**Gate:** every actionable claim has evidence and a stated current-status uncertainty where needed.

### 6. Verify and deliver

1. Check every surfaced message ID and exact quotation against the working corpus, then the original source where the quote is unredacted. A redacted display quote must not be described as verbatim original text.
2. Re-read the context of the highest-priority recommendations; syntactically valid references do not prove their interpretation.
3. Reconcile reviewed keys against the manifest and reported totals against saved accounting. Separate the completed metadata pass from any unfinished semantic pass.
4. Give Георгий a substantive Russian summary: **круг общения → основные темы → рабочие возможности → что проверить/закрыть**. Lead with conclusions, not parser implementation details.
5. For follow-ups, use a compact table: **чат · дата · основание · что проверить/сделать · уверенность**. State which items are proposals rather than known obligations.
6. Attach a private readable report when detail exceeds a useful chat reply. Keep raw contacts and secret values out of it; do not publish the archive or create external tasks merely because the analysis suggested them.

## Verification checklist

- Source unchanged; no account actions or correspondent messages sent.
- Raw entries, duplicate removals and retained totals reconcile.
- Dates, sender namespaces and unavailable media are accounted for.
- Human conversations and operational/promotional bot traffic remain distinct.
- Scoped review coverage is explicit and checked programmatically.
- Report quotations resolve to source messages; key interpretations were re-read in context.
- Candidate follow-ups are not mislabeled as proven debts, overdue tasks or lost clients.
- The report states what it did not assess and contains no unnecessary private data.
