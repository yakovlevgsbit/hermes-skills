# Site quality audit over a harvested org base

Turning a harvested base into a ranked list of *sellable* prospects: which orgs have
no site, a dead site, or a site that is visibly broken/crusty — i.e. who to pitch a
new site to. This is the stage after `org-contact-base-collection`.

Reusable scripts live in `/root/.hermes/cache/scratch/`: `probe_sites.py` (HTTP probe),
`era.py` (HTML/CSS era markers), `cringe.py` (old-web artifacts), `build_xlsx.py`
(scoring -> xlsx). Copy them out of scratch before relying on them long-term; scratch
is pruned.

## 1. Host-level dedup before any counting

Multi-branch orgs share a domain. Collapse the base to **one record per host**
(`dict.setdefault(host, rec)`) — the raw rows overstate the number of sites several
times over (528 filled `Веб-сайт` cells -> 128 distinct hosts on a 1531-row base).
Report `rows`, `rows with site`, `distinct hosts`, and `own domain` as four separate
numbers; the client conflates them otherwise.

## 2. Split platform hosts from own domains — this is the headline finding

Most "websites" in an RU local-business base are **not sites at all**, they are
booking-frontends and link-in-bios pages. Classify by host suffix before probing:

| Bucket | Host patterns | Verdict |
|---|---|---|
| Booking aggregator | `dikidi.net/.ru/.app`, `yclients.com/.ru`, `mst.link`, `link.beautybox.ru`, `profsalon.org`, `beautyagent.ru`, `dikidi.online`, `dkd.su`, `записьонлайн.рф`, `блиц-запись.рф` | its own vendor's page; nothing to sell |
| Link-in-bio / messenger | `taplink.cc/.ws`, `t.me`, `vk.link`, `vk.ru`, `max.ru`, `ylink.me`, `invite.viber.com`, `yandex.eu/maps` | no site at all — that IS the pitch |
| Free/builder subdomain | `*.tilda.ws`, `*.tilda.site`, `*.clients.site`, `*.onligo.ru`, `*.tb.ru`, `*.plp8.ru`, `*.obiz.ru`, `*.see.ru`, `*.uds.app`, `*.moiprofi.ru`, `crеatium` | hand-made by the owner: often dead or crusty |
| Own domain | everything else | audit these in depth |

Count of "no own domain" is a selling point on its own — 405 of 528 on the sample
base — and it is far cheaper to establish than a per-site audit. Deliver it first.

## 3. Liveness probe (plain HTTP, thread pool)

Fetch with a real desktop `User-Agent`, `timeout=20`, `verify=False`, and classify:

| Result | Meaning | How to confirm |
|---|---|---|
| DNS failure (`NameResolutionError`, `getent hosts` empty) | domain expired/dropped | `getent hosts <h>`; retry twice before writing it off |
| connect timeout on 80 and 443 | host dead or firewalled | `curl -m 20 -w '%{http_code}'` |
| 200 on the probe, `103`/`402`/`403`/`404`/`500` from `curl -L` | server is Cloudflare-challenging the client, or genuinely broken | always re-check a non-200 with `curl -L` before calling it broken |
| parking page (`Этот домен был создан`, `testdomain.ru`, `lpmotortest.com`) | parked | grep the body for `домен.*создан`, `for sale`, `parking` |
| `403 Page not found` / `402 Please renew your subscription` on `*.tilda.ws` | Tilda page deleted or subscription unpaid | follow the exact URL from the base; the root often differs from the deep link |

A dead site plus a live business (phone, reviews) is the strongest pitch in the whole
list — keep these in a separate sheet, do not bury them in the ranking.

## 4. Mobile measurement — the dominant "crusty" signal

Run through Browser CDP, one host at a time:

**Order matters: set the emulation BEFORE navigating, on a blank tab.** Metrics
applied after the page has loaded are not always picked up by the layout, and the
measurement then reports a desktop layout for a site that is in fact responsive.

```python
new_tab("about:blank")
cdp('Emulation.setDeviceMetricsOverride', width=375, height=812, deviceScaleFactor=2, mobile=True)
goto_url("http://" + host); wait_for_load(); time.sleep(2.5)   # NOT 1s — sliders init late
m = js("({iw: innerWidth, sw: document.documentElement.scrollWidth, vv: visualViewport.width})")
```

Read `visualViewport.width` too: it stays 375 when the layout is genuinely mobile, and
only `innerWidth` growing means a desktop layout was served. Discriminate on the
combined triple, not on `scrollWidth` alone.

| Observation | Diagnosis |
|---|---|
| `sw > vv + 30` | horizontal scroll on a phone — broken mobile |
| `iw` stays 700–1300 while `vv` is 375 | the layout itself is fixed-width (viewport meta present or not) — a 1280 px canvas squeezed onto the phone: microscopic text, pinch to read |
| `iw = sw = 375`, media queries present | fine, drop it from the shortlist |
| `iw = 383–395` | scrollbar/transform shim — **not** a defect, do not report |

**Wording discipline.** `iw > 420` is measured; "no mobile version" is an inference and
is often wrong — some of these pages carry a correct `width=device-width` meta and
still lay out at 991 px. Phrase it as «вёрстка не сжимается: страница Npx при экране
375px», never as «мобильной версии нет». A re-measured batch overturned 3 of 10
"desktop" verdicts this way, one of them the session's headline finding — so re-measure
any single host you are about to name as the worst before reporting it.

Sleep 3 s before measuring: slick/swiper carousels reach their real track width only
after init, and at 1–2 s they report a clean 375 px for a page that in fact overflows.
Confirmed on a live host: 375 px at 2 s, 1257 px at 3 s. Take the **worst** of several
samples when merging batches, and name the overflowing element
(`div.slick-track`, width 5421) so the finding is actionable rather than a number.

Count `@media` in `document.styleSheets` (wrapped in try/except — cross-origin rules
throw) as a second opinion: zero media queries plus a 1257 px body is conclusive.

## 5. Era / crustiness markers (HTTP only, cheap, no browser)

Grep the HTML **and every linked CSS** (follow `<link rel=stylesheet>` + `@import`, up
to ~8 files) for: `display:flex|grid` (absence + `float:` and `position:absolute` heavy
= pre-2015 layout), `jQuery 1.x|2.x`, `bootstrap.min.css` + `col-md-`, `<font>`,
`<center>`, `cellspacing`, `bgcolor=`, `align=left|center`, `.swf`, `min-width:9xx px`,
`user-scalable=0`, `X-Powered-By: PHP/5.x|7.2|7.3` (EOL), and a lone `© 2013`.

Two traps that produce false findings:

- **A lone copyright year is the signal; a range is not.** `© 2013` = forgotten footer,
  `© 2013 - 2026` = maintained. Regex the pair: `(?:©|&copy;)\D{0,30}(\d{4})(?:\s*[-–—]\s*(\d{4}))?`
  and only count `y1 < 2019 and not y2`.
- **`-webkit-marquee` in a Tilda `<style>` block is a CSS feature query, not a marquee.**
  `@supports (overflow:-webkit-marquee)` appears on every Tilda menu; matching
  `marquee` raw flags dozens of modern sites. Match `<marquee` as a tag, and treat
  `data-marquee-speed` (Tilda ticker block) as a design choice, not legacy.
- **The viewport regex `name=["']viewport` misses reversed attributes.**
  `<meta content='...' name='viewport'>` (Tilda, some builders) inverts the order; that
  regex reported 25 of 105 sites as "no viewport" and nearly every one was false.
  Confirm with a second HTTP pass on any "no viewport" verdict — measure, don't grep.

## 6. Scoring and the deliverable

Weight the findings so the ranking means something: a broken phone layout (6) and a
desktop-locked viewport (5) outrank any library age (1–2); dead site is its own sheet.
Each row carries `балл, хост, название, город, рейтинг, отзывов, телефон, сайт, что не
так` — the "что не так" cell is a semicolon list of concrete facts with numbers, not
adjectives.

Sheets: (1) ranking of live sites with reasons, (2) dead/broken with what happened,
(3) shortlist "crusty site + live business" for an outreach campaign. Screenshots of
the worst 3–5 (mobile frame at 375 px plus desktop) are worth more in the reply than
the whole ranking — attach as `MEDIA:` after downscaling to ~760 px wide (full-page
2 MB PNGs are unusable).

### Outreach file: join contacts back onto the ranking

A ranking of hosts is not callable — nobody phones a domain. Build the campaign sheet
from the **source base rows** (they carry address, phone 1–2, email, TG/WA/VK, rating,
reviews, 2GIS link) matched by host, keeping the row with the most reviews when a host
has several branches. Only own-domain hosts in *this* list: a booking-aggregator page gives the
seller no site to replace, so it never appears in the **replace-the-site** call list even
when it scores. It belongs to the other campaign — «своего сайта нет, ваших работ не
видно» — with its own hook and its own sheet (§9). The commercial reading flips there: an
org already on DIKIDI/YCLIENTS pays a vendor monthly, so willingness to spend is proven —
warmer lead for that offer, not colder for this one.

Priority is a blend, not the crustiness score alone — a perfect score on a 4-review
studio is worth less than 6/10 on a 700-review network:

| Tier | Rule | Offer |
|---|---|---|
| A | score ≥ 5 AND ≥ 100 reviews | «сайт разваливается» — call first |
| B | score ≥ 5 AND < 100 reviews | same pitch, second wave |
| C | score < 5 AND ≥ 200 reviews | «апгрейд / скорость / запись в один тап», not "rescuer" |
| D | the rest | reserve |

Sort by `score + min(8, reviews/60) + (2 if rating ≥ 4.5)`. Give every row a phone and
messenger link; a row with neither is dead weight in a call list — flag it rather than
letting it rank high.

## 7. Deliver only measured claims in the chat reply

Before sending the verdict, re-verify the one or two hosts you are about to name first
in prose (re-navigate them with a fresh emulation setup) — a headline claim built on a
flaky measurement is the worst possible outcome of this task, and the user will act on
it. If a re-measure contradicts an earlier number, say so plainly in the reply and
correct the file; do not silently re-rank.

## 9. Selection sheet: orgs with no own site

The cheapest campaign in the whole base: rows where the `Веб-сайт` cell is empty or holds a
vendor page. Classify every row into three buckets — `own` (audit it, §4–6), `agg` (vendor
page / link-in-bio / messenger), `none` (cell empty) — and deliver `agg + none` as one
selection with a `что вместо сайта` column naming the actual service (DIKIDI, YCLIENTS,
Taplink, only-Telegram…). On a 1531-row beauty base: 999 empty + 400 vendor pages = 1399
rows without an own site against 132 with one. Verify before promising the count that
blank cell ≠ no site: the owner may have built one and never linked it from the catalog.

Rows have **no host**, so dedup switches from host to **phone**: strip to the last 10 digits,
group, keep the record with the most reviews, count the rest as `филиалов`. Without it a
6-branch network becomes six calls to one owner.

Two traps in this export, both costing a rework:

- **The phone cell carries prose** — `89994236581 (кабинет маникюра)`,
  `83952989817 (единый номер: пн-вс 9:00-21:00)`. Stripping all non-digits swallows the
  digits of the note and yields a 15-digit number. Match the first phone-shaped token
  (`re.search(r'\+?\d[\d\s\-()]{8,16}\d', s)`), normalize to `+7XXXXXXXXXX`, and move
  `s[:m.start()] + s[m.end():]` into a separate `Примечание` column. A call list whose phone
  column is not dialable is not a call list.
- **The 2GIS column's value is literally `открыть`** — the URL is in the cell hyperlink
  (`row[21].hyperlink.target`), present on roughly 60% of rows. Read the hyperlink, else fall
  back to `https://2gis.ru/<city>/search/<name>`. Copying `.value` ships a column of «открыть».

Priority inside the selection keys off **reviews, not rating** (reviews = how many people
actually reached the salon; 5.0 on 3 reviews is noise): ≥100 → A, 30–99 → B, 10–29 → C, no
reviews but a messenger → D, rest → E. Work list = rows with a phone and ≥10 reviews; add a
`ТОП-40` sheet so the first call session does not start with a filter.

## 10. Batches, not one long run

A single Browser session survives roughly 12–18 navigations before
`WebSocket connection closed` / `Failed to open a new tab`. Batch 12–15 hosts per
`browser_exec` call, persist each batch to its own JSON immediately, and use a new
`session` name for the next batch. Re-run `ensure_real_tab()` inside the retry.
Dedup input by *what has a successful measurement*, not by file existence — a batch
that died halfway still wrote its (empty) file and silently blocked the rest.
