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

Don't build on two providers at once. Pick by the order's shape.

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

## Selling point

Ship as a template: paid-channel bot + subscription table + webhook verification
+ grant/revoke worker, provider-swappable. Show a demo link. Never claim
experience you can't demonstrate.
