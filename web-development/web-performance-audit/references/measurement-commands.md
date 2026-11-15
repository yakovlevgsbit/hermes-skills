# Measurement commands and the audit report structure

## 1. Browser measurement (one `browser_exec` call)

Navigate first, wait, then read the Performance API. Returns navigation timings,
transfer size grouped by extension, and the biggest offenders — enough to name
the cause in one shot.

```javascript
(() => {
  const t = performance.getEntriesByType('navigation')[0] || {};
  const res = performance.getEntriesByType('resource');
  const byType = {};
  let totalBytes = 0;
  const big = [];
  res.forEach(r => {
    const size = r.transferSize || 0;
    totalBytes += size;
    const ext = (r.name.split('?')[0].match(/\.[a-z0-9]+$/i) || ['other'])[0].toLowerCase();
    if (!byType[ext]) byType[ext] = {count: 0, bytes: 0};
    byType[ext].count++; byType[ext].bytes += size;
    if (size > 100000) big.push({url: r.name.slice(-70), kb: Math.round(size/1024), dur: Math.round(r.duration)});
  });
  return JSON.stringify({
    ttfb: Math.round(t.responseStart || 0),
    domContentLoaded: Math.round(t.domContentLoadedEventEnd || 0),
    loadEvent: Math.round(t.loadEventEnd || 0),
    transferKB: Math.round(totalBytes/1024),
    resourceCount: res.length,
    byType: Object.fromEntries(Object.entries(byType).map(([k,v]) => [k, {count: v.count, kb: Math.round(v.bytes/1024)}])),
    biggest: big.sort((a,b) => b.kb - a.kb).slice(0, 15)
  }, null, 1);
})()
```

Read the result as: is one extension bucket dominating `byType`? That bucket is
the answer. Then look at `biggest` for the individual files to name in the report.

## 2. Server probes (`curl`)

```bash
URL=https://example.com/

# TTFB + transfer size + compression on the HTML
curl -sS -o /dev/null -D - "$URL" -H "User-Agent: Mozilla/5.0" --compressed \
  -w ">>> TTFB: %{time_starttransfer}s | TOTAL: %{time_total}s | SIZE: %{size_download}\n"

# HTTP version (h2 vs 1.1)
curl -sS -o /dev/null -w "HTTP version: %{http_version}\n" "$URL" -H "User-Agent: Mozilla/5.0"

# Cache headers on a static asset
curl -sSI "$URL/image/banner.png" -H "User-Agent: Mozilla/5.0" \
  | grep -iE "cache-control|expires|etag|content-length"

# Real weight of one image, with compression negotiated
curl -sS -o /dev/null -D - "$URL/image/banner.png" \
  -H "Accept-Encoding: br,gzip" -w ">>> SIZE: %{size_download}\n" \
  | grep -iE "^(HTTP|content-type|content-length|content-encoding)|>>>"

# Uncompressed vs gzipped HTML — the real cost of a heavy page
curl -sS -o /dev/null "$URL" -H "Accept-Encoding: identity" -w "identity: %{size_download}\n"
curl -sS -o /dev/null "$URL" -H "Accept-Encoding: gzip"     -w "gzip:     %{size_download}\n"

# Count images and lazy attributes in the served HTML
curl -sS "$URL" -H "User-Agent: Mozilla/5.0" --compressed \
  | grep -oiE '<img' | wc -l
curl -sS "$URL" -H "User-Agent: Mozilla/5.0" --compressed \
  | grep -oiE 'loading="lazy"' | wc -l
```

Zero lazy attributes against dozens of images is the lazy-loading finding.

## 3. Finding the same image in two formats (the strongest argument)

```bash
curl -sS "$URL" -H "User-Agent: Mozilla/5.0" --compressed \
  | grep -oE 'src="[^"]*\.(png|jpg)"' | sed 's/src="//;s/"//'
```

Look for matching base names with different extensions and compare their
`content-length` from the probe above. Two identical-dimension banners at 2 500 KB
(PNG) and 573 KB (JPEG) is the sentence that sells the job.

## 4. Before/after КП structure

The audit is a client-facing document; generate it as a PDF (font registration
and layout rules in `freelance-order-response` → `references/proposal-pdf.md`).
Sections that work:

1. **Title block** — site URL, CMS, server, and **the method** («реальные замеры:
   Chrome Performance API, HTTP-заголовки, curl»). Naming the method is what
   separates the report from a guess.
2. **«Главное в двух строках»** — current seconds and megabytes, the dominant
   cause with its share, and the projected result.
3. **Before/after table** — one row per metric, columns: показатель / сейчас /
   норма / после работ. Colour the «сейчас» values red and «после» green so the
   gap is visible at a glance.
4. **Cause sections** — one heading per cause, each with its measured number and
   the mechanism. Rank by impact, biggest first.
5. **Plan table** — этап / что делаем / срок / цена, with a bold ИТОГО row.
   Keep each stage independently purchasable and say so («можно взять только
   Этап 1 и увидеть основной эффект сразу») — it lowers the entry barrier.
6. **Terms and guarantees** — backup before work, refund for a stage that showed
   no effect, 30-day fix window, what you need from the client (access, timing).
7. **Expected result** — the multiplier, and the honest note that the numbers
   are reproducible by the client through PageSpeed Insights.

Price the image-conversion stage as the largest single line — it is where the
bulk of the win is, and pricing it lowest makes the total look arbitrary.

## 5. Publishing the report for the client

A client-facing PDF goes to a durable public URL, not to a chat attachment only.
Route and deploy mechanics: `web-panel-on-existing-vps` → «Hosting client-facing
documents». Verify with `curl` that the URL returns `200` and
`content-type: application/pdf` before sending the link.
