# Message-cost lookup on a messenger platform

Use when the task is "tell me which of these phone numbers is registered on
<platform>", or when scoping a number-verification / outreach feature.

## There is no official lookup on the consumer platform

The platform's own bot API is message-oriented and exposes no "does this number
exist" method. Anything that answers the question goes through a third-party
gateway, and those gateways are thin adapters over **one authorized personal
account** on a phone number. So the real cost is not the API call — it is the
account behind it.

## The cheap-first ladder

Do not start at the paid tier; the question is usually "is there any demand at
all", and a handful of manual probes answers it.

1. **Free developer tier, manual probes.** Gateways expose a `checkAccount`
   method (`{phoneNumber: <int>}` → `{exist, chatId}`) with a small monthly
   allowance and a strict rate limit. Probe a handful of numbers by hand and
   learn the true hit rate before building anything.
2. **Only if the rate is high**, size the paid tier into the price of the
   service being sold. A monthly gateway fee is a line item in the offer, not a
   fixed cost of the feature.
3. **Never build an unauthorized automation ("userbot") as the cheap path.**
   An unofficial client running on a personal account is against the platform's
   terms and the account is the thing that gets punished: bulk lookups trip an
   abuse limit and the ban is measured in weeks. Zero spend, and you lose the
   channel entirely.

## Traps that cost real time

- **The rate limit is a per-account abuse control, not a throughput number.**
  Repeated probes of the *same nonexistent* number are flagged faster than a
  broad sweep, and a violation means backing off for hours — not retrying.
  Space probes, and never re-probe a number that already answered.
- **Lookup ≠ the right to message.** On anti-spam-oriented platforms a
  verified number still does not grant a first-message channel: the user must
  write to the bot first. A "verified list" is only a lead list, not an
  audience. Confirm this before selling the pipeline as outreach.
- **Region must be a real mobile number in a supported country.** Virtual
  numbers and out-of-region numbers are rejected outright.
- **A gateway is not a search index.** Pass it a number, not a business name.
- **A city id is not a geographic filter.** Passing a city identifier to a
  catalog API that ignores it returns nationwide rows (a capital city shows up
  under a small town's tag). Always post-filter on the city column inside the
  returned payload.

## What to tell the user instead

The honest report has three parts: (1) lookup requires a gateway bound to one
real account, (2) the free tier answers the demand question in an afternoon,
(3) the free-tier numbers are only useful if the product's value is already
established — otherwise it is spend before revenue.
