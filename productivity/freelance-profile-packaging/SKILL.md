---
name: freelance-profile-packaging
description: "Use when writing a freelance listing or order отклик."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [freelance, marketplace, kwork, listing, pricing, covers, capability, lead-filter]
---

# Freelance Profile Packaging

Turn a capability inventory (skills suitcase, shipped demos) into a marketplace profile that converts leads: specialization, listing set, texts, covers, prices, tags.

## When to Use

- The user wants a profile on a freelance marketplace (Kwork, FL.ru, Upwork), or new listings/kworks on an existing one.
- The user asks for listing texts, covers, tags, or prices.
- A lead scanner's niche filter must change because the capability set changed.
- The user asks "what do I put as my specialty / what tags / what price".
- The user wants an отклик (bid) on someone else's posted order — see «Order responses» below.
- The user asks "как откликнуться / напиши отклик на заказ".

## Always-on rules

1. **Capability first: the profile, every listing, and the lead scanner's filter all derive from ONE inventory of what is actually shippable.** Before writing a word, list the demo URLs that return 200 publicly and the skills that cover the work. A listing promising what no skill or demo backs wins the order and loses the dispute.
2. **Narrow specialization beats broad.** «Telegram-боты» converts; «программирование» disappears among all programmers. Pick the single subcategory the strongest demo proves; add secondary tags only to widen search.
3. **Never fabricate reviews, ratings, or experience.** Cite only demos that are publicly reachable right now — a demo behind a login wall is worthless in a listing and embarrassing to send.
4. **Do not over-promise scope at a low price.** A cheap listing naming an enterprise integration (CRM, ERP) sets up the «мне обещали X, а сделали Y» dispute. Name only what the price genuinely buys; route bigger scope to a higher-priced listing or to «обсудим отдельно».
5. **Mixed pricing on a zero-review profile: cheap listings buy the first reviews, mid-priced listings buy the money.** Ship both, not either — pure-cheap never reaches an income target, pure-expensive never sells without reviews.
6. **Free-response channels first when the user has an income target and no reviews.** Never recommend a pay-per-response platform (FL.ru, Workzilla) as the primary channel: the user spends before earning and unproven slots rarely convert. Keep it as a scanner information source and say so. Channel economics and reachability live in `references/marketplace-economics.md`.
7. **Close every package with what the profile must NOT do** (fake reviews, over-promise, dead demo links), not only the sell. The user reads the limits before the platform does.

## Procedure

1. **Inventory capability before writing anything.** Public demo URLs with live status codes, the skills suitcase, one line per item on what it closes. This is the only source for every claim that follows.
2. **Pick the specialization from the strongest demo**, then the listing set from the inventory — ~5 listings covering the price ladder (2 cheap / 3 mid on a zero-review profile).
3. **Write each listing as hook → what's included (bulleted) → price + deadline → demo link.** Keep «what's included» to items the price actually covers.
4. **Get the platform's asset spec BEFORE generating any cover.** Read the user's screenshot of the creation form or the platform's upload rules and record: minimum pixel dimensions, file weight range, accepted formats, forbidden content, and whether the thumbnail must stay readable. A cover rendered to the wrong format is a full re-render, not an adjustment — a banner-shaped asset inside a portrait spec frame crams the text and has to be redone.
5. **Generate covers through the coding sub-agent, then render and verify.** The sub-agent writes the HTML; you render it at the exact spec size in headless Chromium with `device_scale_factor=2` and run a *critical* vision check (text cut off? overlapping? readable at thumbnail size? typos?). Compose vertically (title → subtitle → icon → features → price) when the spec box is square-ish or portrait; a horizontal banner layout inside that frame leaves the text cramped. If the sub-agent's frame is malformed but its logic is sound, integrate the working part into a verified frame and say which part was hand-integrated — do not rewrite the logic, and do not self-serve the whole deliverable.
6. **Fill the required buyer-input field.** Marketplaces require a «what I need from you» block with a minimum character count; left empty it blocks publication. Write it as a numbered list — task description, example texts, access/credentials, a contact for testing — and end with a line that removes the barrier for a buyer with no written spec («если ТЗ нет — опишите словами, я помогу сформулировать»).
7. **Tags: 3–7 per listing, each mapped to a real capability.** Extra tags dilute the listing in search; a tag with nothing behind it loses the order.
8. **Hand the texts over one at a time in copy-paste blocks** with the field name above each. The user fills the platform form while reading; five listings in one wall of text is unreadable and invites half-filled forms.
9. **Save the package to the KB before it is consumed** (`clients/<marketplace>-profile.md` plus the cover files) and warn that scratch copies expire — the user downloads now, the durable copy lives on the VPS.

## Expanding a lead scanner's niche filter alongside a new capability set

When the listing set widens, the scanner's keyword filter must widen with it — and the filter is where false positives are born.

- **Ban short, generic trigger words.** «магазин», «смс», «сервер», «max» match a hundred unrelated orders and bury the real ones; use only the distinctive form («интернет-магазин», «ivr», «макс»).
- **A stop-list entry correctly overrides a niche hit.** An order titled «Shopify интеграция с 1С» is not shippable without a 1С developer — rejecting it is correct behaviour, not a filter bug. Do not "fix" a rejection whose mechanism is sound.
- **Run a pass/fail battery before shipping a filter change:** several titles that must pass (one per new niche) and several that must be rejected (design, copywriting, foreign stacks). Expect the foreign-stack case to reject even when a niche word is present, and count that as a pass.
- **The filter must match capability, not ambition.** Adding a niche word the suitcase cannot close produces leads the user cannot convert, which reads as incompetence rather than breadth.

## Order responses (отклики)

An отклик is a bid on someone else's posted order — a different artifact from a listing, and it is read against dozens of competitors. Shape and full template in `references/order-response-shape.md`. Always-on rules:

1. **Start with the order's required keyword, literally first.** Many orders end with «начните сообщение с <слово>». Miss it and the отклик is filtered before it is read. Put the keyword as the very first characters, then a blank line.
2. **Answer every item the order explicitly demands.** «В отклике укажите: стек, сроки, стоимость MVP, примеры» is a checklist — a missing item reads as inattention. Walk the list and hit each one.
3. **Never fabricate demos, examples, or reviews.** When the order asks for «примеры ваших живых ботов», an invented URL or fake case is the fastest way to lose — the client checks first. Offer the real, honest set (production bots, real agents) and, if a closer match is needed, offer to build a small live demo before the deadline. Never write a link you have not confirmed returns 200.
4. **Lead with proof you read the task.** One or two sentences naming the client's actual situation (their product, their competitor, their constraint) beat any generic «готов выполнить».
5. **Recommend a stack and justify it against the alternatives the order named.** Orders usually offer a choice (code vs no-code). Pick one and give the concrete reason tied to their requirements — not «я так привык». Name the requirement that decides it.
6. **Price as a ladder: MVP first, then stages.** Give an MVP price they can say yes to today, then 1–2 optional stages with their own price and outcome. «Начать с MVP, посмотреть на живых данных, решать дальше» lowers the entry barrier.
7. **Surface the technical landmine that shows competence.** State the non-obvious constraint before the client hits it (file-size limits, API caps, per-call LLM cost) with its workaround, and ask the clarifying question that decides the architecture. One named risk beats a feature list.
8. **Quote in the client's currency.** A client in Almaty thinks in ₸, one in Moscow in ₽. Give the other currency only as a parenthetical reference and note the rate floats.
9. **When the budget is capped, say so honestly and scope to it.** State what the full job costs, what genuinely fits the cap, and what the capped version will and will not deliver. Silently trimming scope to hit a number sets up the dispute; naming the gap builds trust and often wins the order anyway.
10. **Offer the demo build as the closer when the honest example set is thin.** A live demo of the exact requested behaviour (built small, before the deadline) converts better than any description — present it as an option, not a promise you cannot keep.

## Pitfalls

- **The user's screenshot of the form IS the spec.** Fields visible there (category, language checkboxes, platform, cover uploader with its requirements panel, the buyer-input block) are the contract — read them before producing anything, and re-read them when the user sends a new one, because the spec may contradict what you assumed.
- **A listing set that all sits at one price cannot reach a target.** If the user states an income goal, make the ladder explicit and say why: reviews come from the cheap end, revenue from the mid end.
- **Do not widen the scanner's filter and the listing set independently.** They are one capability statement in two places; drift between them produces either missed leads or orders the user cannot close.

## references

- `references/marketplace-listing-specs.md` — Kwork cover and field requirements, the render recipe, and the per-listing text shapes.
- `references/marketplace-economics.md` — cost-of-contact per platform, platform reachability probes, international channel pack, and the sequence for a stated income target.
- `references/order-response-shape.md` — the section-by-section shape of a winning отклик, with a worked example and the honesty rule for missing examples.
