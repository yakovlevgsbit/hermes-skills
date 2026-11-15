---
name: telegram-personal-export-analysis
description: "Use when analyzing Telegram JSON exports."
version: 0.1.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [telegram, exports, privacy, analysis, evidence]
    related_skills: [document-to-action-items, audit-tool-validation, hermes-workflow]
---

# Telegram personal export analysis

Analyze an authorized offline Telegram export without connecting to the account, sending messages, or changing production. Keep observations, interpretations, proposed follow-ups and current-state uncertainty separate.

## When to use

- The user attaches Telegram Desktop `result.json` for a general, business, relationship or communication review.
- A large export must be inventoried or searched without dumping it into model context.
- Old conversations need evidence-backed action candidates.

Do not use Bot API history as a substitute for a personal export. Business bots normally see only the updates available to their connection, not the account's historical cloud archive.

## Intake

1. Ask the analysis objective when missing, but first perform a small structural inventory if the user supplied a file. Do not turn an ambiguous general request into intimate profiling.
2. For export instructions, use the official sources: https://bugs.telegram.org/c/60 and https://core.telegram.org/import-export . Desktop supports JSON through Settings → Advanced → Export Telegram Data, or an individual chat's export menu. A fresh desktop login may require approval from another device or a wait.
3. Parse the local JSON programmatically through `terminal`; use `read_file` only for bounded derived excerpts. Never inline the entire archive. Handle both a full `chats.list` export and a single Chat object with `messages`.
4. Report current-list records and `left_chats.list` separately. Count empty records, ordinary messages, service events, date coverage and missing media. A title-only channel record does not contain its publications.

## Normalize and verify

- Flatten `text` strings and mixed arrays of strings/entity dictionaries. Preserve message IDs, chat section/index, dates, direction, forwarding and unavailable-media flags alongside the text.
- Determine the owner from `personal_information.user_id` when available; do not identify authors by display-name similarity. Do not merge different peers because their names match.
- Separate the official Telegram service account from human-contact metrics even when its export type is `personal_chat`. Verify the identifier, not just the displayed name.
- Treat channel/anonymous senders as author-unknown. A non-owner `from_id` is not proof that another human wrote the message; the owner may send as a channel.
- Deduplicate exact repeated message objects within the same peer/message-ID scope. Preserve raw, removed and unique counts; fail or flag conflicting objects that share an ID. Do not globally deduplicate Telegram message IDs across different chats.
- Compare `date` against `date_unixtime` to establish the export timezone. Anchor recent-window counts to the archive snapshot and label the window. Do not silently substitute the current date.
- Test mixed text, duplicates, conflicting IDs, empty chats, direction and timestamps on a fixture. Re-run deterministic statistics and compare outputs; reconcile aggregate counts with a separate raw-source parse.

## Minimize private exposure

- Keep raw archives in their attachment location. Put temporary derived batches in the session scratch directory with restrictive permissions where supported; keep final reports in a private output location.
- Exclude authentication/service conversations from semantic excerpts unless they are explicitly needed. Redact credentials, codes, phones, emails and unnecessary private details before delegation.
- Do not call regex-redacted data fully anonymous. Passwords or login codes can be standalone, split across adjacent messages, or lack a label. Review contextual secret candidates and keep excluded message markers rather than publishing values.
- Do not copy raw archives, intimate findings or third-party personal details into memory, KB, skills or public repositories. Store only reusable method lessons in this skill.
- A general report does not need private debts, minors' details, addresses or access values. Include only what supports the user's chosen scope.

## Semantic analysis

1. Split by complete conversations, not arbitrary message windows. Save an assignment manifest, append batch findings to files, and verify union, overlap and message totals in code.
2. For delegated work, give each child the exact permitted batch, output path and privacy rules. Require a classification row for every assigned chat, including empty/unknown rows. Require factual findings to cite chat key, message ID and a short verbatim quote.
3. Distinguish work requests, family/friends, practical services, incoming advertising, outgoing prospecting and automated notices. Neither a subscribed channel nor an incoming pitch proves interest, agreement, expertise or a new customer.
4. Examine transactional bots separately. Form notifications can be business evidence: deduplicate by actual transaction identifier locally, not a redacted displayed placeholder. Count submissions, not unique people, paid orders or lost leads unless those outcomes are explicitly supported.
5. Read later context and related conversations before proposing unfinished tasks. Separate a performed action from its successful result, and different incidents affecting different systems. Explicit cancellation or restoration closes that episode; a later unrelated 'works' does not.
6. Treat missing replies as unknown, not neglect, debt or an overdue commitment. Follow-ups commonly continue by phone or another messenger; preserve explicit channel-switch evidence. Never revive old tasks automatically.
7. Record deadlines/owners only when explicit. Preserve relative or conflicting dates rather than inventing a calendar deadline. Advice, a proposed price or a sales pitch is not an accepted obligation.
8. Describe behavior observed in the sample, not diagnoses or fixed personality. Frequency is not intimacy; message volume is not reading time. A general overview should balance work and personal themes without turning every acquaintance into a lead.

## Report and verification

- Deliver a readable report with source scope, core themes, evidence-backed opportunities, a short status-check table and explicit exclusions. Attach only the minimized report, not a raw corpus by default.
- Reconcile all assigned chat keys and message totals programmatically before claiming full coverage. Verify every cited ID and quote against the original, then manually re-read context for the selected conclusions.
- Keep historical demand, current verified demand, outbound offers and recommendations distinct. Do not imply current production failure, legal violation or a debt from an incomplete old archive.
- Compare style across actual writing samples without claiming AI authorship based on style alone. Keep user-generated figures and quotations unchanged; recommendations are separate from the evidence.
- Inspect the final artifact for credentials and unnecessary personal data. Confirm that links/IDs and numeric claims match source data. State which media, channel content and live systems were not assessed.
- Obtain separate authorization before sending follow-ups, creating external tasks, changing permissions, deleting data or enabling account access. Read back exact external targets after any subsequently authorized writes.
