---
name: skill-routing-eval
description: "Use when a skill's trigger accuracy needs measuring."
version: 1.0.0
author: Мария (Hermes)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [skills, eval, routing, description, benchmark, trigger]
    related_skills: [hermes-agent-skill-authoring, third-party-tool-vetting]
---

# Skill routing eval

Measures the one thing that silently ruins a skill library: skills that never fire because
nobody recognizes the description, and skills that fire on everything because their scope
overlaps three neighbours. Harness lives at `/root/skill-eval/` (README there has the full
reference), adapted from the eval loop in `anthropics/skills` → `skill-creator`, which needs
the `claude` CLI this box does not have.

## When to Use

- A skill exists but never loads on the requests it was written for.
- Two or more skills claim the same trigger and you need to see which wins.
- You rewrote a `description` and want evidence it improved routing instead of a feeling.
- Auditing a batch of skills with descriptions under ~45 characters.

Don't use for: judging skill *body* quality (this only measures discovery), or for skills
whose trigger is a single command name the agent cannot miss.

## Prerequisites

- `ANYMODEL_API_KEY` in `/root/.secrets/tokens.env`.
- Fixture per skill: `{"skill": ..., "positives": [...], "negatives": [...]}`.
- Nothing to install; stdlib only.

## How to Run

```bash
cd /root/skill-eval
python3 eval.py catalog                        # index size, weak descriptions
python3 eval.py run --fixture fixtures/xlsx.json
python3 eval.py run --fixture fixtures/qa-agent.json --repeat 3
python3 eval.py run --fixture fixtures/qa-agent.json --desc-override "candidate text"
./ab_descriptions.sh fixtures/qa-agent.json    # several candidates in one pass
python3 eval.py report                         # all runs, side by side
```

## Procedure

1. **Write the fixture first.** 4–6 positives phrased the way the user actually speaks, 3–4
   negatives that belong to a *neighbouring* skill. No query may contain the skill's name.
   Completion: the file parses and `run` prints 7–10 verdict lines.
2. **Baseline the current description.** `run --fixture ...` with no override.
   Completion: `recall`, `top1_accuracy` and `false_positive_rate` written to `results/`.
3. **Read the misses, not the score.** A missed positive names the trigger word the
   description lacks; a first-choice loss names the skill that outranked it.
4. **Draft 2–3 candidates and A/B them** with `--desc-override`, same fixture, same catalog.
   Completion: each candidate has its own summary file.
5. **Repeat the winner** with `--repeat 3`. Single runs are noise at this model size.
   Completion: the winner's advantage survives the repeat, or it is declared a tie.
6. **Apply the winner to the skill file** with `skill_manage(action='patch')`, then re-run once
   without `--desc-override` to prove the file matches the expectation.

## Metrics that matter

- `top1_accuracy` — was it the **first** choice. This is the one to optimise when skills overlap.
- `recall` — was it chosen at all (including as second choice).
- `false_positive_rate` — did it fire on a neighbour's request.
- `errors` / `scored` — errored queries are excluded from rates on purpose.

## Pitfalls

- **Do not truncate descriptions in the catalog.** Hermes renders the full description in its
  skills index; truncating to 160 chars measures a prompt the agent never sees and inflates
  recall by up to 0.4.
- **Empty replies masquerade as misses.** Long prompts make `qwen3.8-27b` return empty content
  about two times in three; `glm-5.3-flash` answers reliably. The chain is `glm → qwen`, and
  errored rows are excluded rather than scored.
- **A router that starts doing the task** means the system prompt reads like an assignment:
  state "you do not perform the request", put the query first, the catalog second, the JSON
  request last.
- **`top1_accuracy` stuck at 0.2–0.4 across every candidate is a scope problem, not a wording
  problem.** Four QA skills on this box (`qa-agent`, `qa-agent-production-suites`,
  `production-health-sweep`, `dogfood`) split the same trigger; no description fixes that, and
  rewriting one to "win" makes the others worse. Report the duplication and propose merging.
- **Model routing is noisy at 27B**. One run is a hint; `--repeat 3` is a finding.

## Verification

- [ ] Fixture has no query containing the skill's own name.
- [ ] Baseline and at least two candidates measured on the same catalog (`DESC_LIMIT = 0`).
- [ ] Winner reproduced with `--repeat 3`, or the difference reported as a tie.
- [ ] The applied description was re-measured from the file, not from the override.
- [ ] If `top1_accuracy` stayed low, the overlap with neighbouring skills is named in the report.
