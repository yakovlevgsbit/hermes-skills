---
name: freelance-order-response
description: "Use when answering or pricing a freelance order."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [freelance, kwork, proposals, pricing, client-communication]
    related_skills: [prompt-engineering, web-code-delegation]
---

# Freelance Order Response

Write an order response (отклик) that wins the job, and price it without
working at a loss. Georgy takes these orders himself; the deliverable is
text he pastes into the marketplace form.

## When to Use

- Georgy is answering an order on Kwork / fl.ru / another marketplace.
- He asks what a job should cost, or how to fit a client's budget.
- A client pushes back on price and the scope needs re-cutting.

Don't use for: proposals to his own existing clients, or work that is not a
listed freelance order.

## Before writing: read the ТЗ for hard constraints

Extract and honour, in this order:

1. **Required opening** — if the ТЗ says "start your message with <word>", that
   word is the first line. It is a filter; missing it means instant rejection.
2. **Character limit** — count it in code, never by eye. Kwork counts
   characters *with* spaces and newlines. Leave a small margin.
3. **Required blocks** — "in your reply specify: stack, timeline, MVP price,
   examples". Every listed item must be present; skipping one loses the job.
4. **Scope items** — everything the ТЗ names is *inside* the quoted price.
   Never push a listed requirement into a paid add-on: the client reads it as
   "you did not read the brief". Only unrequested extras go outside the scope.

## Always build a live demo when the order allows it

For anything runnable (bot, parser, automation, agent), build a working demo
and give a public link in the response. This beats any description of past
work — the client clicks and sees exactly what they asked for.

- A demo is worth more than a portfolio. Georgy prefers showing only the
  *test* demo in responses, not his live production bots/agents.
- Ship the demo as a real running service, not a video or screenshots, when
  the platform allows links. Give the client a numbered click-through script
  ("1. write X, 2. ask about price, 3. send a file") so testing takes a minute.
- Build the demo's knowledge/prompt as editable separate files so the client
  sees the update path without a developer.

## Pricing

- Quote in the client's currency. For KZT clients use tenge; give rubles only
  if they ask. Convert at the current rate and state the rate you used.
- Give a range for discovery work, a single number for a fixed MVP.
- State what is *not* included and its price separately.
- Know the floor before negotiating. Below the floor, decline and say why —
  never discount into working for free.
- When the client names a budget, say plainly what does and does not fit, then
  offer the largest honest scope that fits.
- Explain a discount by a real reason (core already built and tested), never as
  a bare concession.

## Honesty rules

- Never invent portfolio links, client names, or "live bots" — the client
  checks first. If there is no demo, describe real production work by function
  without exposing client systems, or build a demo instead.
- State what was actually verified vs. what is assumed.
- Name technical risks that affect the price or the plan (see below) so the
  quote survives contact with reality.

## Pitfalls

- **Do not count characters by eye.** Run `len(text)`; a "2000 char" response
  that is 2100 gets truncated by the form and looks broken.
- **Do not move a ТЗ requirement into a paid add-on.** It reads as not reading
  the brief.
- **Do not promise a position/result the budget cannot buy.** Say what the
  money realistically achieves and what it does not.
- **Do not send the same text at several budget levels.** Rewrite scope to fit
  each budget instead of shaving the price.

## Reusable technical points that change the quote

Raise these in the response — they show competence and prevent underquoting:

- **Telegram Bot API file limits.** A bot cannot *download* files over 20 MB
  (`getFile`); it can *send* up to 50 MB. For large source files (CDR/DXF)
  forward the message to the manager instead of downloading — originals keep
  full quality. Storing files needs a local Bot API server (up to ~2 GB).
- **LLM cost.** Quote per-dialog cost with a cheap model (e.g. gpt-4o-mini:
  ~0,3–0,5 ₽ per dialog) and give a monthly figure at the client's volume, so
  the running cost is not a surprise.
- **no-code vs code.** Recommend code when the task needs file handling, real
  dialog memory, or an editable prompt/KB — say why in one line each.
- **Contact-base coverage.** Map catalogs (2GIS/Yandex) carry email for only
  ~3% of organizations; websites are present for 30–60%, and 50–70% of live
  sites yield an address. So an email base is a two-stage job (harvest orgs,
  then scrape their sites) and N emails needs several times N organizations
  across many cities. Quote the count the method yields, not the count asked
  for — see `org-contact-base-collection`.
- **Page-speed order.** When the order is an audit or an optimisation, measure
  the live site first and quote from the real numbers — the dominant cause is
  usually one resource group, and naming it wins the job. Method, calibration
  table and the before/after КП structure: `web-performance-audit`.

See `references/pricing-notes.md` and `references/telegram-bot-quote-risks.md`.
When the client asks for the plan as a PDF (КП), follow
`references/proposal-pdf.md` — Cyrillic font registration, the section order a
client expects, and the totals layout.

## Kwork order quick analysis

When a Kwork project link arrives:

1. **Open `/projects/<id>/view`** — the `/new_offer` link redirects to login; the view page is public.
2. **Extract in 30 seconds**:
   - Task description (what needs building)
   - Budget: desired / acceptable
   - Client: name, projects posted, hire rate %, time left
   - Proposals count (competition level)
3. **Quick verdict — this is advice, not a gate.** Georgy decides; he often bids on a crowded low-budget order anyway ("будем биться") when he has a ready demo or wants the client's repeat work. State the odds in one line, then produce the response he asked for — do not refuse or argue the heuristic.
   - Proposals > 100 + low budget (≤3000₽) → low odds; bid only with a demo or a concrete edge, and say the odds plainly.
   - Proposals 40-100 + medium budget (5000-20000₽) → worth a tailored response.
   - Client hire rate < 30% → they may not actually hire.
   - Client with 0% hire rate (first order) → higher risk, but less competition.
   - **When bidding against 100+ competitors, the only differentiator is concreteness**: name the exact stack, a single price at or just under the desired budget, a short timeline, and a demo link if one exists. A generic "сделаю качественно" is invisible in that queue.
4. **Response template** (paste into Kwork):
   ```
   Здравствуйте!
   [Concrete solution in 1-2 sentences]
   
   **Что входит:**
   - [Scope item 1]
   - [Scope item 2]
   - [Scope item 3]
   
   **Срок:** X дней.
   **Цена:** Y ₽.
   
   [Demo link if available]
   Готов приступить сразу.
   ```
5. **Price anchoring**: Quote 10-20% below max acceptable budget. If budget is 7000-21000₽, quote 5000-6000₽. If budget is 1500-4500₽, quote 1200-1500₽.

## Live demo as differentiator

For any runnable task (bot, parser, panel, automation):
- Build a working demo in 1-2 hours
- Deploy to VPS with public HTTPS
- Include in response: "Demo: https://domain/panel/ (login: demo/demo)"
- Add click-through script: "1. Click X, 2. Fill Y, 3. See result"

This beats 95% of text-only responses. Even a minimal demo shows you can deliver.
