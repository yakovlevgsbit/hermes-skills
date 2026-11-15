# Digest agents — aggregation, dedup, ranking

Depth for agents that poll many sources, filter, and emit a ranked report
(news watchers, repo scouts, price/competitor monitors). The always-on rules
live in SKILL.md; this file is the design detail.

## Source discovery is a probe, not a guess

Before writing the fetch list, probe each candidate URL and record status +
size. A feed map for one domain goes stale fast: vendor blogs move to
`/news/rss.xml`, some drop RSS entirely, Reddit and several doc sites answer
bots with 403. Keep the working set small and verified rather than large and
aspirational — a feed that 404s on every run costs a failed branch each tick.

Mark which sources are weight-3 (primary, first-party announcements),
weight-2 (independent analysis), weight-1 (mainstream/business). Weight is
what breaks ties when two items are equally fresh.

## GitHub as a discovery source

API mechanics that decide whether a repo-scanning agent produces signal:

- **Query by topic, not full text.** `q=topic:agent-skills&sort=stars` returns
  real collections; `in:name,description,readme` matches every repo whose README
  mentions the words and puts `awesome` / `public-apis` / interview-prep repos on
  top.
- **`/search/*` and core are separate rate buckets** — 30 req/min for search
  against 5,000/hour for core. `/rate_limit` reports both; read it before a
  loop of queries, not after the 403.
- **Search results do not carry `subscribers_count`**, and `watchers_count` in
  the search payload is a copy of `stargazers_count`. Any manipulation check
  built on it sees 1:1 for every repo. Fetch `/repos/{owner}/{repo}` per
  shortlisted candidate (1 core request) to get the real watcher count — score
  the shortlist after enrichment, not before.
- **`/search/code` paginates shallowly.** `filename:SKILL.md` reports millions of
  total matches and hands back the first few hundred, so use it as a pointer to
  candidate repos, never as a count.

What the stars:watchers ratio means once you have it, and the licence/currency
checks that go with it, live in `third-party-tool-vetting` — do not re-derive
the thresholds here.

## Per-source balancing

Cap items per source at roughly `batch_size // 3` before the LLM call, sorted
by freshness within the source. Without a cap, ranking by volume means the
loudest feed becomes the entire report. Log the cap so the numbers in the
report are explainable.

## Dedup

- Normalize the title (`re.sub(r"\W+", "", title.lower())[:60]`) and keep a
  set — the same story reprinted across three outlets collapses to one.
- Keep a `seen.json` of emitted ids for cross-run dedup, and prune it on a
  window (60 days) so it does not grow without bound.
- A watermark of ids answers "what is new since last run"; a time window
  answers "what happened today". Pick per agent — a daily digest usually wants
  the window, a watcher wants the watermark. Do not mix them in one file.

## Ranking a scout list

Bucketed points (`stars >= 1000 → 30 pts`) collapse the ranking: every strong
candidate lands on the same total and sorting becomes a no-op. Use a log scale
for the popularity term (`min(cap, log10(n + 1) * k)`) so the list actually
orders, and keep the discrete buckets only for gating.

Score components that survive across domains: freshness (dominant), popularity
(log), license permissiveness, topical relevance, then penalties for archived /
noise / suspected manipulation. Emit the penalty reasons next to the item — a
score with no explanation cannot be audited.

## Batch enrichment through the LLM

To translate or annotate N items in one call, ask for delimiter-separated lines
rather than JSON:

```
owner/repo ||| русское описание
```

A malformed JSON block loses the whole batch; line-wise parsing loses only the
broken line, and the caller can fall back to the original text per item. Tell
the model the exact separator and one line per item, then split on `|||` and
strip list markers (`-`, `*`, `•`) from the left side before matching keys.

Enrich exactly the items that will be displayed — recomputing the display
slice after enrichment means some rows come back untranslated.

## Idempotency of the state file

Store only what the next run needs to decide: seen ids with timestamps, quota
counters keyed by UTC day, last successful run. Do not store the report body —
it is already on disk and in the chat, and a growing state file is the thing
that eventually makes the run slow.
