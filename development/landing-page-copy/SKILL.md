---
name: landing-page-copy
description: "Use when writing or reviewing landing page copy."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [copywriting, landing-page, conversion, cta, objections, social-proof, microcopy]
    related_skills: [generated-client-text-quality, prompt-engineering, seo-specialist]
---

# Landing Page Copy

Write and review conversion copy for a landing page: hero, body, CTAs, objection
handling, microcopy. Load when the order is "текст для лендинга", "конверсия",
"заголовок не работает", or a client asks why visitors bounce.

## When to Use

- Writing a landing page from scratch (offer, audience, conversion goal known).
- Rewriting a hero/CTA that is not converting.
- Reviewing a draft before it goes live.

Don't use for: long-form content marketing (different skill), or client replies
(see `generated-client-text-quality`).

## The one rule

**Above the fold must state the value proposition in under 5 seconds.** If a
first-time visitor cannot say what this is and who it is for after the hero, no
amount of body copy recovers it.

## Procedure

1. **Pin the brief first.** Offer, audience segment, primary conversion goal,
   traffic source, and brand voice. If the user cannot supply the goal, ask — a
   page with two goals converts on neither.
2. **Draft the hero:**
   - Headline = benefit, not feature. Prefer specificity and numbers over
     adjectives.
   - Subhead = who it is for + what changes for them (curiosity gap, not hype).
   - One primary CTA, action-first verb, value-reinforcing (never "Submit").
3. **Body:** one idea per section, written for scanning (short lines, clear
   headings). Lead with the benefit, follow with the feature that proves it.
4. **Objection handling before the final CTA.** List the real hesitations
   (price, trust, "will it work for me", "what if it breaks") and answer each in
   one or two lines. Sales-reported objections beat invented ones — ask.
5. **Social proof near the highest-friction decision points**, not dumped in a
   logo wall at the bottom. Specific testimonials (name, result, number) beat
   "Great service!" every time.
6. **Microcopy pass:** form labels, error messages, empty states, button text,
   confirmation messages. This is where drop-off hides.
7. **Mobile check.** Read the copy at a small viewport width; hero copy that fits
   desktop often pushes the CTA below the fold on a phone.

## Headline patterns that work

- Benefit-first ("Ship your bot in a day", not "Bot platform").
- Problem → agitate → solve.
- Number-driven specificity ("3 клика вместо 12 звонков").
- Audience-named ("Для мастеров маникюра, которые устали от блокнота").
- Before/after framing.

## CTA patterns

- Action-first verb ("Записаться", "Получить доступ"), not "Отправить".
- Low-commitment first step when the ask is big ("Посмотреть демо" before "Купить").
- Urgency only when true — false scarcity burns trust permanently.
- Repeat the same CTA down the page; do not rotate five different asks.
- The button copy must match what happens after the click.

## Pitfalls

- **Feature dump above the fold.** Visitors do not buy features; they buy the
  outcome. Feature lists belong in the proof section.
- **Two primary CTAs.** Competing asks split intent and convert on neither.
- **Readability above 8th grade** for consumer offers — long subordinate clauses
  kill scanning.
- **Testimonial soup.** Ten generic quotes are weaker than one specific one with
  a number in it.
- **Writing the body before the hero.** The hero decides the message; the body
  only proves it. Drafting body-first produces a page with no spine.
- **Do not promise a test result you did not run.** "A/B test lifted conversion
  from 2.4% to 3.6%" is a claim, not copy. Only state numbers you actually have.

## Verification

Before calling the copy done:

- [ ] A stranger can state the offer and audience from the hero alone.
- [ ] Exactly one primary CTA, repeated consistently.
- [ ] Every objection from the brief is answered before the final CTA.
- [ ] Social proof sits near the decision point, not at the bottom.
- [ ] Copy reads correctly at mobile width (CTA above the fold).
- [ ] No claim in the copy that the user cannot back with a real number.
