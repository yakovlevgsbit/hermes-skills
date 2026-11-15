# First-touch handoff: approval, text, queue, journal

Everything between «base is ready» and «messages are out», for channels the agent
cannot send on itself.

## 1. Approval loop

The user reads the exact text before the first message leaves. Order that works:

1. Show the message once, with the substitution table (`{problem}` by segment).
2. Ask only the questions that change the text: is the price current, is the demo
   link the right one, dry tone or not.
3. Rewrite on the spot, re-show, then send.

Showing a finished text with placeholders beats describing it: the user corrects a
sentence, not a concept.

## 2. Verifying the hook per lead

Never ship a claim you have not reproduced on the lead's own page.

```python
new_tab("about:blank")
cdp("Emulation.setDeviceMetricsOverride", width=375, height=812, deviceScaleFactor=2, mobile=True)
goto_url(url); wait_for_load(); sleep(2.5)
js("({iw: innerWidth, sw: document.documentElement.scrollWidth})")
```

- `sw > 405` at 375 px → breaks on phones, honest hook.
- 375–395 → normal; scrollbars and sliders account for the few pixels.
- Page of 9 KB instead of ~100 KB → placeholder «site not working», strongest hook
  there is.
- `site` field = `t.me/<channel>` → no site at all; the message must say that, not
  «site not responsive».
- `site` = yclients / dikidi / taplink / sonline → someone else's booking page.

Segment accordingly and keep one claim per message.

## 3. Message shape (dry, 5 blocks)

```
Здравствуйте! Пишу по «{Название}», {адрес}.

{Одна проверенная проблема, словами клиента}.

Делаю сайты для салонов в {город}: работы, цены и запись в два касания,
заявка приходит вам в Telegram — без звонков и администратора.

Пример, как это выглядит (демо, студия вымышленная): {ссылка}
От {цена} ₽, срок — {срок}.

Если не актуально — ответьте «нет», больше не напишу.
```

Email variant differs in three ways only: a subject line that names the business
(«Сайт «{Название}»: запись с телефона»), no attachments on the first touch, and a
closing line with source + opt-out («Письмо отправлено на адрес из открытой
карточки в 2ГИС. Не хотите получать письма — ответьте „отписаться“.»).

Before sending, grep the text for `px, jQuery, вёрстк, адаптив, CSS, PHP, рендер,
библиотек` — the owner is not a developer, technical facts read as noise.

## 4. Manual queue + widget

`queue.xlsx`: `№ | День | Компания | Город | Адрес | @username | Ссылка | Статус | Текст`.
Day 1 = 15–20 rows, day 2 = the rest.

Widget over the same rows (`::preview{file="queue_day1.html"}`):

- «Скопировать текст» / «Скопировать ссылку» — `navigator.clipboard.writeText`,
  fallback to a temporary `<textarea>` + `execCommand('copy')`;
- «Открыть чат» — try `window.open`, and if it returns null, copy the link instead;
- «✓ Отправлено» — `data-hermes-send` / `window.hermes.send(...)` with the real
  username, so the journal fills from the click;
- print the URL as selectable text under the buttons.

Two traps, both silent:

1. **Preview iframes block popups.** `target="_blank"` and `window.open` do nothing;
   the link must be copyable.
2. **The widget is generated from a Python f-string.** `${{c.uname}}` renders as
   `${c.uname}`; inside single quotes it stays a literal and the button sends the
   raw template. Use backticks in JS. Verify by stubbing
   `window.hermes = {send: t => arr.push(t)}`, clicking, and printing `arr`.

## 5. Journal

```json
{"wave": "<channel>-day1", "total": 15,
 "sent": [], "replied": [], "declined": [], "unreachable": [],
 "notes": []}
```

Rules: a missing username in a «sent» event means the event is unusable — fix the
widget rather than guessing the row. `declined` and `unreachable` are permanent:
they never enter a later wave.
