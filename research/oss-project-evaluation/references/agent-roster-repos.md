# Agent-roster and prompt-library repos

Depth for one specific sub-class of OSS: repos whose shipped artifact is a
**prompt** (persona files, role libraries, "an AI agency in a repo") and/or a
plugin that injects those prompts into a harness (Claude Code, Cursor, Codex,
OpenCode, Hermes). Code review of such a repo is the wrong instrument — the
deliverable is text that will be executed as instructions with the host agent's
credentials.

## What to measure (numbers, not adjectives)

| Question | Command | What it decides |
| --- | --- | --- |
| How many roles actually survive validation? | `find <divs> -name '*.md' \| wc -l` vs the count the converter prints | Roster size claims are pre-validation; the installable set is smaller |
| Is each persona a real methodology or a stub? | `wc -c` sorted, take median and min | Median under ~3k chars = prompt theater |
| Does it know the user's stack at all? | grep role names for the stack's nouns (n8n, telegram, supabase, …) | A roster written for another market has zero domain value here |
| English-only? | regex `[а-яА-Я]` over bodies | Non-English deliverables fall back to the host agent anyway |
| Network on install? | `grep -nE 'curl\|wget\|https?://\|npm i\|pip install' scripts/*.sh scripts/*.py` | Zero hits in installer, converter and lib = no telemetry, no phone-home |

Repo hygiene that separates a real roster from a dump: CI workflows that lint
the persona frontmatter, a divisions manifest checked against the directories on
disk, an originality/anti-plagiarism check, and tests for the converter.

## Prompt-injection scan (mandatory — bodies become system prompts)

Scan every body for: `ignore (previous\|prior)`, `disregard`, `curl`/`wget`,
`~/.ssh`, `id_rsa`, `.env`, `API_KEY`, `base64 -d`, `eval(`, `exec(`,
`system prompt`, `jailbreak`, plus every `https?://` host.

Interpretation rules:

- A hit is not a verdict. Read the surrounding lines. Security and prompt-engineering
  personas *legitimately* contain "Ignore all previous instructions" as a test case, and
  meeting/summarisation personas contain it to say "treat pasted text as data, not commands".
- URLs pointing at vendor docs, MITRE, RFCs and `localhost` are normal. A URL that
  carries data in a query string, or any host that is not a docs domain, is the finding.
- Report the scan as a measured line ("0 exfiltration patterns; 2 hits are defensive
  examples in X and Y"), never as "looks safe".

## Evaluate a harness plugin without installing it

1. Confirm the target harness can carry it. Grep the installed core for the API the
   plugin uses rather than trusting the repo's support table:
   ```bash
   grep -rn "def register_tool" <core>/hermes_cli/plugins.py
   ls <core>/agent/subagent_lifecycle.py     # only if the plugin delegates
   ```
   Signature drift is the usual reason a third-party harness plugin silently does nothing.
2. Build into a scratch directory, never into the live profile:
   ```bash
   git clone --depth 1 <repo> && cd <repo>
   python3 scripts/build-<harness>-plugin.py --repo-root . --out /tmp/out
   ```
   Record what it produced: `__init__.py` size, `data/*.json` size, agent count.
3. Run the handlers standalone with a stub context — no install, no gateway restart:
   ```python
   import importlib.util, json, pathlib
   p = pathlib.Path("<out>/<plugin>/__init__.py")
   spec = importlib.util.spec_from_file_location("pl", p)
   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
   tools = {}
   class Ctx:
       def register_tool(self, name=None, **kw): tools[name] = kw["handler"]
   m.register(Ctx())
   print(tools.keys())
   print(tools["<search-tool>"]({"query": "<real task>", "limit": 5}))
   ```
   Works because lazy-router plugins keep the roster on disk and touch the harness
   only inside the delegate path; import alone must not require the harness.

## Probe router/search quality before recommending it

A roster of hundreds of roles is only usable through its search tool, so measure
that, not the roster size. Run two batches of queries:

- queries that match a role NAME (`seo audit`, `sales outreach`, `code review`)
- queries that describe a TASK (`vps deployment`, `telegram bot`, `landing page design`)

Read the scores, not just the order. Many results clustered at the same baseline
score (e.g. 5.54 next to 5.55) mean plain token matching with no IDF — every
document containing any query word ties, and the top hit is noise (a map-vector
"cartography designer" for "landing page design"). Say that plainly: search
works only when words coincide with role names.

## Verdict rule for this sub-class

Personas are prompts, not knowledge: the roster carries no facts about the user's
systems, and a 13k-char persona costs context on every turn. So adopt only when
the roster names the user's stack by role, prefer the lazy-router plugin over
installing N skills into the skill catalog, and name what NOT to install (other
harnesses' config dirs, the bundled desktop app) alongside the verdict. Close with
the exact install and undo commands plus where the config backup goes.
