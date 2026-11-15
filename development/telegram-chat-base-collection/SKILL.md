---
name: telegram-chat-base-collection
description: "Use when assembling a Telegram chat list for outreach."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [telegram, chats, groups, outreach, lead-gen, catalog, tgstat, dedup]
    related_skills: [telegram-ad-vetting, competitor-news-monitor]
---

# Telegram chat/group base collection

Assemble a list of Telegram *groups/chats* (not channels) for an outreach
campaign — offer broadcasts, community seeding, survey recruitment. Load when the
order is «собрать базу чатов», «найти группы по теме», «50–500 чатов для
рассылки».

## When to Use

- The user needs a target list of Telegram groups in a niche, with sizes.
- The list feeds a placement or a broadcast, so dead and off-topic entries cost
  real money.

Don't use for: pricing one channel's ad (see `telegram-ad-vetting`).

## Always-on rules

1. **Groups, not channels.** The client asked for чаты (interactive groups). Most
   Telegram catalogs list *channels*; shipping channels as chats is the single
   most common way to fail this task. Verify each entry is a group.
2. **Dedup by normalized URL before counting.** Strip `https://`, `t.me/`,
   `telegram.me/`, trailing slashes, lowercase. Overlapping catalogs duplicate
   heavily; report the deduped count, never the raw sum.
3. **Filter the dead ones out and say so.** A chat with zero messages and zero
   monthly-active users is dead; drop it. State the filter you applied.
4. **Never claim a freshness you cannot see.** Catalogs expose monthly activity
   (MAU), not the date of the last message. «Последние сообщения не старше 7
   дней» is not verifiable from a catalog — say that plainly and mark which
   entries are active-by-MAU versus unverified.
5. **Exclude the excluded categories explicitly** (intim/escort/adult, and any
   the client named) and report that you did.

## Sources, ranked

- **TGStat chat ratings — `tgstat.ru/ratings/chats/<category>`** — the primary
  source: it is the catalog that lists *chats* with participants, message count
  and MAU. Useful categories: `psychology`, `babies` (family), `other` (the big
  dating/general groups live here). Sort by members, msgs, or mau.
- **telegid.me/catalog/supergroups/...** — large group catalogs (e.g. «женские
  чаты»), usually without metrics.
- **tgramsearch.com**, **russian-chats-list (GitHub)** — city/country group
  lists; useful for a geographic slice.
- **Editorial подборки** (vc.ru, dtf.ru, РБК, МИФ, Netology) — mostly *channels*;
  mine them for names, then verify group-vs-channel elsewhere.
- TGStat starts returning 429 to plain fetches after a few pages; use the browser
  tool for deeper pages.

## Procedure

1. Slice the niche by topic so each slice is independent (psychology /
   relationships / women's communities / family / self-development).
2. Harvest each slice from TGStat ratings first, then the secondary catalogs.
3. Normalize URLs, dedup, drop dead entries, drop non-groups.
4. Attach per-entry metrics where the source gives them; leave the rest marked
   unverified rather than guessing.
5. Emit a CSV: name, link, participants, MAU, topic, source. Keep the raw harvest
   so the count can be re-derived.
6. Report the deduped count, the topic split, and the honest limitations.

## Parallel harvest

The slices are independent, so a fan-out of subagents (one per topic slice) works
well — each returns its own list, and the parent dedups and merges. Append each
slice to a file as it lands so a timeout does not lose progress, then aggregate
in code rather than in your head.

## Pitfalls

- **Channels counted as chats.** Re-check before reporting.
- **Raw sums across catalogs.** The same group appears in three lists; dedup.
- **Zero-MAU entries passed through.** They are dead; drop and say so.
- **Invented freshness.** Do not state «активен за последние 7 дней» from MAU.
- **Private groups (`t.me/+hash`) cannot be joined without the invite** — fine as
  a target, but outreach there needs the admin, not a public post.

## Verification

- Count is deduped, and every entry is a group.
- Dead entries excluded, exclusion categories named.
- CSV opens and the topic split sums to the reported total.
