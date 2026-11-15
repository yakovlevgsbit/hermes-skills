---
name: telegram-bot-payments
description: "Use when a Telegram/MAX bot order needs payments."
version: 1.0.0
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [telegram, bot, payments, subscriptions, cloudpayments, yookassa, robokassa, эквайринг]
---

# Telegram Bot + Payments (RU)

Add payment acceptance to a Telegram/MAX bot: one-off payments and recurring
subscriptions with automatic grant/revoke of access. Load when an order involves
paid access, subscriptions, or "take money in the bot".

## Provider choice (RU market)

| Provider | Use when | Notes |
|---|---|---|
| **CloudPayments** | subscriptions, recurring, no redirect | Widget, `api.cloudpayments.ru`, card token in Pay notification, plan amount editable anytime. Best for paid-signal channels. |
| **YooKassa** | universal, one-off + recurring, 54-ФЗ receipts | Good docs, Python SDK, status webhooks. Safe default. |
| **Robokassa** | also covers Telegram/MAX/VK natively | Good fallback. |
| **Telegram Stars** | built-in, XTR currency, no provider_token | Bot must have Stars enabled in BotFather; new bots often don't. Gate the menu on a runtime check (`getMyStarBalance`), don't hardcode. |
| **CryptoBot / Crypto Pay** | crypto (USDT/TON/BTC), no ИП, no BotFather | Endpoint `pay.crypt.bot/api/` (NOT `api.telegram.org/bot...`), auth via `Crypto-Pay-API-Token` header. |
| **Lava.top** | RU market, recurring subscriptions only, no ИП required for sales | `POST /api/v3/invoice` with `periodicity=MONTHLY`. Auth via `X-Api-Key` header. Webhook auth uses the same key. See `references/lava-top.md`. |

Don't build on two providers at once for the same flow. Pick by the order's shape.

## Multi-provider setup pattern

When the bot must support several payment methods that each may or may not be configured:

1. Each provider's availability is gated by a single env var (e.g. `CRYPTOBOT_TOKEN`, `LAVA_API_KEY`, `UKASSA_PROVIDER_TOKEN`).
2. The `/topup` keyboard is built dynamically — only buttons for configured providers appear.
3. Startup hook (`post_init` in python-telegram-bot) probes runtime features (e.g. `getMyStarBalance`) and stores results in `bot_data`; menu code reads from there.
4. Each provider has its own pending-payment registry (`pending_lava`, `pending_crypto`) keyed by invoice/contract id, holding `{user_id, pkg, created_at}` so the webhook/auto-check can finish crediting.
5. One `successful_payment` table + one ledger — `payment_method` column distinguishes `stars` / `card` / `cryptobot` / `lava_sub`. Don't fork the database per provider.

## Core mechanics (provider-agnostic)

1. **Checkout**: bot sends a payment link → user pays.
2. **Webhook** (`payment.succeeded` / `waiting_for_capture` / `recurrent` /
   `canceled`): provider POSTs to your endpoint. **Verify the request** —
   HTTP Basic or signature; never trust the body alone.
3. **Idempotency**: key every create-payment call; webhooks can fire twice.
4. **Grant access only after a verified webhook** — never on the user's
   "I paid" message.
5. **Recurring**: first payment stores a card **token**; later charges reuse it.
6. **Revoke** on `canceled` / `failed` / `subscription ended`.
7. **Receipts**: 54-ФЗ fiscal receipt via the provider API; don't hand-roll.

## Reference architecture

```
Bot ──create payment──▶ Provider
 ▲                          │ webhook (succeeded/recurrent/canceled)
 │ grant/revoke             ▼
 └──── backend ◀── verify sig → update subscription row → act on access
```

One `subscriptions` table: `user_id, plan, status, provider_token,
current_period_end, last_event_id`. Access reads status; money decisions come
only from webhooks.

## Webhook security (never skip)

- Whitelist provider source IPs where documented.
- Replay protection: store `last_event_id`, drop duplicates.
- **Amount check**: confirm paid amount == expected plan price before granting;
  a tampered webhook must not buy access for 1 ₽.
- Secrets (API key, Basic password) live in `/root/.secrets/`, never in bot
  code or workflow JSON.

## Bot-side flow

1. `/pay` → `createPayment(amount, plan)` → send link.
2. User pays → webhook → verify → insert/refresh subscription row.
3. Bot checks row → sends invite / adds to channel.
4. Worker/cron: rows past `current_period_end` with no fresh payment → revoke + notify.

## Pitfalls

- **Card data never touches your server** — use the widget/token. Raw PAN breaks PCI.
- **Test keys first**: run pay→webhook→grant→revoke on test keys before going live.
- **Two-stage capture**: some providers return `waiting_for_capture`; confirm it or you grant access on money never captured.
- **Refunds**: build the refund path (provider API) before launch.
- **Legal**: client needs ИП/самозанятость + provider approval of the niche.
  Trading-signal niches face stricter moderation — set that expectation early.

### python-telegram-bot specifics

- **First matching callback handler wins.** PTB does NOT chain handlers that both match — it picks the first registered one. If you register `CallbackQueryHandler(menu_callback)` without a pattern AND a second one with `pattern="^topup_"`, every callback is eaten by the first and the second never fires. Fix: register ONE general handler and dispatch by `callback_data` prefix inside it.
- **Do not re-import a globally imported name inside a function.** Python sees the local `import` and promotes the name to a local variable for the WHOLE function; the top of the function then raises `UnboundLocalError` because the assignment hasn't run yet. If a module is imported at the top of the file, never `from x import that_module` again inside a function — call it directly.
- **`getMyStarBalance` may not exist on `ExtBot`** in older PTB versions. Wrap the call in try/except and treat absence as "Stars unavailable". Hardcoding "Stars works" is wrong for fresh bots.
- **Register `CallbackQueryHandler` for `pre_checkout_query` and `MessageHandler` with `filters.SUCCESSFUL_PAYMENT`** at the dispatcher level — these are NOT callbacks, they have their own handler types.

### Webhook hosting

- **Run the webhook server inside the same PTB process** via `Application.post_init` + `asyncio.create_task`. PTB uses long polling for Telegram updates so the event loop is free. Spinning up a separate systemd unit is unnecessary unless the webhook handler is heavy.
- **Bind to `127.0.0.1`, not `0.0.0.0`.** Terminate TLS at the public reverse proxy (nginx/caddy) and proxy to localhost. Lets the proxy own certificates.
- **Always respond `200 OK` quickly**, then process. Most providers retry on any non-2xx; slow handlers trigger 20+ retries and you waste API quota.
- **For nginx in docker** (`jonasal/nginx-certbot` style): the vhost file inside the container has `server { listen 443 ssl; ... }` blocks. New `location` directives must be inserted INSIDE the active server block — appending at file end puts them between blocks and nginx fails `nginx -t` with "location directive is not allowed here".

## Selling point

Ship as a template: paid-channel bot + subscription table + webhook verification
+ grant/revoke worker, provider-swappable. Show a demo link. Never claim
experience you can't demonstrate.
