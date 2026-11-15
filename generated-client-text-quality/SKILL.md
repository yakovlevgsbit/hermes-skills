---
name: generated-client-text-quality
description: "Use when LLM-generated text goes to a client unreviewed."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [llm-output, client-facing, guardrails, humanize, boilerplate, outreach]
---

# Generated Client Text Quality

Enforce that LLM-generated client-facing text (freelance replies, outreach pitches, bot answers, notification copy) is actually sendable, without a human re-reading every generation.

## When to Use

- A pipeline, cron job, or daemon generates text that goes to a **client, prospect, or end user** — not to your own chat.
- The user has complained the output sounds robotic, template-like, or gets cut off mid-sentence.
- You are writing `REPLY_RULES` / a system prompt whose output is delivered without review.

## The two failure modes that ship by default

An unprompted model produces client text that fails in two ways, and both are invisible until the client sees them:

1. **Boilerplate voice.** Formulaic openers and closers that read as a bot: «Понял задачу», «Готов обсудить детали», «Буду рад сотрудничеству», «технически вижу так».
2. **Truncation.** The model hits `max_tokens` and stops mid-sentence, so a pitch arrives ending on a dangling word («От этого зависит, как»).

Prompt rules alone do not reliably prevent either on small models. **Add a post-generation guard in code** — the check is cheap and the failure is expensive.

## The AI-ism list (prompt rules AND post-check)

A third failure mode ships alongside the two above: text that is grammatically
clean but reads as machine-written. It survives every truncation and banned-phrase
check because it is not broken — it is just soulless. Catch it in two places:

- **In the prompt:** name the specific patterns to avoid, not "write naturally".
- **In the post-check:** grep the produced text for the same patterns.

| Pattern | Examples to ban |
|---|---|
| Sycophantic openers | «Отличный вопрос!», «Конечно!», «С удовольствием!» |
| Stock vocabulary | leverage, utilize, streamline, navigate, robust, seamless |
| Hedging stacks | «стоит отметить, что», «важно понимать, что» |
| Filler transitions | Furthermore, Moreover, In conclusion, «Более того» |
| Hollow closers | «Буду рад сотрудничеству», «Готов обсудить детали» |
| Em-dash overuse | more than one or two per paragraph |
| "There is/There are" openers | «Есть несколько моментов…» as a paragraph start |
| Headers that restate the paragraph | «## Заключение» above a conclusion sentence |

Preserve while stripping: code blocks, URLs, technical terms, the author's actual
meaning, and sentence structure that is not pattern-matched. The goal is to remove
the *mechanical* patterns, not to rewrite the piece in your own voice.

## Procedure

1. **Write the prompt rules first.** Describe the target voice concretely: first person, start at the substance or a genuine reaction to the brief, no «here is the reply» preamble, end on a real question or concrete next step. Give a length range (e.g. 120–200 words). State the safety rules that never change: never invent experience, never fabricate portfolio links, never promise what was not built.

2. **Size `max_tokens` above the target length, then guard anyway.** A length ceiling that the model fills exactly will clip the last sentence. Give real headroom (a 120–200 word reply needs ~900 tokens, not 600) and *also* detect truncation, because a long reply can still run over.

3. **Encode the guard in the generator function:**
   ```python
   BANNED = ["понял задачу", "готов обсудить детали", "технически вижу", "вижу так"]

   def looks_truncated(text):
       t = text.rstrip()
       return bool(t) and t[-1] not in ".!?»\"…"

   def build_reply(...):
       best = ""
       for attempt in range(2):
           cand = clean(call_model(prompt, max_tokens=900))
           if not cand:
               continue
           if not (has_banned(cand) or looks_truncated(cand)):
               return cand
           best = best or cand
       return best
   ```
   Reject on **either** a banned phrase or truncation, retry, and keep the first non-empty candidate as a fallback so a total model failure still returns something rather than an exception.

4. **Ban the shortest distinctive form of each phrase — the model drops and swaps qualifiers.** An entry like «технически вижу» matches only text that still contains «технически»; the same sentence with the qualifier dropped («По пунктам ТЗ вижу так:») or replaced («вижу это так») sails past it. List the short forms as separate entries («вижу так», «вижу это так») so every variant is a substring of something banned. After a live test, **grep the produced text for the pattern you assumed was caught** — a user screenshot is the cheapest regression test you will get, and a variant that slipped through is a signal to widen the list, not to trust the prompt.

5. **Test on three genuinely different briefs, not one.** The same prompt behaves differently on a payment brief, a backend brief, and a bot brief. Run all three and confirm zero banned phrases and `looks_truncated() == False` on each before calling the change done.

6. **Run the real pipeline once end to end after the edit** (cron job, daemon, or the script the scheduler calls) and confirm delivery. A generator that passes a unit test but is never exercised in the scheduler is not verified.

7. **Do a readability pass on the finished text.** Passive chains longer than two sentences, five-item bullet lists that should be prose, and headers that repeat the next line all read as machine output. Technical audiences: grade 10–12; consumer audiences: grade 8 or below.

## Pitfalls

- **`.lower()` both sides of the banned-phrase check.** Case and Cyrillic homoglyphs will otherwise slip a match.
- **An empty model response is not a clean one.** Guard `if not cand: continue` before any `.rstrip()` or indexing, or the truncation check raises on the retry path.
- **A banned phrase in a *comment or docstring* of your own generator** will match the same grep you run to audit output. Describe the mechanism without quoting the phrase.
- **Do not silently ship the retry if it is worse.** Keep the cleaner of the two candidates rather than always returning the last one.
- **Changing the generation prompt is a change to what a client receives** — re-run the live pipeline, not just the function, and report which output changed.
- **Stylistic cleanup is not a substitute for the content check.** A beautifully de-slopped pitch that invents a portfolio link is still a lie. Run the truncation and banned-phrase guards first, the style pass second.
