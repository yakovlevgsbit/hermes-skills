# Order response (отклик) shape

A bid on someone else's posted order. Read against dozens of competitors, so the
first line decides whether the rest is read at all. The rules in SKILL.md
«Order responses» are the contract; this file is the shape and a worked example.

## Section shape

1. **Required keyword** — literally the first characters of the message, alone on
   the first line, blank line after. Then a greeting.
2. **Proof you read the task** (1–2 sentences) — name the client's actual
   product, competitor, or constraint. This is the only part that cannot be
   copy-pasted between orders.
3. **Answer the demanded checklist** — every item the order listed («укажите:
   стек, сроки, стоимость»). Same order as the order.
4. **Recommended stack + the reason it wins** over the alternative the order
   named. Tie it to one of their stated requirements.
5. **Scope + price ladder** — MVP first (a price they can say yes to today),
   then 1–2 optional stages, each with its own price and outcome.
6. **The named technical landmine** + its workaround + the one clarifying
   question that decides the architecture.
7. **Honest example set** — real demos only, or the offer to build a live demo
   of the exact behaviour before the deadline.
8. **Close** — «готов начать / готов ответить на вопросы», and offer the detailed
   PDF or plan.

## Worked example skeleton

```
<КлючевоеСлово>

Здравствуйте! Разобрал задачу.

<2 sentences naming their product + the constraint that shapes the work.>

Почему <рекомендуемый стек>, а не <альтернатива из заказа>
<1–2 reasons tied to their requirements: file sizes, memory, editable prompt.>

Что предлагаю:
| Этап | Что входит | Срок | Стоимость |
|---|---|---|---|
| MVP | ... | 2 недели | ... |
| Этап 2 | ... | +1 неделя | ... |

Что важно знать заранее
- <landmine> — <workaround>. Уточните: <the deciding question>?

Примеры
- <real demo, or: соберу небольшое живое демо под эту задачу до дедлайна>

Готов начать. Могу прислать подробный план в PDF.
```

## The honesty rule for examples

When the order asks for «примеры ваших живых ботов/работ» and the on-hand set is
adjacent rather than exact, do NOT invent. Two acceptable moves:

- **Adjacent-real:** list what genuinely exists in production and say plainly how
  it differs from the order's ask. Verification survives a conversation.
- **Build-the-proof:** offer to ship a small live demo of the exact requested
  behaviour before the deadline. This converts better than any description and
  cannot be checked false.

An invented URL or a fake case study is the one failure that ends the bid on the
spot — the client's first action is to open the link.

## Currency

Quote in the client's currency. For a Kazakh client the working rate has hovered
around 1 ₸ ≈ 0,19 ₽ (1 ₽ ≈ 5,3–5,4 ₸) — give ₸ as primary, ₽ as a parenthetical
reference, and note the rate floats, so a fixed ruble price needs a buffer or
should be pegged to ₸.
