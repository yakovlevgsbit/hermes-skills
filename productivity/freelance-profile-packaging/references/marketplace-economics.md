# Marketplace economics and channel selection

Which marketplace to invest in, what each costs the seller, and how to pick.

## Cost-of-contact per platform (verify before recommending)

| Model | Platforms | Economics |
|---|---|---|
| **Free listing + commission on earned** | Kwork (20/12/7.5% by turnover), Fiverr (20%), Upwork (10%) | Seller invests time, not capital. Best for a zero-review profile. |
| **Pay-per-response** | FL.ru (responses bought separately, ~5 free/day; PRO status from ~490 ₽/mo does NOT include responses) | Seller pays for every chance with no guarantee of an order. Fatal arithmetic for a zero-review profile: spend precedes income, and profiles without reviews rarely win paid slots. |
| **Pay-per-contact / subscription** | Workzilla, Профи.ру, Freelance.ru | Same trap as pay-per-response. |

**Rule:** on a zero-review profile with a stated income goal, never recommend a pay-per-response platform as the primary channel — the user pays before earning, and no track record means the paid slots rarely convert. Put it in the scanner as an information source only (market intel), and say so explicitly.

## Platform reachability (probe before promising monitoring)

Before claiming a platform can be auto-monitored, check it from the VPS:

```bash
curl -s -o /dev/null -w "%{http_code}\n" --max-time 8 -A "Mozilla/5.0" "<rss or search url>"
```

Observed behaviour:

| Platform | RSS / search from VPS | Verdict |
|---|---|---|
| FL.ru | 200 | RSS scannable |
| Kwork | 200 | scannable (project pages need the browser) |
| Habr Freelance | 410 | permanently closed |
| Weblancer | 403 (WAF) | not scrapable |
| Upwork | 403 RSS, 403 page, Cloudflare "Just a moment…" in headless Chromium | **not parseable; search manually in a browser** |

**Rule:** never write an RSS endpoint into the scanner without the probe passing, and never promise automatic monitoring of a platform whose probe returned 403. A 403 with a Cloudflare interstitial means manual search only — the responses themselves are still free, which is what makes the channel worth preparing a pack for.

## International channels

New capabilities (e-commerce, voice, international payments) unlock $-marketplaces where the same niche pays 3–5×. Two things are needed that the Russian-language pack does not cover:

1. **An English pack**: profile title + overview, skill tags, and a short proposal template ending in one specific question plus a live demo link (a review-less profile converts on proof-of-work, not claims).
2. **Manual search**: parsing is blocked (see above), so budget the user's time for browsing, and keep the proposal template tight — 3–5 sentences beats a wall of text.

Price orientation on the $-market for this niche: simple bot $50–150; n8n automation $80–200; payment/subscription bot $200–500; Supabase mini-app $150–400.

## Sequence for a stated income target

1. Start where responses are free and monitoring is automatic (Kwork-style marketplaces) — it is the only channel that can produce income without pre-spending.
2. Add the international channel manually once the Russian one produces the first reviews.
3. Treat pay-per-response platforms as market intelligence only until there is a track record to make paid slots convert.
