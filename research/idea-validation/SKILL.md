---
name: idea-validation
description: "Use when pressure-testing a product idea before building."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [validation, product-idea, go-no-go, competitors, demand, anti-sycophancy]
    related_skills: [competitor-news-monitor, research-analyst]
---

# Idea Validation

Pressure-test a product or service idea and give a go / no-go call with the
evidence behind it. Load when the user pitches something and asks "стоит ли",
"есть ли спрос", "не поздно ли", or is deciding what to build next.

## When to Use

- The user has an idea and wants it attacked before investing time.
- The user is choosing between two directions.
- The user asks whether a market is saturated.

Don't use for: validating an idea the user has already committed to building —
at that point the useful work is execution risk, not a verdict.

## The anti-sycophancy rule

**You do not validate an idea because it sounds clever.** You hunt for the
mistake, the missing demand, or the distribution failure that will kill it.
If it survives scrutiny, say so plainly and shift to execution — but the default
posture is skepticism, and praise must be earned, not given.

## Procedure

1. **Extract the four claims** the idea rests on: the problem, the audience, the
   assumed differentiator, and the monetization. Write them down before searching.
   Most ideas fail on a claim the founder never noticed they were making.
2. **Demand.** Is there evidence people already pay to solve this? Look for:
   - existing competitors with customers (the strongest signal);
   - search volume and the intent behind it;
   - communities where the pain is voiced (Telegram, forums, Reddit);
   - "free alternative" usage — what people cobble together today.
3. **Competition.** Map direct competitors and indirect substitutes. For each:
   who they serve, what they charge, their visible weakness, and why a customer
   would switch to you. "Nobody does this" usually means "nobody pays for this".
4. **Differentiation.** Test the claimed advantage. Is it a moat (data, network,
   distribution, cost structure) or a feature anyone can copy in a week? A feature
   is not a business.
5. **Distribution.** How does the first paying customer arrive? This kills more
   ideas than demand does. "Post on social media" is not a distribution plan.
6. **Execution risk.** What is the smallest version that proves demand, and how
   long does it take to build? If the MVP is a month, the validation is not an MVP.
7. **Verdict.** Go / no-go / pivot-to-X, with the single fact that decides it.

## Output format

```
VERDICT: <go | no-go | pivot to X>

THE FOUR CLAIMS
<problem / audience / differentiator / monetization, restated>

WHAT THE EVIDENCE SHOWS
<demand, competitors, differentiation — each with the source>

THE KILLER RISK
<the one thing most likely to end this, and what would disprove it>

CHEAPEST TEST
<the smallest thing to build or do that produces real evidence>
```

## Pitfalls

- **Flattery dressed as analysis.** "This is a great idea and here is why" is
  sycophancy. If the evidence is weak, the verdict is no-go.
- **"No competitors" read as opportunity.** It almost always means no market.
  Check for failed attempts and free substitutes before celebrating.
- **Market-size numbers with no source.** "The market is $10B" is not evidence;
  it is a slide. Use only figures you found and can cite.
- **Confusing enthusiasm for demand.** People saying "cool" is not a willingness
  to pay. Look for existing spend on the same problem.
- **Ignoring distribution.** A validated problem with no reachable customer is
  still a dead business.
- **Never invent a competitor's metrics.** If traffic or pricing is not public,
  say it is unknown rather than estimating silently.

## Verification

- Every factual claim in the verdict traces to a source you actually fetched.
- The killer risk is stated as something that could be **disproven**, not a vague
  worry.
- The cheapest test produces real evidence (a payment, a signup, a conversation),
  not more opinion.
