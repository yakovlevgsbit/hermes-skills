---
name: third-party-tool-vetting
description: "Use when evaluating a GitHub repo before adopting it."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [vetting, open-source, adoption, licensing, repo-audit, skill-adaptation]
    related_skills: [codebase-inspection, subagent-library, web-design-check]
---

# Third-Party Tool Vetting

Decide whether an external GitHub project is worth adopting, adapting, or skipping — and extract only the part that transfers. Covers the whole arc: "изучи эту ссылку" → a cited verdict, and (only when asked) a working installation.

## When to Use

- The user shares a GitHub URL and asks «изучи», «можем использовать?», «что это такое».
- The user shares a promo video or social post about a tool instead of the repo itself.
  Trace it to the project, then vet the project on its own evidence, treating the video's
  claims as the checklist to verify — invented urgency («the vendor is furious»), tier
  arithmetic and superlatives are the parts most likely to be wrong.
- Choosing between external repos for the same job.
- Before writing SKILL.md for an adaptation of someone else's tool.

**Scope is set by the user's wording, not by this procedure.** «Изучи», «разбери»,
«что это» = desk research only: docs, repo metadata, license files, independent
reviews and benchmarks. Do NOT install, run, or pull images until the user says
«ставь», «попробуй», «проверь вживую». Runtime installation/testing in steps 5–6 below is opt-in; desk research uses published requirements and source inspection only.

Why: running a heavyweight repo on a production box without being asked burns
real CPU, RAM and disk for hours — one 17 GB ML image held the host at load
average 8–11 and left abandoned jobs running. The test result is worth less than
the box staying up. If desk research leaves a number you genuinely cannot get
without running it, ASK before running it.

**If you already ran it, say so plainly and clean up before continuing.**
When the scope was exceeded, the recovery is: state in one line what was
installed and what it cost the box; remove the artefacts (image, container,
volume, package, cache) and confirm the host is back to its prior state; then
continue with the desk research the user asked for. Do not bury the overrun
under a long report, and do not quietly leave the footprint in place. A
production box that a research task left heavier is a bill the user did not
agree to — and the next task inherits the drift.

Don't use for: auditing the user's own code (see `adversarial-code-review`), or
reviewing a dependency for known CVEs.

## Specialized evaluations

- Keyless/free model plugins and routers: [references/free-model-gateways.md](references/free-model-gateways.md).
- Website/app/game reconstruction tools: [references/reconstruction-tools.md](references/reconstruction-tools.md).
- Coding-agent plugins, token-saving styles and security scanners: [references/agent-plugin-claims.md](references/agent-plugin-claims.md).
- Finding and reviewing skills without unnecessary installation: [references/skill-discovery.md](references/skill-discovery.md).
- AI ad-creative systems, playable exports, and automated spend claims: [references/ad-creative-systems.md](references/ad-creative-systems.md).
- Design-agent bundles, schema collisions, extraction helpers and hosted-service boundaries: [references/design-skill-bundles.md](references/design-skill-bundles.md).

## Procedure

1. **Pull repo + metadata in parallel.** Clone (shallow), and in the same call
   fetch the GitHub API: stars, forks, open issues, `archived`, `pushed_at`,
   `license.spdx_id`, primary language.
   ```bash
   git clone --depth 1 <url> && du -sh <dir>
   curl -s "https://api.github.com/repos/<owner>/<repo>"
   ```
   `pushed_at` older than ~12 months = treat as dead until proven otherwise.

2. **Read the structure, not the README.** List top-level files, count by
   extension, then find where the real value lives. In Claude-Code-era skill
   repos the giant `SKILL.md` files are usually harness scaffolding (preamble,
   telemetry, plan mode); the actual knowledge sits in `data/`, `specialists/`,
   `sections/`. Report the split explicitly: «X KB of harness, Y KB of substance».

3. **Check the license against the intended use.** MIT/Apache permit broad use subject to their conditions. AGPL is not a commercial-use ban: review the actual integration, modifications, distribution and network-service obligations, including corresponding-source offers where applicable. Do not assert that every surrounding proprietary product must become AGPL merely because it calls an external service. Check model/data/brand licenses separately; a permissive code license does not grant those rights.

4. **Check what it is built ON, before what it costs.** Identify the platform
   and credential each capability depends on. A tool is worth far less when
   its best channels need a desktop browser session (headless browser or
   server-side runtime does not substitute for a logged-in Chrome profile),
   or a phone-verified / real-name account, or a region the user cannot sign
   up from. Say which half of the feature matrix is reachable from THIS box —
   that is usually the whole verdict.

5. **Check runtime requirements within the authorized scope.** For desk research, inspect manifests, service definitions and published image metadata; mark idle RAM, latency and engine behavior as unmeasured. Do not pull images or start services to obtain these numbers. For a separately authorized live test, inspect current host capacity, measure the isolated stack and report the calculation with actual tool output. Published RAM requirements are not an idle-RAM measurement.

6. **Test the engine live — only when the user asked for it.** Run it several ways
   from the upstream checkout: main path, edge flags, JSON mode, persistence,
   error paths. Only adapt what demonstrably runs. Before starting, state what
   you are about to pull and how much of the box it will consume, and prefer a
   throwaway container with `--memory`/`--cpus` limits. Kill it and reclaim disk
   the moment you have the numbers — an abandoned heavy job keeps running and
   keeps holding the device.

7. **Adapt, then test from the installed path.** When porting to Hermes:
   - Strip harness-specific tool references and rewrite them to this
     environment's tool names (see `references/adapting-foreign-skills.md`).
   - Copy engine + data, skip the CLI/gallery/screenshots dead weight.
   - Re-run the tests from the destination directory — a test that passed in
     the source tree can fail from the new path.

8. **Deliver a verdict, not a survey.** The user wants a decision: adopt whole /
   adapt to Hermes / extract methodology only / skip — plus what NOT to take and
   why. When there are several viable paths, give numbered options with the
   recommendation first; this user picks one and expects it executed.

9. **Before recommending any provider, credential, or account, check what is
   already connected.** Grep the KB's provider registry (`/root/kb/ops/llm-providers.md`)
   and the secrets dir for the provider's name and its domains. A curated list of
   free tiers will happily recommend a provider the user already pays for under a
   different hostname, and will list a second key for a service one key already
   covers. Name the overlap explicitly in the verdict — "already have this via X"
   is a finding, not noise. Same check before proposing a new provider plugin:
   the registry records the exact model ids, base URLs and auth quirks for every
   provider already wired, so the recommendation inherits known traps instead of
   rediscovering them.

   **Then check whether the audit already exists.** Search the KB for the repo
   name, the provider domain and the service slug before writing anything:
   `grep -rilE '<provider>|<domain>' /root/kb/`. A prior verdict is a starting
   point, not a duplicate to redo — read it, verify only what has changed
   (version, pushed_at, prices), and amend it. Re-vetting from scratch wastes
   the session and risks contradicting a decision the user already took.

   **Say which finding is new.** If the audit already existed, name the delta
   in one line («the star count moved, the licence did not; the verdict stands»)
   instead of re-narrating the whole project — the user already read it.

   **When the user asks the economics after the verdict, price against the
   baseline the environment actually runs.** The question is never «is this
   provider cheap» in the abstract; it is «cheaper than WHAT we already pay».
   Name the existing route, the unit of comparison, and the side that decides
   it. Two sides usually have opposite answers: **consumption** (our own
   rungs, videos, covers) favours whichever provider is cheaper per unit,
   while **resale** (a bot selling generations to clients for Telegram Stars)
   favours the widest catalogue, because assortment — not unit price — is what
   the customer buys. Say which side the workload is on; if the KB does not
   say, ask, because the two verdicts are opposites and guessing wrong sends
   the user down a paid path that buys nothing.

10. **When the candidate competes with something already running, price it
    against that — not against the vendor's list.** The unit of comparison is
    the same deliverable (same model, same duration, same resolution), priced
    the same way on both sides, including the cost of the account, the key, the
    extra dependency and the layer of code someone has to maintain. "The new
    provider is cheaper" is only meaningful against a named baseline. If the
    existing route is already cheaper on the workloads actually being run, the
    honest verdict is "do not switch" — and the new provider's value, if any,
    is usually a wider model catalogue rather than a lower price.

    For media generation specifically, see `media/generative-media-api-generation`
    for the two-sided comparison (per-unit cost, markup on resale, assortment
    width) — the deciding question is usually whether the workload is
    consumption or resale, because those have opposite answers.

## Pitfalls

- **A project can be a curated catalog or a hosted service, not code to install.**
  If the thing being evaluated is a list of APIs, a cloud agent platform, or a
  route table, there is nothing to run and step 6 does not apply — the
  deliverable is a decision about whether to USE it and through which surface.
  Say so explicitly instead of hunting for a test to execute.
- **What is already installed beats a better upstream tool.** Before naming an
  alternative to an existing capability, diff it against what the environment
  already has: matching skills, an installed CLI, a working reader. Then either
  name the single concrete axis where the alternative wins ("compare tool A vs
  tool B on one query") or state that the current setup already covers it. A
  recommendation to replace something that already works is the failure mode.
- **A catalog's rows are marketing summaries; its footnotes are the audit.** Long
  curated lists keep the flattering part in the table and the binding constraints
  (regional restrictions, training-data consent, unpublished limits, real-name
  verification, "non-commercial use only") in numbered footnotes. Read the
  footnotes before quoting any row, and quote the constraint with the number.
- **A "free tier" with unpublished limits is not a plan.** A provider whose docs
  say "check your quotas in the console" or "limits may be reduced without
  notice" cannot carry production load, however good the model looks. Prefer
  providers that print exact RPM/RPD/TPM numbers, and say which class you would
  trust with real traffic.
- **Rate limits are often org-level, not key-level.** Several providers count RPM
  and RPD per organization or per IP, so minting a second key does not multiply
  quota — and rotating keys to dodge a limit is a ToS violation at some of them.
  Check the aggregation scope before proposing a fallback strategy.
- **A README is marketing, not state.** "Open source alternative to X" and
  "free commercial use" have both turned out to contradict the actual LICENSE
  file. Read the LICENSE, and read the model license separately when one exists.
- **A bundle's licence is per folder, and a missing one is a refusal.** In a
  multi-skill repo the root often carries no LICENSE at all while each
  `skills/<name>/LICENSE.txt` differs — one family can be relicensed mid-life
  (Office moving to Apache-2.0) while its neighbours stay proprietary, and a
  skill with no licence file cannot be copied however official the repo. Read
  every subfolder's licence at the revision under review, not the repo badge.
- **Popularity metrics do not prove quality or fraud.** Stars, watchers and forks can all be noisy or manipulated. Do not infer purchased stars from a ratio alone. Inspect canonical provenance, commit/release history, substantive issues, tests and independent evidence; label any remaining concern as uncertainty rather than an accusation.
- **An empty benchmark table is an absence of evidence.** A `benchmarks.md`
  that says "no verified rows yet" means every speed claim in the README is
  unmeasured by the authors. Find an independent measurement on comparable
  hardware instead — search for the provider plus "benchmark" or "RTF" on a
  box you can identify (core count, year, GPU). Never present an RTF as a
  property of the model: it is a property of model × hardware, and a second
  measurement on different silicon that agrees tells you the ratio, not the
  number. Quote the hardware class with every figure you cite.
- **A headline benchmark number is the vendor measuring itself.** «71.5× fewer
  tokens» printed by the project's own script measures its own corpus, in its own
  unit (per query, over mixed documents and images) — not a coding session on our
  code. Quote corpus, unit and measurer; with no independent run, say the number
  is unmeasured, and then ask whether the win exists at our size of codebase at
  all, because a graph pays off on large unfamiliar trees and costs setup on small
  ones.
- **«A free tool replaces a $200 subscription» is an economics claim, not a
  capability claim.** Two checks settle it: the tier's real price and what that
  tier actually buys — usage limits and model access are not bought with token
  savings — and whether the tool sells its own paid plan. A product that kills
  subscriptions rarely sells one.
- **CPU-only is a different product.** A tool can be "fully usable on CPU"
  and still be unusable: 4 cores from 2013 could not finish a default-engine
  generation inside the app's own 600 s budget, and cutting quality settings
  did not save it — the box is the binding constraint, not the configuration.
  Always time the DEFAULT path on the actual box, not a lighter engine, and
  read the app's own error text for what a timed-out job does. An abandoned job
  that keeps running and keeps holding the device is a production hazard, not a
  slow feature: on a shared host it silently steals CPU from the services you
  already run, and the tell is load average climbing while your test looks idle.
- **Model weights have their own license, and it can forbid commerce.** A
  permissive code license (Apache-2.0) does not license the weights: check the
  HF model card's license field and its discussions, not just the repo LICENSE.
  CC-BY-NC weights make the default model unusable for client work even when
  the app is AGPL and the code is free. Look for a repo's own license-inventory
  file — a `commercial_use: true` flag with none set is a finding, not a gap.
- **Stars do not mean maintained.** 135k stars with a year of silence is a
  museum piece; 1 star with a commit last week can be the better bet. Check
  `pushed_at`, not the star count.
- **Harness scaffolding masquerades as value.** A 137 KB `SKILL.md` can be 90%
  Claude Code preamble and telemetry. Find the `data/` or `specialists/`
  directories before judging the size.
- **A vendor bundle's value may be its prose, not its code.** Check what each
  skill actually invokes before planning an install: an eval loop that shells out
  to the vendor's own CLI (`claude -p`) transfers as methodology, not as a runnable
  script, because that binary and its auth are not on this box. Decide
  «methodology only» explicitly and re-implement the loop on our own model route,
  instead of installing scripts that can only fail.
- **Zero test results usually means a wrong query, not broken data.** Before
  "fixing" adapted code that returned nothing, run the same query against the
  upstream original. Byte-identical output means the data is fine and the query
  hit columns the engine does not search semantically.
- **Derive every command from the real `--help`.** Writing SKILL.md from memory
  of the docs produces wrong flag names that fail every test. Read the actual
  argument list, then document it.
- **Verify the destination against disk, not memory.** A KB note claiming a
  file was "not taken" can be stale; the file is on disk and working. Read the
  current file before patching it.
- **Do not execute the repo's own install instructions during a desk pass.** A
  README that says "paste this into your agent" is the repo's onboarding flow,
  not a research finding — running it installs packages, writes config, may
  register skills and may hit a paid API. Copy the commands out, read them, and
  report them; install only after the user says so. The same applies to
  `npx <pkg>`, `pip install <git-url>`, `curl … | sh`, `npm i -g` and any
  `skills add` line quoted in a README.
- **Adapted skills need their own attribution header.** Record the upstream
  project, license, and what was changed, in every adapted file and in the KB.

## Reporting

Report in this shape: what it is → canonical provenance and maintenance status → license reality → platform/credential requirements → what is worth taking → what to skip and why → a ranked verdict. Use popularity metrics only as context, never as proof of quality, maintenance or fraud.

Two output rules for this user:

- **No preambles or restating the request.** Start with the finding, not with
  "I studied X". Every sentence carries information; drop the ones that only
  confirm you did the thing he asked for.
- **Numbered, ordered-by-recommendation options.** When several paths are viable,
  list them best-first and say what each costs. He picks one and expects it
  executed — a flat list of five equal candidates is not a decision.

Keep the file in the KB (`/root/kb/projects/<repo-or-service>.md`) and commit
it, so the next session starts from the verdict instead of re-vetting. A
one-paragraph chat answer is not the deliverable for this class of task.

## Verification

- [ ] Repo metadata pulled (pushed_at, license, archived) before any judgement.
- [ ] License checked against the intended commercial use.
- [ ] Platform/credential dependencies identified and checked against this box.
- [ ] Existing local coverage checked before recommending any replacement.
- [ ] Runtime requirements compared against actual free RAM and disk.
- [ ] Verdict written to the KB and committed.
- [ ] Every adapted file carries attribution; KB records the decision.
- [ ] **Desk-research passes: no install, no pull, no run.** The default scope ends
  at documents and metadata. Checking this box means you stopped before the engine.
  If an engine was run anyway, the artefacts are removed and the host's prior
  state is confirmed before the report goes out.
- [ ] **Live passes only (user asked for them):** the engine ran from the upstream
  checkout AND from the installed destination, and the box is checked only after
  both succeeded. Delete these two lines rather than leaving them checked from a
  desk pass.
