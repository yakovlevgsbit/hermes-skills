---
name: web-performance-audit
description: "Use when a site loads slowly or needs a speed audit."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [performance, speed, audit, ttfb, lazy-loading, images, webp, nginx, http2, caching, pagespeed, kp]
    related_skills: [web-design-check, freelance-order-response, web-panel-on-existing-vps]
---

# Web Performance Audit

Measure why a live page loads slowly, rank the causes by real impact, and turn
the result into a client-facing report with a «до/после» table. Load when a
client says «сайт долго грузится», when the order is an audit/optimization, or
when you need to price a speed job without guessing.

This is **measurement, not taste**: every finding carries a number read off the
live site. It is a different class from `web-design-check` (contrast, tap
targets, a11y) — do not run one and call it the other.

## When to Use

- A client reports slow loading, or asks for a speed/PageSpeed audit.
- You are pricing an optimization job and must know what is actually wrong.
- You inherited a site (new client, takeover) and need a baseline before edits.
- You only have a screenshot and must first find which site it is (see below).

Don't use for: visual/a11y defects (`web-design-check`), functional bugs
(`dogfood`), or backend/database tuning on an API with no page in front.

## Procedure

1. **Identify the target.** If the user gave a URL, go. If they gave only a
   screenshot, see «Identifying a site from a screenshot».
2. **Measure in the browser first** — one `browser_exec` call that returns
   navigation timings, per-resource transfer sizes grouped by extension, and the
   biggest offenders. Exact snippet in `references/measurement-commands.md`.
   This single call usually names the culprit.
3. **Probe the server with `curl`** — TTFB, `Content-Encoding`, `Cache-Control`,
   `HTTP version`, compression on CSS/JS. These are the facts the browser cannot
   show you.
4. **Rank causes by bytes and seconds**, not by how interesting they are. The
   heaviest resource group is almost always the answer; the exotic one rarely is.
5. **Prove each cause with a number** from steps 2–3, and with a comparison
   inside the client's own site when one exists (see the strongest argument).
6. **Write the report as a before/after table** plus a per-stage price. Structure
   in `references/measurement-commands.md`.
7. **Re-measure after the work** with the same commands and publish the real
   numbers — the «до/после» table is the deliverable the client pays for.

## Calibration: what the numbers should be

Use these as the bar when writing findings. They are ordinary targets for a
content/catalog page, not best-in-class records.

| Metric | Target | Alarm |
|---|---|---|
| TTFB | < 0.2 s | > 0.5 s |
| DOM ready | < 1.0 s | > 2 s |
| Load event | < 2.5 s | > 4 s |
| Total page weight | < 2 MB | > 5 MB |
| Requests | < 50 | > 100 |
| Largest single asset | < 300 KB | > 1 MB |

## The causes, ranked by how often they are the answer

1. **Photographs served as PNG.** The single most common and most expensive
   defect. PNG is lossless and meant for logos/icons with transparency; a photo
   or render in PNG is typically 3–6× the weight of the same image as JPEG/WebP.
   Detect by grouping transfer size by extension — a fat `.png` bucket next to a
   small `.jpg` bucket is the diagnosis. Fix: convert photos to WebP with a JPEG
   fallback, keep PNG only where transparency is needed, and automate conversion
   at upload so it does not regress.
2. **No lazy loading.** Every `<img>` loads immediately, including those far
   below the fold. Count `loading="lazy"` occurrences against total `<img>`
   count; zero out of dozens is the tell.
3. **No `Cache-Control` on static assets.** Only `ETag` present means the browser
   revalidates on every navigation. Fix in nginx: `expires 30d;` for images, CSS,
   JS.
4. **HTTP/1.1 instead of HTTP/2.** At 100+ requests HTTP/1.1 serializes into ~6
   connections per host. Check with `curl -w '%{http_version}'`.
5. **Oversized HTML.** A megabyte of HTML (before compression) usually means
   inline styles/scripts. Compare gzipped vs identity size to see the real cost.
6. **Slow backend.** High TTFB with a light page means the app rebuilds the page
   per request — CMS page cache is the fix, not frontend work.

## The strongest argument you can make

When the client's own site contains the **same image in two formats**, put the
side-by-side weight in the report. It converts an abstract claim («PNG is
heavy») into their own number: e.g. a banner at 2 500 KB as PNG and 573 KB as
JPEG at identical pixel dimensions — «в 4 раза легче при том же качестве».
Search the resource list for matching base names with different extensions.

## Identifying a site from a screenshot

When the user sends a screenshot and asks for the site, do **not** reach for
reverse image search first — a screenshot of a mobile page usually returns junk.
Instead, read the unique on-page strings and search them verbatim.

1. `vision_analyze` the image and transcribe **every** readable string: section
   headings, tab labels, button text, footer lines, the cookie banner.
2. Search the most unusual combination — two or three rare phrases together in
   one query. Generic headings («Продукция») match thousands of sites; the
   cookie-banner wording, an odd tab order, or a niche product phrase is
   near-unique.
3. Confirm by loading the candidate and asserting the strings are present
   verbatim (`'<phrase>' in document.body.innerText`). Three or four independent
   matches, including one rare phrase, is proof.
4. Say plainly which method you used and that the match rests on the text, not
   on the image. If nothing matches, then fall back to reverse image search.

## Pitfalls

- **Do not report «медленно» without numbers.** The client cannot argue with
  «20.4 МБ и 5.6 с», and cannot act on an adjective.
- **Do not optimise what you did not measure.** Guessing at causes produces a
  plan that does not move the metric.
- **Do not confuse transfer size with decoded size.** `transferSize` is what the
  network carried; an already-cached or compressed asset reads near zero. Take
  the measurement on a cold load or with cache disabled.
- **Do not treat `no-store` on an HTML page as a static-asset problem.** HTML and
  hashed assets want opposite cache policies; check them separately.
- **Do not promise a rank or a conversion lift.** Speed is one ranking input;
  promise the seconds and the megabytes, which you can measure.
- **A local `file://` load has no TTFB and no HTTP headers** — performance work
  is only meaningful against the live origin.

## Verification

- Every finding in the report traces to a specific command output from this
  session (browser timing, curl header, resource size).
- The before/after table lists the same metrics on both sides.
- The report states what was **not** checked.
- If work was performed: re-measure with the identical commands and publish the
  real numbers, not the projection.

## Support files

- `references/measurement-commands.md` — the exact browser Performance-API
  snippet, the `curl` header probes, and the before/after КП structure.
