# Marketplace listing specs

Per-platform requirements for listing assets and fields, plus the verified render recipe. Add a platform section when the user targets a second marketplace.

## Kwork (kwork.ru)

### Cover image

| Requirement | Value |
|---|---|
| Minimum size | 660 × 440 px |
| File weight | 30 KB – 10 MB |
| Formats | jpg, jpeg, png |

A good, selling cover: a thematic image illustrating the service; sharp, not blurred; **text not cropped and readable even at the kwork thumbnail size**; text free of spelling and grammar errors.

The listing is returned for rework if the cover has: bright "acid" colours or hypnotic backgrounds; any 18+ imagery (alcohol, sex, smoking, weapons, violence); profanity or slang; **contact details or requests for contacts (including social-media logins)**; watermarks.

Compose **vertically** for this box: title → subtitle → icon → feature line → price, centred column. A horizontal banner layout inside a 660×440 frame leaves the text cramped.

### Creation-form fields

| Field | Notes |
|---|---|
| Вид (category) | single choice, e.g. «Написание и доработка» |
| Язык разработки | checkboxes — mark only the languages the work is actually done in |
| Платформа | checkboxes — mark every platform the listing covers |
| Обложка | required, per the spec above |
| Описание | required, min 100 / max 1200 characters |
| От покупателя нужно | required, min 100 / max 500 characters — what the buyer must supply |
| Цена, срок | the listing's price and delivery window |

The category screen carries no price field — it appears after «Продолжить». Read the whole form before assuming a field is missing.

### Buyer-input block ("От покупателя нужно")

Shape that reads as low-friction and protects scope:

```
Для старта мне нужно:
1. Описание задачи — что должен делать бот, какие разделы.
2. Примеры текстов/сообщений, если есть.
3. Если нужна интеграция — доступ к ней (ссылку на таблицу дайте на просмотр, или название системы и ключ API).
4. Ваш Telegram для связи и тестирования.
Если точного ТЗ нет — опишите словами, я помогу сформулировать.
```

The last line is the conversion lever: it keeps a buyer without a written spec from abandoning the order.

## Cover render recipe (verified)

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 660, "height": 440}, device_scale_factor=2)
    pg.goto("file:///abs/path/cover.html")
    pg.wait_for_timeout(1200)
    pg.screenshot(path="cover.png")
    b.close()
```

`device_scale_factor=2` gives a crisp upload from a small viewport. Then run a **critical** vision check on the PNG — text cut off, overlapping elements, thumbnail legibility, typos — not a confirming one. Adjust the HTML and re-render; two or three rounds is normal.

Deliver with `MEDIA:/abs/path/cover.png` so the user can download inline, and state that scratch copies expire so the durable copy must land in the KB.

## Listing text shapes

- **Hook:** what it is, in the buyer's words, plus the choice that matters to them (stack, scope).
- **What's included:** 4–5 bullets, each an item the price genuinely covers — never an item that belongs to a higher tier.
- **Price + deadline:** plain, no «от».
- **Demo link:** one publicly reachable URL proving the class of work.

Profile "about" block: who you are → what you build (2 lines) → the differentiator (working demo, shipped turnkey) → where to see it. No invented years, clients, or stack.

