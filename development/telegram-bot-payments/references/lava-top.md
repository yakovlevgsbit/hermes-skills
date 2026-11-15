# Lava.top provider specifics

Use when integrating Lava.top into a Telegram bot for RU-market recurring
subscriptions.

## Auth

- Header: `X-Api-Key: <api_key>` (NOT `Authorization:`)
- Webhook auth uses the SAME key in the `X-Api-Key` header — verify it
  before parsing the body. Treat any other header format as unsigned.
- Base URL: `https://gate.lava.top`
- No SDK required — vanilla `aiohttp` works and avoids venv bloat.

## Create subscription / invoice

- Endpoint: `POST /api/v3/invoice` (NOT `/api/v2/invoices` — that returns 405)
- For recurring: include `"periodicity": "MONTHLY"`
- For one-off: omit `periodicity` (defaults to one-time)
- `buyerLanguage` is an **enum**: must be uppercase (`"RU"`, `"EN"`, `"PT"`, `"ES"`). Lowercase `"ru"` returns 400.
- `email` is REQUIRED and must have a **public TLD** (gmail.com, yandex.ru).
  `forge.local` is rejected. If you don't want to ask the user for email, you
  cannot use Lava.

Successful response (201):
```json
{
  "id": "<uuid>",
  "status": "new",
  "amountTotal": {"currency": "RUB", "amount": 500.00},
  "paymentUrl": "https://app.lava.top/products/<seller>/<offer>?paymentParams=..."
}
```

The `id` field is the invoice/contract id — save it for webhook matching.

## Webhook

Configure in [app.lava.top](https://app.lava.top) → Integrations → API →
Add Webhook.

- URL: `https://<your-domain>/<webhook-path>`
- Auth: select "API Key", pick the same key
- Events to enable: at minimum `payment.success`,
  `subscription.recurring.payment.success`, `subscription.cancelled`

**Retry policy**: 20 attempts — first 1s/5s/15s, then 10×1min, then 5×1hr.
Slow handler = quota burned.

**Envelope shapes vary by event type**:
- Old `payment.*` and `subscription.*` events use a flat camelCase structure:
  `{"eventType": "...", "contractId": "...", "buyer": {...}}` — no `data` wrapper.
- New `refund.*` and `chargeback.*` events use an envelope with `data` field
  and snake_case field names.

**Always**: handle BOTH shapes — try `payload.get("data") or payload` for
the body, and accept `event` / `eventType` for the type.

### Identifying the buyer

Without a stored `metadata.user_id` field you set yourself, you must look
the user up by:
1. `data.contractId` / `payload.contractId` — map to your saved contracts table
2. `data.email` / `payload.buyer.email` — map to user_id you saved at sign-up
3. `customFields.telegram_id` if you passed it

Keep an in-memory dict `pending_subscriptions[contract_id] = {user_id, plan}`
for the lifetime of the bot process. Persist to DB if the bot restarts
between signup and webhook.

### Logging the raw payload

Always log the full raw body on first contact with a new event type:
```python
logger.info(f"Lava webhook: event={event_type}, payload={payload}")
```
Then add explicit handlers once you know the real shape.

## RU-account constraint

For Russian accounts Lava may expose **only subscription products** — no
true one-time products. Workaround: create a subscription with
`periodicity=MONTHLY`; the user can cancel after the first charge and you
have effectively taken a one-time payment through a subscription mechanism.

If the UI in the creator dashboard only shows "Подписка" (not "Разовая
продажа"), this is the case.

## Testing without spending money

There is no sandbox. Real test requires:
1. A product priced as low as the platform allows (1 RUB on Lava)
2. A throwaway card or SBP transfer

Run your test once, then immediately cancel the subscription in the
dashboard to avoid the next month's charge.

## Field name gotchas (verified against the live API)

| What you want | Actual field | Notes |
|---|---|---|
| Subscription/invoice id | `id` | NOT `contractId` on create; webhook may use either |
| Buyer email | `email` or `buyer.email` | API rejects non-public TLDs |
| Amount | `amount` / `sum` / `paidAmount` | Accept any of these in webhook |
| Status | `status` | `"new"`, `"paid"`, etc. |
| Payment URL | `paymentUrl` | NOT `url` or `payment_url` |

## Alternative: polling instead of webhook

For one-time flows only — recurring is impractical via polling because
charges arrive monthly.

```python
# Every 30s, check pending invoices
data = await get_invoice(invoice_id)
if is_invoice_paid(data):
    await credit_topup(user_id, ...)
```

Acceptable for one-shot products. For subscriptions, set up the webhook —
it's required.
