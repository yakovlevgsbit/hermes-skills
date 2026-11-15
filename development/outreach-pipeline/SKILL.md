---
name: outreach-pipeline
description: "Use when building an outbound outreach pipeline."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [outreach, sales, crm, proposals, email, b2b, pipeline]
    related_skills: [org-contact-base-collection, freelance-order-response, telegram-chat-base-collection]
---

# Outbound outreach pipeline

Build the whole outbound motion for a product or service: positioning, a CRM
funnel, messaging sequences, proposal documents, and a delivery channel — so the
base actually turns into conversations instead of a folder of CSV files.

## When to Use

- The user asks to «создать отдел продаж», «найти покупателей», «сделать
  рассылку», «подготовить КП» for a product they own.
- A contact base exists (or will) and needs to be turned into outreach.

Don't use for: harvesting the contact base itself (see
`org-contact-base-collection`), pricing a freelance marketplace order (see
`freelance-order-response`), or building a Telegram group list.

## Always-on rules

1. **Execute autonomously, deliver a report.** When the user delegates a pipeline
   build, do not ask for permission per step — build it, verify it, and hand back
   a report of what was done and what is blocked. Ask only for decisions that are
   genuinely theirs (which domain to send from, which VPS, budget).
2. **Do not promise delivery that the platform forbids.** Cold-first messaging is
   impossible on Telegram/MAX (bot cannot open a dialog) and gated by domain
   verification on email. State the real unblock step in the report — never
   promise «рассылку сделаю» and then have it silently fail.
3. **Deliver working artifacts, not plans.** A pipeline that exists only as a
   description is not a deliverable. Produce the base, the proposals, the message
   texts, and a sender that runs — then verify each.
4. **Separate what you verified from what you assumed.** In the report, say which
   channel was actually tested end-to-end and which is only configured.
5. **Do not gate the real send behind a permission question.** When the channel is
   proven and the list is the user's own base, send and report. The user grants
   full server access and expects execution; asking «запускать?» for a campaign
   that is already scoped is a confirmation loop, not caution.
6. **A rate-limited channel is batched, not abandoned.** A new sending account
   carries recipient quotas (5 recipients/hour, 10/24h) that lift on a schedule.
   Send daily batches sized to the quota and tell the user the cadence and the
   lift date — never conclude «канал не работает» from the first `429`.
7. **The legal line is the client's.** Open organizational contacts only; say that
   compliance of the campaign (unsubscribe, sender identity, advertising law) is
   the client's responsibility.
8. **Show the first-touch text before the first send.** A wave leaves in the user's
   name; one approval round costs minutes, a wrong claim costs the lead and the
   reputation. Send nothing until the user has read the exact message.
9. **Every hook is verified per lead, never inherited from the base.** A base column
   saying «сайт плохой» is a hypothesis: 8 of 13 «broken» sites in a real beauty
   salon base turned out responsive with online booking. Check the defect yourself
   (mobile emulation at 375 px, page actually rendering, contact address actually
   the company's) and either pick a different hook or drop the lead.
10. **Measure channel coverage before choosing the channel.** Count how many rows
   actually carry a usable email / Telegram / phone first: in that same base email
   covered 6%, while 523 rows had Telegram. A campaign designed for the 6% channel
   is a campaign for nobody — pick the channel the base supports and say the number
   in the report.
11. **No invented personas in the first touch.** Dry, factual, first person: who you
   are, what you saw at THIS business, what you offer, price, exit. A made-up story
   («жена не смогла записаться») breaks on the first counter-question, and the user
   will ask for it to be rewritten anyway.

## Procedure

1. **Product facts first.** Pull the real state of the product (what it does, what
   it replaced, live URL) from its KB note and its data. Do not invent features —
   the client checks.
2. **Positioning.** One file: what it is in plain words, who buys, the three pains
   it closes, how it beats «we count in Excel / we have 1C», tariff table, and the
   honest limitation (what it does NOT replace).
3. **CRM model.** Statuses from `new` to `won`/`lost`, each with the next action.
   Keep it in one JSON file; log every touch in a separate CSV.
4. **Contact base.** Harvest + enrich per `org-contact-base-collection`. Dedup by
   phone/site/name, then **dedup again by company** before messaging — one company
   must not receive the same pitch in two channels.
5. **Sequences.** First touch, reminder (day 2–3), final (day 7–10), and the
   proposal-accompanying message. Max 3 touches without a reply.
6. **Proposals.** Generate PDFs from the base. Structure that works: what the
   client gets (capability → result table), tariff composition, cost table
   (one-off vs monthly, separate), implementation time, contacts. Generate with
   reportlab + a registered Cyrillic font (DejaVu) — an unregistered font renders
   blank Cyrillic silently.
7. **File naming.** Include city + company + **full** address in the filename, and
   disambiguate collisions with the phone tail. Two branches of one network are
   legitimately separate targets, but identical filenames make them look like
   duplicates at send time.
8. **Delivery channel.** Decide by testing, not assuming — see the pitfall on
   SMTP ports. Prefer a REST mail API over SMTP when ports are filtered.
9. **Verify end-to-end.** Send one real message WITH the attachment to the
   account's own address, confirm the file opens, then unlock the list.
10. **Make the sender idempotent before the volume run.** A quota-limited channel
    must never send the same address twice. Keep a local journal (CSV) as the only
    source of truth, compute the remaining quota from the journal, and stop on the
    provider's rate-limit response. Recipe: `references/rate-limited-sender.md`.
11. **Batch under the quota and drive it from cron.** For a new account with a
    daily recipient limit, send a daily batch sized to the quota and schedule it
    (Hermes cron, `--no-agent`, wrapper under `~/.hermes/scripts/` — symlinks are
    refused). Report the cadence and the date the quota lifts.
12. **Monitor replies.** Read the inbox for answers where the key allows it, log
    them with a classification (`интерес` / `отказ` / `автоответ` / `прочее`), and
    keep read-state locally — an inbox-scoped key often cannot relabel messages.
13. **Report.** Totals per channel, coverage %, artifacts produced, what was
    actually sent vs only prepared, and the single unblock step needed.

## Handoff when the platform cannot open the dialog

When the channel is Telegram and no user account is authorised (bot cannot write
first, `api_id` unavailable), do not park the wave — hand it over as a queue the
user can send from in minutes, and keep the log on your side:

- `queue.xlsx`: №, day, company, address, `@username`, link, the exact text,
  status. Day 1 capped at 15–20 contacts.
- A `::preview` widget over the same rows with «Скопировать текст»,
  «Скопировать ссылку» and «✓ Отправлено»; the last one sends a hidden prompt so
  the journal fills itself. Details and two frame-level traps:
  `references/first-touch-handoff.md`.
- Journal (`sent_log.json`): `sent / replied / declined / unreachable`; a «мне не
  пишите» reply removes the contact from every later wave.

Manual cadence: 30–60 s between messages, 20/day per account — first-touch bursts
are exactly what Telegram's anti-spam scores.

Unblocking the automated path: `api_id`/`api_hash` come from `my.telegram.org` and
belong to the **application**, not the account — an app created under any other account
of the user logs in the main one. `Too many attempts` there is a per-IP flood, not an
account block, so it is a wait-and-switch-IP problem, never a dead end.

## Pitfalls

- **A send returning 200 proves delivery to the provider, not to the inbox.**
  Verify with a self-test that includes the attachment.
- **Message dedup must be by company, not by contact.** Deduping only by email/
  phone lets one firm receive the same pitch in WhatsApp and again in email.
- **Testing-mode email services only allow sending to your own address.** Resend
  returns `403` until a domain is verified. Do not plan a campaign against an
  unverified domain.
- **Send-only API keys cannot read status.** They return `401 restricted_api_key`
  on `/domains`, `/api-keys`, and `/emails/{id}`. Sending works; you cannot poll
  delivery — ask the recipient.
- **Batch endpoints need a broader key.** A send-only key refuses `POST /batch`;
  loop single sends with a ~1.2s pause.
- **Do not restate the product's roadmap or feature list in the proposal** — the
  client reads capability → result, not a changelog.
- **Name the unblock, not the failure.** If delivery is impossible, the report must
  say exactly which step opens it (e.g. «verify domain X»), so the user can act.
- **Never derive "already sent" from the inbox.** A sender that "checks the inbox
  first" re-sends the whole list when the key cannot read sent mail, or when the
  inbox is empty because nobody replied. The local journal is the only source of
  truth; a failed send is logged as `fail` and is not an "already sent" marker.
- **A `429` on a new account is a quota, not a broken channel.** Print the provider's
  message verbatim — it names the limit and the lift time — and switch to batching.
  Quota windows are per-account and often lift within days.
- **A contact address harvested from a site footer is often the web studio, not the
  business.** `support@`, `info@<recording-service>`, `*@<hosting>` and foreign-
  looking domains are noise: mailing them reaches a developer or nobody. Filter by
  «email domain belongs to the company's own site» before adding to the wave.
- **Do not burn parser runs hunting email for a niche that does not publish it.**
  Public `t.me/s/` channels carry no address, VK HTML without a login yields only
  service garbage, and web search over vk/zoon/flamp returns other people's mailboxes.
  If coverage is under ~10%, the niche's channel is phone/Telegram — say so instead
  of running enrichment again.
- **A personal mailbox is not a sending platform.** ~20 messages/day is the ceiling
  before the provider starts throttling; anything larger needs a verified domain and
  a sending service. Put the number in the plan, not in a footnote.

## References & support files

- `references/email-delivery-resend.md` (under `org-contact-base-collection`) —
  sending mail through a REST API when SMTP ports are filtered.
- `references/rate-limited-sender.md` — quota-aware idempotent sender: journal
  schema, quota computation, cron wiring, permission probe matrix.
- `references/first-touch-handoff.md` — first-touch approval loop, the dry message
  template (email + messenger), the manual send queue with a preview widget, and the
  journal fields that keep the next wave clean.
- `scripts/send_resend.py` — Resend sender: dry-run by default, optional PDF
  attachment, per-message logging. Copy and adjust the templates.

## Verification

- Every count reported comes from a deduped set, stated with its coverage.
- The sender was run for real at least once, with an attachment.
- Proposal filenames are unique and traceable to a base row.
- The report distinguishes «tested end-to-end» from «configured only».
