# Evaluating coding-agent plugin claims

Use for videos/catalogs promising a team of developers, free tokens, shorter answers or automatic security fixes. Keep project-specific snapshots and verdicts in one KB note per project; this reference contains reusable checks.

## Identify the actual surface

Distinguish instruction-only skill, host plugin, executable gateway, managed service and built-in slash command. A video may call all of them plugins. Resolve a garbled name against canonical first-party sources rather than silently treating the transcript as an exact package identifier.

Official marketplace inclusion does not imply Anthropic authorship. Check the plugin manifest, canonical upstream, author and plugin-level LICENSE.

## Treat each plugin as a licensing boundary

Read the license beside the specific plugin, not only the parent marketplace license or GitHub's detected SPDX field. A public repository can contain a proprietary plugin limited to one vendor's products; public readability is not permission to port its prompts, skills, workflows or code to a competing host.

Pin the reviewed commit. Current releases may have a different license from older releases; an old LICENSE-MIT retained as a third-party notice need not be the current project license. Check hosted services and trademarks separately.

Summarize restrictions without republishing proprietary implementation/prompt files in a public skills tap or user-facing research archive.

## Separate a method from the executor

Check for existing local TDD, review and delegation skills before proposing a new framework. An adapted subset is not the latest upstream plugin, but it is real existing coverage.

Check actual host adapters, rather than assuming a Claude-era project is Claude-only. A native plugin must still be installed and exercised before claiming live compatibility.

Translate delegation to the discovered tool schema. In Hermes, use `delegate_task(tasks=[{goal, context, ...}])`; unsupported legacy `goal=`/`toolsets=` examples are not runnable instructions. Children cannot directly clarify with the user or close tracked work. Give them full context, allowed file scope and verifiable outputs; the parent owns questions, verification and transitions.

Never blindly import global bootstrap/controller rules on top of existing adaptations. Added reviews and always-on skills may increase model calls and context overhead.

## Measure token savings against a fair baseline

Compare terse-style plugins with the user's existing concise instruction, not only an artificially verbose no-instruction baseline. Distinguish per-case median, pooled output totals, input tokens, cached tokens, reasoning tokens and provider-billed cost.

State sample size, model, skill version and whether raw pairs/quality review exist. A historical benchmark is not evidence for a newly rewritten skill. Output reduction does not prove code or semantic equivalence.

Account for the skill's own input overhead and the billing unit. Fewer tokens do not necessarily save per-request credits. Never apply a fixed promotional savings percentage to a session without a counterfactual measurement.

For memory/prompt compression, preserve literals, negation, safety constraints and retrieval of originals. Do not rewrite SOUL, USER, MEMORY or production prompts automatically merely to save tokens.

## Map each module's data boundary

Audit classic skill, CLI telemetry, local proxy, compression service, router and hosted gateway separately. Local output-style instructions may make no vendor call while optional Auto routing sends recent prompts/context to a cloud endpoint.

Read defaults and conditions precisely: installed, signed in, enabled and selected as a model are different states. Identify extra request replay/cache warming, original-data storage, telemetry opt-out and managed-mode billing before recommending global installation.

## Bound setup and security claims

A setup recommender's read-only instructions are not an OS sandbox. Distinguish analysis, recommendations, permission to change config and installation. Existing integrations must be inventoried before suggesting more MCPs or credentials.

For security tools, distinguish scan, triage, patch generation, patch validation, application and PR publication. Human approval between them matters. Bind findings to source revision; absence of findings is not proof of safety, and nondeterministic scans cannot certify a repository.

Check host permissions, repository trust, provider access to code, model/account requirements, cost and sensitive report retention. A scanner running in an existing agent session may add no isolation. Never run an untrusted checkout with production secrets to evaluate a scanner.

## Follow helper-process side effects

Inspect the actual subprocess arguments, environment, provider selection and fallback path of UI Apply/preview/automation helpers. A harmless-looking editor can launch a coding CLI with approval or sandbox bypass flags when the normal chat route is unavailable. Do not copy that default onto a production host; separate passive analysis from write/apply modes and require a constrained, authorized pilot.

Check first-run launchers and validators as executable code. A skill may download a binary when first invoked, and a project-defined validation command runs with the caller's permissions. An installer exit code or an advisory hook's success does not prove a scan ran; report fail-open and skipped checks honestly.

For minimal-code benchmarks, identify the baseline, task types, whether tests count toward LOC, whether the agent could execute/debug, and which tasks have behavioral checks. Recomputing a published table is not a live benchmark, and fewer lines do not justify missing acceptance criteria, validation or tests.

## Related KB examples

- `/root/kb/projects/omniroute.md`
- `/root/kb/projects/superpowers.md`
- `/root/kb/projects/caveman.md`
- `/root/kb/projects/claude-code-setup.md`
- `/root/kb/projects/claude-security.md`
- `/root/kb/projects/claude-mem.md`
- `/root/kb/projects/impeccable.md`
- `/root/kb/projects/ponytail.md`
- `/root/kb/projects/humanizer.md`
- `/root/kb/projects/watch-video-skill.md`
