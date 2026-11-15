---
name: scrapling
description: Scrape sites with stealth browsing and Cloudflare bypass.
version: 1.1.0
author: FEUAZUR
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Web Scraping, Browser, Cloudflare, Stealth, Crawling, Spider]
    related_skills: [duckduckgo-search, domain-intel]
    homepage: https://github.com/D4Vinci/Scrapling
prerequisites:
  commands: [scrapling, python]
---

# Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) is a web scraping framework with anti-bot bypass, stealth browser automation, and a spider framework. It provides three fetching strategies (HTTP, dynamic JS, stealth/Cloudflare) and a full CLI.

**This skill is for educational and research purposes only.** Users must comply with local/international data scraping laws and respect website Terms of Service.

## When to Use

- Scraping static HTML pages (faster than browser tools)
- Scraping JS-rendered pages that need a real browser
- Bypassing Cloudflare Turnstile or bot detection
- Crawling multiple pages with a spider
- When the built-in `web_extract` tool does not return the data you need

## Installation

```bash
pip install "scrapling[all]"
scrapling install          # downloads Chromium (~150 MB); every browser fetcher needs it
```

`scrapling` alone is HTTP-only. `scrapling[fetchers]` adds the browser stack used
by `StealthyFetcher` — but **not** markdown output: `.md`/`.txt` need
`markdownify`, which only `[rag]`, `[ai]`, `[shell]` and `[all]` pull in. With
`[fetchers]` alone the CLI dies on `.md` with an ImportError, so write `.html` or
install `markdownify`. The MCP server ships in the same package — `scrapling-mcp`
(stdio) is the same entry point as `scrapling mcp`.

Minimal install (HTTP only, no browser):
```bash
pip install scrapling
```

With browser automation only:
```bash
pip install "scrapling[fetchers]"
scrapling install
```

## Quick Reference

| Approach | Class | Use When |
|----------|-------|----------|
| HTTP | `Fetcher` / `FetcherSession` | Static pages, APIs, fast bulk requests |
| Browser (JS + stealth) | `StealthyFetcher` / `StealthySession` / `AsyncStealthySession` | JS-rendered content **and** anti-bot sites |
| Remote CDP | `RemoteSession` / `AsyncRemoteSession` | Attach to a Chromium already running over CDP, reuse its login |
| Spider | `Spider` | Multi-page crawling with link following |

`DynamicFetcher` / `DynamicSession` were **removed in 0.5** — `StealthyFetcher`
absorbed the dynamic role and is now the only browser fetcher. Code written
against the old name dies with `ImportError: cannot import name 'DynamicFetcher'`.

## CLI Usage

### Extract Static Page

```bash
scrapling extract get 'https://example.com' output.md
```

With CSS selector and browser impersonation:

```bash
scrapling extract get 'https://example.com' output.md \
  --css-selector '.content' \
  --impersonate 'chrome'
```

### Extract a page with a real browser (JS and anti-bot in one)

Since 0.5 `extract fetch` runs `StealthyFetcher`. There is no `stealthy-fetch`
subcommand and no `DynamicFetcher`.

```bash
scrapling extract fetch 'https://example.com' output.md \
  --css-selector '.dynamic-content' \
  --network-idle \
  --solve-cloudflare          # only when the site actually challenges
```

Measured on this box: **~12 s** per JS page, **~13 s** with `solve_cloudflare`.
That is not a bulk path — see the pitfalls.

### POST Request

```bash
scrapling extract post 'https://example.com/api' output.json \
  --json '{"query": "search term"}'
```

### Output Formats

The output format is determined by the file extension:
- `.html` -- raw HTML
- `.md` -- converted to Markdown
- `.txt` -- plain text
- `.json` / `.jsonl` -- JSON

## Python: HTTP Scraping

### Single Request

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()
for q in quotes:
    print(q)
```

### Session (Persistent Cookies)

```python
from scrapling.fetchers import FetcherSession

with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://example.com/', stealthy_headers=True)
    links = page.css('a::attr(href)').getall()
    for link in links[:5]:
        sub = session.get(link)
        print(sub.css('h1::text').get())
```

### POST / PUT / DELETE

```python
page = Fetcher.post('https://api.example.com/data', json={"key": "value"})
page = Fetcher.put('https://api.example.com/item/1', data={"name": "updated"})
page = Fetcher.delete('https://api.example.com/item/1')
```

### With Proxy

```python
page = Fetcher.get('https://example.com', proxy='http://user:pass@proxy:8080')
```

## Python: Browser — JS-rendered and anti-bot (one class since 0.5)

`StealthyFetcher` renders JS **and** carries the stealth stack. There is no
`DynamicFetcher` any more, so every example that used it now goes through this
class.

```python
from scrapling.fetchers import StealthyFetcher, StealthySession

# JS-rendered page
page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
data = page.css('.js-loaded-content::text').getall()

# Wait for a specific element — a selector string plus a separate state
page = StealthyFetcher.fetch(
    'https://example.com',
    wait_selector='.results',
    wait_selector_state='visible',   # attached (default) | visible | hidden | detached
    network_idle=True,
    timeout=60000,                   # milliseconds, not seconds
)

# Cloudflare / anti-bot
page = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,
    block_webrtc=True,
    hide_canvas=True,
)
content = page.css('.protected-content::text').getall()
```

### Session — one browser, many pages, cookies carried

```python
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page1 = session.fetch('https://protected-site.com/page1')
    page2 = session.fetch('https://protected-site.com/page2')
```

### Drive the page yourself

`StealthyFetcher` still accepts a Playwright `page_action`, which is how you
scroll, click "load more", or wait for a lazy section:

```python
from playwright.sync_api import Page

def scroll_and_click(page: Page):
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(1000)
    page.click('button.load-more')
    page.wait_for_selector('.extra-results')

page = StealthyFetcher.fetch('https://example.com', page_action=scroll_and_click)
results = page.css('.extra-results .item::text').getall()
```

### Reuse a logged-in browser over CDP

```python
from scrapling.fetchers import RemoteSession

with RemoteSession(cdp_url='http://localhost:9222', new_context=False) as session:
    page = session.fetch('https://example.com')   # carries the browser's cookies
```

`new_context=False` reuses the default context and its login state; the default
`new_context=True` opens a throwaway context.

## Element Selection

All fetchers return a `Selector` object with these methods:

### CSS Selectors

```python
page.css('h1::text').get()              # First h1 text
page.css('a::attr(href)').getall()      # All link hrefs
page.css('.quote .text::text').getall() # Nested selection
```

### XPath

```python
page.xpath('//div[@class="content"]/text()').getall()
page.xpath('//a/@href').getall()
```

### Find Methods

```python
page.find_all('div', class_='quote')       # By tag + attribute
page.find_by_text('Read more', tag='a')    # By text content
page.find_by_regex(r'\$\d+\.\d{2}')       # By regex pattern
```

### Similar Elements

Find elements with similar structure (useful for product listings, etc.):

```python
first_product = page.css('.product')[0]
all_similar = first_product.find_similar()
```

### Adaptive — surviving a redesign (narrow; do not oversell it)

With `adaptive=True` on the `Selector`, `auto_save` the element on the old page,
then `adaptive=True` on the new one:

```python
page_old = Selector(html_v1, adaptive=True)
page_old.css('.price', auto_save=True)

page_new = Selector(html_v2, adaptive=True)
page_new.css('.price', adaptive=True)     # relocated by structural similarity
```

**Measured limit:** it relocates **one** element, because `save()` stores
`elements[0]`. On a 50-item list whose classes were renamed, plain `css` returned
0 and `adaptive=True` returned **1** — not 50. For a list, relocate the anchor,
then expand with `find_similar()` from it. "Never breaks when the site changes its
layout" is marketing: it is a hint, not a guarantee, and it fails by returning a
short list rather than an error.

### Navigation

```python
el = page.css('.target')[0]
el.parent                # Parent element
el.children              # Child elements
el.next_sibling          # Next sibling
el.prev_sibling          # Previous sibling
```

## Python: Spider Framework

For multi-page crawling with link following:

```python
from scrapling.spiders import Spider, Request, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10
    download_delay = 1

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
                "tags": quote.css('.tag::text').getall(),
            }

        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page)

result = QuotesSpider().start()
print(f"Scraped {len(result.items)} quotes")
result.items.to_json("quotes.json")
```

### Multi-Session Spider

Route requests to different fetcher types:

```python
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class SmartSpider(Spider):
    name = "smart"
    start_urls = ["https://example.com/"]

    def configure_sessions(self, manager):
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css('a::attr(href)').getall():
            if "protected" in link:
                yield Request(link, sid="stealth")
            else:
                yield Request(link, sid="fast", callback=self.parse)
```

### Pause/Resume Crawling

```python
spider = QuotesSpider(crawldir="./crawl_checkpoint")
spider.start()  # Ctrl+C to pause, re-run to resume from checkpoint
```

## Pitfalls

- **Speed claims are about parsing, not networking.** Measured here: parsing is 13x faster than BS4 on 85 KB and 8.5x on 344 KB; but `FetcherSession` warm equals `requests` (~110 ms each), and a headless browser page costs ~12 s. "800x faster" is one micro-benchmark, not your pipeline.
- **Browser fetches are seconds per page.** ~12 s for a JS page, ~13 s with `solve_cloudflare` — 500 pages is ~1.7 hours. Reach for the browser only where the page truly needs it.
- **`DynamicFetcher` / `DynamicSession` no longer exist** (removed in 0.5). Use `StealthyFetcher` / `StealthySession`; the CLI subcommand `stealthy-fetch` is gone too, `extract fetch` now runs the stealth fetcher.
- **Markdown output needs `markdownify`.** `pip install "scrapling[fetchers]"` gives you browsers but not the `.md`/`.txt` converter; `scrapling extract ... output.md` fails on import. Use `.html`, or install the `[ai]`/`[all]` extra (which is what the tutorials' two-line install actually does).
- **`wait_selector` is a plain string; the state is a separate argument.** `wait_selector='.results', wait_selector_state='visible'`. Passing a tuple `('.results', 'visible')` — the shape older docs used — dies with `TypeError: Expected str, got array`.
- **`adaptive` returns one element per saved selector** — see the Adaptive section before promising a redesign-proof scraper.

- **Browser install required**: run `scrapling install` after pip install -- without it, `StealthyFetcher` and its sessions fail
- **Timeouts**: `StealthyFetcher` timeout is in **milliseconds** (default 30000), `Fetcher` timeout is in **seconds**
- **Cloudflare bypass**: `solve_cloudflare=True` adds 5-15 seconds to fetch time -- only enable when needed
- **Resource usage**: StealthyFetcher runs a real browser -- limit concurrent usage
- **Legal**: always check robots.txt and website ToS before scraping. This library is for educational and research purposes
- **Python version**: requires Python 3.10+
