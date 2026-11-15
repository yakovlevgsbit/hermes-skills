# Social Publishing API Viability

Which platforms still allow programmatic posting, and what to do when one does not. Scope this BEFORE writing code for a multi-account panel, arbitrage tool or autopost bot — the platforms closed their write APIs through 2025–2026 and the closure is invisible in the docs. A quote or a build promised on a dead API is the most expensive mistake in this class.

## Check order

1. **Does the platform ISSUE a token carrying the scope the write needs?** Not "does the API have the method" — the method being documented means nothing if no token type carries the scope. This is the step people skip.
2. **Is a business / verified profile required?** Several platforms now gate API access behind passport-level verification.
3. **What is the monthly call cap without verification?**
4. **Only then** estimate the build.

## Reality table

Verify each against a live call before quoting — this moves fast.

| Platform | Programmatic video post | Notes |
|---|---|---|
| Telegram | ✅ yes | Bot API, free, no review. Bot must be a member/admin of the destination channel. 50 MB video cap — see below. |
| YouTube | ✅ yes | Data API v3 + OAuth. Quota units, roughly 10 uploads/day/account. |
| VK | ❌ video / ✅ text to a community wall | Video write API is closed, but a **community token CAN `wall.post`** with no OAuth and no business verification — see below. |
| Instagram | ⚠️ gated | Business/Creator account + App Review. Long-lived tokens ~60 days; refresh every ~50. |
| Threads | ✅ yes | OAuth only — **no Business/Creator, no linked Facebook Page**. 250 posts / 1000 replies per 24h per profile. See below. |
| TikTok | ⚠️ gated | Content Posting API, Business account, audit 1–2 weeks, ~6 req/min. |
| X/Twitter | ⚠️ metered | Per-post pricing. |
| Reddit | ⚠️ metered | Per-call pricing for commercial use. |

**TikTok's silent-draft trap:** its daily active cap can make the API return `success: true` while the post lands as a draft in the TikTok inbox. Read the `fallback_to_inbox` flag rather than trusting the status code.

## Telegram: the open case

Telegram is the cheapest transport in this class and the one to build first: a bot
token costs nothing, needs no review, and posts to any channel the bot is a member
of. It is also the right first target when a paid platform's onboarding is stuck —
it proves the whole publish path end to end (panel button AND scheduler worker)
while that argument is still unresolved.

- **The destination is a chat, not a credential.** Model it as the account's
destination field (`@channel` when the channel is public, the numeric `-100…` id
when it is private) — one row per destination.
- **50 MB video cap** on `sendVideo`; a larger file needs `sendDocument` (no inline
playback) or a transcode down. Caption ≤1024 chars, text ≤4096.
- **Find a channel's numeric id when it has no public `@username`** by reading what
the bot has already seen: `getUpdates?offset=-50` lists the chats it received
anything from. A long-polling consumer that has already acked those updates leaves
nothing to harvest, so read the id before the poller starts or have the bot print it.
- **Probe capability in three calls before writing any publish code**, in order:
`getMe` (token alive) → `getChat` (destination reachable, and its type) →
`getChatMember` with the bot's own user id (is it an admin, does it carry
`can_post_messages`?). A token that authenticates proves nothing about whether the
destination will accept a post — the same rule as the aggregator's accounts object.
- **Prove it with a real post, then clean up.** Publish one test video, read the
returned `message_id` back, run one past-dated scheduler task to prove the worker
path too, then `deleteMessage` each id and confirm the channel is clean.
- **A token pasted into a chat is compromised.** Have the user `/revoke` it in
BotFather, store the replacement in the secrets dir, and never re-echo it.

## Threads: the gated platform that is not actually gated

Threads runs on Meta's graph but does **not** inherit Instagram's prerequisites:
no Business/Creator account and no linked Facebook Page are required — its OAuth
runs in its own window and links straight to the Threads profile. When Instagram is
stuck on the account-type prerequisite (or on Meta developer verification), Threads
reaches a comparable audience without that fight, so scope it as its own target
rather than as an Instagram add-on.

- Quota is generous: **250 posts / 1000 replies / 100 deletions per 24 hours** per
  profile — an order of magnitude more headroom than Instagram's 25.
- Text 500 chars (up to 5 links); video MP4/MOV, H.264 or HEVC, AAC ≤48 kHz,
  23–60 fps, ≤5 min, ≤1 GB.
- The aggregator's caption field is `threads_title` (falls back to `title`).
- A direct integration still needs App Review per `threads_*` scope plus Tech
  Provider Verification (~a week) — the same reason to proxy it, not to skip it.

## Minting a connect URL from your own panel

The aggregator can hand your backend an OAuth authorize URL, so the operator
connects an account from inside your panel instead of being sent to the
aggregator's dashboard:

```
POST /api/uploadposts/oauth/{platform}/start   {"profile": "<profile>"}
→ {"authorize_url": "...", "state": "...", "expires_in": 900}
```

Expose it as your own route (`GET /api/uploadpost/connect/{network}`) and have the
UI open the returned URL. Facts that matter:

- The URL is **single-use and short-lived** (~15 min). Mint one per attempt and
  never cache it in the UI — a stale link reads to the user as a broken connect
  button.
- Works for the OAuth platforms (`instagram`, `threads`, `tiktok`, `facebook`,
  `linkedin`, `youtube`, `pinterest`, `x`, `google-business`, `snapchat`).
  Manual-credential platforms are **not** in this flow — Discord/Slack take a
  webhook, Telegram a bot token + chat, Mastodon an instance token, Nostr a
  private key — so do not render the button for them; the API answers
  `Unknown platform '<x>'`.
- Reddit's OAuth answers `503 reddit_unavailable`.

**Trap: the aggregator client's request helper may pass `data` straight to
`urllib.request.Request`, which requires `bytes`.** Posting a `str` JSON body
fails inside the handler with `TypeError: POST data should be bytes` — a 500 that
reads like a bug in your new route. Encode once (`.encode()`) at the call site;
the helper's existing multipart callers keep working while only the new JSON route
breaks, so the traceback points at your code and not at the helper.

## VK: closed for video, open for a community wall post

Do not read "VK's API is closed" as "nothing on VK works". Split it by target:

| Target | Status |
|---|---|
| Video upload (`video.save`) | ❌ closed — needs the `video` scope, which VK ID does not issue |
| **Text post to a community wall** | ✅ **works** via a community token, no OAuth, no business verification |
| Photo attached to that post | ⚠️ needs a second (user) token — see below |
| Reading / deleting / editing wall posts | ❌ a community token answers error 27 for all of them |

- VK moved to **VK ID** (`id.vk.ru`). Old standalone apps and the `oauth.vk.com` authorization-code flow are gone for new apps; the developer cabinet offers no "website" app type.
- **VK ID scopes are login-only:** `vkid.personal_info`, `email`, `phone`. No `video`, `wall`, `photos`.
- **Business verification** (VK Бизнес ID, passport / Госуслуги) governs the *call cap* — ~10 000/month without it, 100M with — but it is **not** required for community-token wall posting.
- **Third-party token workarounds are dead** (Kate Mobile, VK Admin).

### The community token is the cheap, verified path

The operator copies it out of the community itself — *Управление → Настройки → Работа с API → Создать ключ* — and the panel needs **no OAuth route at all**. This was verified end to end with a real post appearing on a real community wall. Build it first; it is the cheapest transport on VK and proves the whole publish path while the photo argument is still open.

Granted scopes (`groups.getTokenPermissions` reports them) look generous — `photos, wall, manage, messages, docs` — but **the mask lies about what is callable**: `wall.post` succeeds while `wall.get`, `wall.getById`, `wall.delete`, `wall.edit` and `photos.getWallUploadServer` all answer error 27 ("method is unavailable with group auth"). So a community-token panel can publish but cannot verify, delete or attach media. Tell the user that before building a delete feature.

### The app-classification ladder (read the error, not the docs)

When a VK authorize URL fails, the JSON `error_description` names the **app's class or state**, not a bug in your code. Probe the authorize endpoint directly and read it:

| `error_description` | Meaning |
|---|---|
| `application is disabled` | The app is not usable for this flow — typically a **Mini App**, which can never mint an API token. Recreate it as **Standalone**. |
| `invalid scope` | That app is not permitted the requested scope (e.g. `offline`) — a per-app grant, not a syntax error. |
| `application was deleted` | Wrong/stale client_id. |
| *(a login page, HTTP 200)* | The app is live and the flow is available. |

Probe **one scope per request with a pause** — a burst of authorize calls gets rate-limited and returns a bot wall that reads as a different failure. Comparing a suspect app against a known-live public app id in the same probe separates "this app is broken" from "the endpoint is broken".

Also: a Mini App's own page answers *"Unable to open mini app — only accessible to its administrators"* when fetched unauthenticated, which is a second, independent confirmation of the app class.

### The user token for photos: check two things before promising it

A community token cannot upload photos, so the photo path needs a **user token** with scope `photos`. Before promising it works, verify both of these, because either one sinks a server-side publisher:

1. **Does the app accept `offline`?** Probe `scope=offline` on the authorize URL. Without it the token expires in ~a day and must be refreshed by hand.
2. **Is the token IP-bound?** Implicit-flow user tokens are issued against the IP that requested them, so a token minted on the operator's home machine is rejected by a VPS publisher (`invalid access_token`). The IP-independent alternative is the Authorization Code Flow, which for API scopes requires the extended provider verification (ИП / самозанятость / юрлицо) that a private individual cannot pass.

State plainly that the photo path is **unverified until a real post lands** — do not present the flow as a working recipe on the strength of the calls succeeding.

## Reposting is not a way around it

`wall.repost` does work with a community token — community tokens *can* write to a wall even though the docs say otherwise, so confirm with a live call rather than reading. That makes "upload once, repost everywhere" look attractive. It fails the actual goal:

- VK's algorithm demotes reposts — reposts without added value get almost no reach.
- Clips enter recommendations only as **originals**. The clip cascade is 200–500 cold-start impressions → 10 000+ if retention clears the threshold; a repost never enters the cascade.
- The same video across many accounts is duplicate content and is demoted too.

So the goal (recommendations) needs an **original clip per account**, which needs a real upload, which the API does not allow. Reposting saves delivery and kills the objective.

## Fallback ladder when the API is closed

1. **A paid aggregator proxying the official OAuth APIs** — cheapest, least risky, and often already configured. Check the secrets dir and the project KB for an existing account/key before building anything.

   **Read its account model before you promise a multi-account panel.** These services are built for "one brand, one account per platform": each *profile* connects exactly **one** Instagram, one TikTok, one YouTube, and profiles are the billed unit (a free tier is typically ~2 profiles). So the aggregator solves a single-operator autopost (and is the only realistic route to Instagram without a Meta developer app, Business verification and App Review) but it does **not** serve a panel whose whole premise is N accounts per network — that needs N profiles, which is the aggregator's per-profile pricing, not one key. Establish this in the scoping round: ask how many accounts per network, and if the answer is "many", the aggregator is the demo/first-client path, not the architecture.

   **Upload-Post pricing tiers (verify live — they change):**

   | Tier | Price/mo | Profiles | Uploads | TikTok | Whitelabel |
   |------|----------|----------|---------|--------|------------|
   | Free | $0 | 2 | 10/mo | ❌ | ❌ |
   | Basic | $24 ($16 annual) | 5 | Unlimited (daily caps apply) | ✅ | ❌ |
   | Professional | $50 ($33 annual) | 25 | Unlimited | ✅ | ✅ |
   | Advanced | $147 ($118 annual) | 75 | Unlimited | ✅ | ✅ |
   | Business | $438 ($350 annual) | 225 | Unlimited | ✅ | ✅ |

   **"Unlimited uploads" means no monthly ceiling — daily platform caps still apply.** Verified 2026-10-18: all platforms get the same **50 posts/day per profile** (Instagram, TikTok, YouTube, Threads, Facebook all returned `quota_total: 50`). These are platform limits, not Upload-Post limits.

   **Free tier is 10 uploads per MONTH, not per day.** One test video eats 10% of the monthly quota. Verify current usage: `GET /api/uploadposts/instagram/publishing_limit?user=<profile>&platform=<platform>&refresh=true` → `quota_usage`, `quota_total`, `remaining`, `limit_reached`. The quota endpoint works for all platforms by substituting the path segment.

   **For a 1-client-1-network model:** Basic at $24/mo ÷ 5 profiles = $4.80/client/month. At 50 posts/day per platform per profile, the quota is never the bottleneck — the profile count is.

   **Quotas are per-platform, not shared.** A post to Instagram does not consume TikTok's quota. Each platform has its own independent counter at the same profile. This matters for cost estimation: a client posting to 3 networks gets 50×3 = 150 posts/day on one Basic profile, not 50 total.

   **Query the aggregator's connection status before writing any publish code.** Its accounts object is the ground truth for what will actually post: a platform whose value is an **empty string** is not linked, a platform **absent entirely** was never connected, and a platform object carries `reauth_required` when the token has lapsed. A key that authenticates fine proves nothing about whether anything is connected — an upload to an unlinked platform is the failure you find at the end of the build instead of the start.

   **An onboarding checklist's "connected an account" badge is a false positive — never read it as evidence.** The dashboard marks that step Done the moment ANY platform is linked, so a YouTube connection made days earlier satisfies it while the Instagram just attempted never arrived. The user sees "2/3 steps completed" and reasonably reports success. Only the accounts object settles it: a platform missing from that object was not connected, whatever the progress bar says. Say so plainly rather than asking the user to redo a flow they believe already worked.

   **On these services the platform's own account-type prerequisite fails silently.** Instagram publishes only from a **Business or Creator** account, and Meta declines to issue a token for a Personal one — the connect popup can close, the dashboard can look unchanged, and nothing appears in the accounts object with no error to show. Before debugging the integration, have the user confirm the account type (Instagram: the profile shows "Professional dashboard"; otherwise Settings → Account type → switch to Professional — free, and visually identical). A prerequisite the provider enforces is not an integration bug.

   **When you do integrate one, keep it in its own module beside the direct-API path.** A direct provider call (Google/YouTube) and an aggregator call fail differently — one returns the provider's error, the other the aggregator's — so separate the modules (`publish.py` direct, `uploadpost.py` aggregator) rather than branching inside one. Send the platform-specific caption field the aggregator documents (`instagram_title`, `tiktok_title`) since it overrides the generic one, and send an idempotency key derived from the local row id + file mtime so a retry after a timeout cannot double-post.
2. **Browser automation** (antidetect browser + Playwright over CDP) — the only route for a platform with no write API. Antidetect browsers are Windows/macOS, so an always-on Windows host is required; a headless Linux VPS cannot run one. Cost is roughly $10–89/mo by profile count plus residential proxies ~$1.5–5/IP/mo — about $300–600/mo at 100 accounts, before earning anything.
3. **Manual** — the panel prepares content and metadata, the operator uploads. Zero risk, and the honest answer when the budget does not cover option 2.

**Never present browser automation as a validated, reliable workflow.** It is an arms race: automation is detected by behaviour (perfectly even intervals, no mouse movement) as much as by fingerprint, so randomised delays and human-like patterns are mandatory, and it breaks whenever either side updates. It is against platform ToS — ban is a matter of time, not probability. Say so instead of selling a guarantee.

## One publish router, not N branches at the call sites

Once two transports exist (a direct provider API and an aggregator), every caller — the "publish now" endpoint AND the scheduler worker — must go through ONE dispatcher that reads the account's network and picks the transport, instead of each caller branching on the network itself. Signature like `publish(account_id, video_id, privacy=None)`, returning a normalised dict (`network`, `url`, `youtube_id`, `privacy`) and raising one error type. Two payoffs: adding a network is a single entry in the map with no caller changes, and the panel and the worker can never drift into different behaviour for the same account. A direct Bot-API transport slots in exactly like a provider API — adding Telegram to the map gave both the panel button and the scheduled worker the capability with no caller edit. The transport modules stay separate underneath (direct vs aggregator); the router is the thin layer above them.

Normalise the return across transports too — an aggregator answers with a `request_id`/`job_id` and no permanent URL, so store that as the handle and build a pseudo-URL from it rather than pretending a link exists. A caller that assumes `youtube_id` is always present breaks on the first Instagram post.

**The router owns file resolution, and a derived artifact is a second file with
its own lifecycle.** When a pipeline bakes a derivative (an outro/intro glued on,
a transcode, a watermark) and stores it beside the source, the router resolves in
one fixed order — `derived → source → original filename` — implemented once and
shared by every transport. Wire all three ends or the derivative leaks or lies:

- **A transport that still reads the source publishes the video WITHOUT the
derivative while the API answers success** — the silent failure the whole pattern
exists to prevent, and the reason the order must live in the router and not in each
transport.
- **Every delete path must delete the derivative.** Removing the source row and
  removing the derivative's own record each orphan a file on disk; deleting the
derivative record must additionally clear the reference on every row that used it,
  or the next publish dies on a missing file instead of falling back to the source.
- **Deleting the current default of a referenced artifact must promote another**,
  or the "use the default" branch finds nothing and the feature quietly stops
  working after one deletion.
- **Distinguish "not found" from "none configured" in the error text.** A wrong id
  answered with "nothing uploaded yet" sends the operator to re-create something
  that already exists.
- **Bake once, at apply time — never inside the scheduler.** Re-encoding on every
  publish makes the worker slow and turns a transient encoder failure into a missed
  post. Store the derivative and let publishing just pick it.

## Architecture note for a multi-network panel

Give each account a `delivery_mode` (`api` | `proxy-service` | `browser` | `manual`) plus the provider-specific handle (antidetect profile id, aggregator connection id). The scheduler enqueues per mode; a browser-mode task goes to an external worker, not the panel process. This keeps one dead-API platform from blocking the whole build.
