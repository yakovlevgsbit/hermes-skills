---
name: oss-project-evaluation
description: "Use when vetting an open-source project for adoption."
version: 1.1.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [open-source, evaluation, adoption, licensing, capacity, fork-detection]
    related_skills: [second-brain-kb, subagent-library, design-system-recommender]
---

# OSS Project Evaluation

Decide whether a third-party open-source project belongs in this stack, and which
parts are worth taking. The deliverable is a recommendation backed by evidence:
identify, read, measure, then advise.

**Never advise from the README alone.** A README is marketing. The LICENSE, the
compose file, and the source are the facts.

## When to Use

- The user sends a GitHub link and asks what it is or whether it can be used.
- Deciding whether to install, self-host, or port parts of a project.
- A listicle or article points at several repos and asks which are worth taking.
- A video or post advertises an "AI agency / 200 roles in one repo" — that is a
  prompt library plus a harness plugin, and it has its own procedure
  (`references/agent-roster-repos.md`).

Don't use for: auditing code you already run (that is `adversarial-code-review`),
or evaluating a business idea (`idea-validation`).

## Procedure

1. **Identify what you are actually looking at.**
   ```bash
   curl -s https://api.github.com/repos/<owner>/<repo>
   ```
   Read `fork`, `parent`, `archived`, `pushed_at`, `stargazers_count`,
   `license.spdx_id`. A linked repo is often a **fork** — and a fork's README may
   link to an upstream that no longer exists. Follow to the canonical repo before
   evaluating anything; a year-stale fork and its thriving upstream are different
   projects.

2. **Read the license in source, and look for a SECOND one.**
   `NOASSERTION` from the API means "not a standard SPDX id" — fetch the LICENSE
   file and read it. Then list the repo root for separate model/data licenses
   (`*.pdf`, `*Licensing Agreement*`). Code and model licenses routinely differ,
   and **the stricter one governs what you may ship**.

3. **Check telemetry and data egress in source.** Grep the shipped code for
   `opt.in`, `opt.out`, `DO_NOT_TRACK`, telemetry endpoints. The *default* state
   matters more than whether the feature exists.

4. **Measure the real footprint** — see `references/vps-capacity-fit.md`.
   - Images: sum layer sizes from the registry manifest, not the README.
   - RAM: estimate per-service idle from the compose file, compare to `free -h`.
   - Hardware: `nvidia-smi`, `lspci`. A GPU requirement with no GPU is an instant no.

5. **Separate methodology from harness scaffolding.**
   Portable: Markdown prompts, checklists, CSVs, JSON schemas, API contracts,
   decision rules. Harness-bound: CLI installers, marketplace manifests,
   editor-specific config dirs, bundled browsers, host-specific hooks.
   **Take the first; name the second as dropped and say why.** Most of a repo's
   weight is usually scaffolding.

6. **Verify every claim before repeating it.** Hardware tables, "free commercial
   use", "works with any agent", and platform lists are marketing until you have
   read the LICENSE, the compose file, or the code that implements them.

7. **If the artifact is a prompt, evaluate it as executable content.** Repos of
   agent personas / role libraries, and plugins that inject them into a coding
   harness, ship instructions that will run with the host agent's credentials.
   Measure role count after validation, body size (median, min), language, whether
   the role names cover the user's stack, and network calls in the installer; then
   scan every body for injection and exfiltration patterns. Build any harness
   plugin into a scratch dir and exercise its handlers through a stub context — do
   not install it to find out what it does. Full procedure, the stub-context
   harness, and how to probe search quality: `references/agent-roster-repos.md`.

8. **Give a verdict naming the single deciding fact.**

## Output format

```
VERDICT: adopt / take methodology only / do not adopt
CANONICAL: <repo it actually lives in, if the link was a fork or stale>
LICENSE: <code license> + <model/data license if separate> — <commercial constraint>
FITS THIS BOX: yes/no — the one number that decides
TAKE: <portable parts>
DROP: <harness-bound parts> + why
BLOCKERS: <ordered by weight, worst first>
DO NOT: <the parts to skip, e.g. another harness's config dirs, the bundled app>
NEXT: <exact install command, undo command, where the config backup goes>
```

The verdict answers "can I use this", so it also answers "what will bite me if I
say yes" and "how do I take it off" — a reader should be able to act on it, or
say no, without a second round of questions.

## Pitfalls

- **Evaluate the canonical repo, not the linked one.** A fork can be a year dead
  while upstream ships weekly, and its README links rot first.
- **Trust the LICENSE over the README's commercial-use claim.** "Free commercial
  use" in a README routinely sits above a non-commercial, revocable model license.
- **A second license file governs the models.** Permissive code plus a
  restrictive model licence means the restrictive one decides.
- **Measure before advising.** Registry manifests and per-service RAM estimates
  beat any README table — and a measured number is arguable in a way an adjective
  is not.
- **Check memory pressure before adding load.** Nonzero swap can reflect earlier pressure and does not alone prove a current RAM deficit. Inspect available memory, swap growth/activity and the production workload before admitting a new service; never infer capacity from a single headline metric.
- **Separate methodology from scaffolding.** The CSVs, prompts and checklists
  port cleanly; the installer and marketplace glue do not.
- **A GPU requirement is binary.** `nvidia-smi` absent means it does not run, no
  matter how good the project is.
- **Do not install to evaluate.** Read the compose file, the LICENSE and the
  registry manifest first; pull images only for the ones you must measure.
- **If the only valuable part is a pattern** — an API shape, an async
  submit/poll contract — say so. A pattern costs nothing to copy and carries no
  licence obligation.
- **A project aimed at a different agent harness is not automatically useless.**
  Check whether it already declares support for this one, and whether its
  knowledge (not its installer) is the part worth taking.
- **A prompt library is executable content, not documentation.** Scan persona
  bodies for `ignore previous`, exfiltration paths (`~/.ssh`, `.env`, `API_KEY`)
  and unknown hosts — then read the hits, because security and prompt-review
  personas contain those strings as legitimate defenses.
- **Measure a roster's search, not its roster.** Keyword routers score every
  match at the same baseline, so a conceptual query returns a confident wrong
  specialist. Run task-shaped queries and read the score spread before saying the
  routing works.
- **Verify harness API compatibility by grepping the installed core.** A plugin
  built against a different `register_tool` signature or a missing
  `subagent_lifecycle` imports cleanly and then does nothing.
- **A roster written for another market has no stack value.** Grep role names for
  the user's own nouns (n8n, telegram, supabase) before praising 280 roles; the
  honest count of relevant ones is usually 2–5.

## Verification

- [ ] The repo evaluated is the canonical one, or the divergence is stated.
- [ ] LICENSE read from source; any second model/data licence identified.
- [ ] Telemetry default state confirmed in code, not in docs.
- [ ] Footprint measured (registry manifest / compose estimate), not quoted.
- [ ] Verdict names the single fact that decides it.
- [ ] Portable vs harness-bound parts listed separately.
- [ ] For prompt/persona repos: role count after validation, body-size median,
      and stack-relevance count measured; injection scan reported with hits read.
- [ ] For harness plugins: core API matched by grep, handlers exercised from a
      scratch build, search quality probed with task-shaped queries.
