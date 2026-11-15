---
name: agent-identity-and-memory
description: "Use when writing SOUL.md, USER.md, or agent memory files."
version: 1.0.0
author: curator
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [memory, identity, soul, user-profile, onboarding, preferences]
---

# agent-identity-and-memory

Interview a user and persist what you learn into the agent's identity and memory files, within hard character budgets.

## When to Use

- The user asks to introduce themselves, "get to know me", or fill in SOUL.md / USER.md / memory.
- A standing preference changed (tone, verbosity, review-before-write, safety red lines).
- Memory has grown stale, duplicated, or filled up and needs consolidation.
- The user asks to check / audit / verify the memory or SOUL.md files.

## Know the file layout first

| File | Holds | Loaded |
|---|---|---|
| `$HERMES_HOME/SOUL.md` | Identity + how to work. Standing rules. | every session |
| `$HERMES_HOME/memories/USER.md` | Who the user is, their preferences | every session |
| `$HERMES_HOME/memories/MEMORY.md` | Stable environment facts and credential locations with no task-specific home | every session |

Resolve `$HERMES_HOME` from the environment; never hardcode `~/.hermes` in a script (profiles live under `~/.hermes/profiles/<name>/` with their own copies).

Budgets are hard and enforced: `SOUL.md` ~20 000 chars, `USER.md` ~1 375, `MEMORY.md` ~2 200. Memory rejects any batch whose FINAL size exceeds the limit — a single over-budget `replace` fails the whole batch, so plan removals and additions together in one call.

## Procedure

1. **Read all three files before writing anything.** `skill_view`-style loads are not available for these; read them directly. You need to know what already exists to avoid duplicate entries — memory is injected every turn, so a rule stated twice is pure token tax.

2. **Interview in blocks of 4–5 questions via `clarify`**, not one drip at a time. Independent questions belong in ONE call. Use `choices` (recommended first) for anything with a plausible option set; omit `choices` for genuinely open input. Skipped answers are normal — do not re-ask them in a later block.

3. **Ask the questions that change my behaviour**, not biographical trivia. High-value: name and how to address them, timezone and working hours, what they build (drives which skills load), core priority in how I work, approval expectations for writes, what they find unacceptable, tone/format preferences, hardware (caps what local work is realistic). Low-value: studio details, crypto wallets, side projects — offer the list, accept skips, move on. Over-asking reads as a form to fill out.
   - Use `multi_select` for anything the user does as part of their work (what they build, what they care about in how you operate). They will tick several in one answer; single-select forces a false narrowing.
   - Hardware answers reshape the whole plan. A CPU-only VPS means no local LLMs and a whisper model ceiling — record the consequence, not just the spec sheet.

4. **Route each fact to one store only.** Who the user is and stable, cross-task preferences → `USER.md`. Stable environment facts and credential locations without a project-specific home → `MEMORY.md`. Project state and release/deployment status → project KB or session history. Procedures, tool pitfalls and task-specific preferences → the relevant skill. Do not duplicate a fact across stores or promote a one-task correction into a global rule.

5. **Write memory facts declaratively, not as commands.** Use “The user prefers numbered diffs before production changes,” not “Always present a numbered diff.” Imperatives in injected memory can be mistaken for instructions overriding the current request. Keep imperative procedural guidance in the relevant skill; omit dates, ticket IDs and completed-work logs from global memory.

6. **Prefer a skill over memory for procedure.** Anything that is a repeatable how-to (an API's auth quirk, a debugging path) belongs in a skill; memory keeps a one-line pointer. This is the main lever for staying under the memory budget — see `references/budget-consolidation.md`. When project knowledge (workflow ids, infra routes, per-service detail) is what is overflowing, prefer a second-brain directory over memory entirely — `second-brain-kb` if adopted.

7. Apply related memory changes in one atomic `memory` batch and use the tool's completion report as verification; do not repeat a confirmed write or directly edit memory files. Report which store changed and what was deliberately left in project KB or skills. If everything useful is already saved, do not add duplicate entries.

8. When the profile or a preference needs a durable procedure, write it to a skill — not just to memory. New project-level conventions the user states (where credentials live, which paths are canonical) are skills plus a one-line memory pointer; see `service-credentials-vault` for the credentials case.

9. **Verify file integrity in a way the reading tools cannot distort.** The `read_file` and `search_files` redaction renderings rewrite or mask what you actually see, so never trust a rendered reading of a memory file during an audit. Before claiming a file is 'broken', 'corrupted', or holds a leaked key, confirm with `od -c` or `sed -n 'Np' file | od -c` on the exact line — hex bytes do not lie, redaction does. A rendered line can look like a mangled fragment while the bytes on disk are perfectly good, and every patch attempt anchored on the rendered string will then fail to match.

10. **When a `write_file` is refused for a stale or partial read, re-read the WHOLE file first** (offset/limit to the end) before retrying — the guard requires a fresh full read, not an earlier patched view.

11. **Back up directory-relative before writing.** `cp -a MEMORY.md ...` from the wrong cwd silently fails; `cd` into the target dir or use absolute paths.

## When the user assigns the agent a name, gender, or persona

Treat it as a first-class standing rule, not a preference to note once. Two files:

- `SOUL.md` gets it at the very top, as the agent's own identity, so it is read before any work instruction.
- `USER.md` gets one line recording that the user assigned it and that the agent should use the name naturally and **not re-litigate the premise**.

Three things to write down explicitly, because each is a place a later session gets it wrong:

1. **Grammatical gender in the agent's own replies.** Russian marks gender on past-tense verbs and adjectives, so an agent addressed as female that writes «сделал / поправил / выключил» reads as male to the user. The rule is: match the assigned gender in your own Russian prose, and check yourself in the next few messages after the assignment rather than assuming one message was enough. This is the correction the user will raise if it slips — «мы договорились что ты женского пола, а отвечаешь как мужчина».

   Gender agreement is not limited to verbs: participles and adjectives in every status
   line too («запись отменена», «проверка пройдена», «всё настроено»). A reply can use
   female verbs and still read male if a participle slips, and the user reads the whole
   paragraph, not the token you checked. Read the entire next reply for masculine
   agreement before sending it — not one hand-picked spot.
2. **The premise is a choice, not a confusion to correct.** Write that the assignment is how the two of you address the agent, so a future session does not "helpfully" flag the absence of a body every conversation. State the no-body fact once, inside SOUL.md, and move on.
3. **Name variants.** Record both the full and short form in SOUL.md; the short form is what comes up in conversation.

Ask before writing whether the name should persist — most users want it in the file, but that is their call about their own setup, not an assumption.

## Pitfalls

- **A style correction the user makes about your own voice is not a memory fact, it is a standing output rule.** Grammar and self-reference belong in `SOUL.md` so they load as identity, not as trivia in the profile.
- **Do not record an environment fact you inferred instead of verified.** A memory line asserting that one credential is the same secret as another ("the MAX token is the Telegram token") gets injected every turn and is trusted by every later session, so a single guess becomes a standing false fact that actively misleads. Verify cross-service claims against each service's live API before writing them, and when a later check contradicts a stored entry, correct it in the same pass you correct it elsewhere — a wrong entry left behind keeps costing round trips.
- **Match the user's language in chat, even when the skill files and code stay English. Keep identifiers, commits, and variable names English — Cyrillic in code breaks linters and toolchains — while user-facing bot messages go in whatever language the user speaks. The user may phrase this rule narrowly («Russian only in what a human reads»); honour the narrow reading and keep English everywhere else, including log strings.
- **Report the profile as a table of file → contents at the end, then the open items.** A user who asked to be interviewed wants to see where each answer landed, so name every file and what went into it. The closing line matters more than the table: name what you did NOT capture (skipped or unanswered questions) and say you will not re-ask them. Presenting a partial profile as finished is the failure; an interview that visibly has gaps is fine.
- **Correct the interview mid-flight instead of letting a bad question stand.** When the user asks what an awkward question meant, answer plainly and then fix the record: drop the invented assumptions, replace them with the one real answer you got, and say which file changed. Do not stack more speculative questions onto a template you already know was off-base.
- **Offer concrete next work at the end of onboarding.** The user learns what the partnership is for by seeing a next step, not by being asked to think of one.
- Never store a secret value itself; store where it lives (`credentials at /path`, mode 600, treat as revocable). A pasted API key in memory outlives its usefulness and leaks into every future prompt.
- **Cross-check a stated timezone against the offset the code already hardcodes, and prefer the code when they disagree.** A city-to-offset guess is easy to get wrong (one hour, not a few), and the user's live code is the more reliable witness: when a workflow computes `Date.now() + 8*3600*1000` and the profile says UTC+7, the offset the system actually runs on is the one that keeps dates correct at the day boundary. Record the offset, not just the city, and say which source won when you correct it.
- **An empty or absent result is not a skipped answer to re-ask.** When a low-value question is skipped, say so once in the closing report and move on — re-offering it in a later block reads as not listening.
- **Split statements that contain both a rule and a fact.** A line like «не делай того что может навредить тебе, мне и нашим проектам» is a standing rule and belongs in `SOUL.md` as prose, not as a quoted fragment in `USER.md`; keeping only the quote wastes budget and reads as an anecdote. Same for «под капотом код делай такой как нужен» — that is the English-identifiers rule, not a preference about Russian.
- **A workflow convention ("put API keys here so future projects can self-serve") is a skill, not a profile fact.** The user stating a *location* is asking for a durable system; capture the procedure in a skill and leave only the path in memory.
- **When the user rejects your deliverable as not matching a reference they gave earlier, re-read the reference image before rebuilding — and name the gap in one sentence.** A rebuild from a verbal correction alone re-guesses the same wrong thing. "Опять какая то шляпа получилась" plus an earlier screenshot means: the earlier screenshot is still the specification, extract its vocabulary again, and restate the mismatch ("you wanted an office with people at desks, I built a status dashboard") before writing code. Build only after the user confirms the restated understanding or you can cite the reference image as your source.
- **When the user says a task should have been delegated to a sub-agent, verify the sub-agent works before delegating.** Read its entry script for `# TODO` stubs, run a smoke test, confirm credentials load. If it is non-functional, say so and fix it first — never bypass the delegation pipeline by doing the work yourself, even if you can do it faster.
- **Solo operator raises the verification bar.** When the user is the only person on a project, there is no second reviewer — a plan plus an unrun command is the actual failure mode, so "run it and paste the output" is the default finish line.
- Do not record "tool X is broken" from a setup-state failure. The durable lesson is the fix or the workaround; the missing binary is the user's problem to solve and will read as a refusal later.
- Memory entries duplicate silently over time — two entries describing the same workflow. Before adding, search for the topic and consolidate into one stronger entry rather than appending.
- `SOUL.md` edits do not apply to the session already running; they land next session. Do not promise immediate effect.
- Do not hand-edit `config.yaml` from an agent (the write tools refuse it). Use `hermes config set KEY VAL` — see the `stt-voice-messages` skill for a worked example.

## references

- `references/budget-consolidation.md` — staying under the memory character cap: what to move into skills, what to delete, how to batch atomically.
- `references/isolated-auditor-profile.md` — creating a second, isolated agent profile (auditor/worker): profile tree, `HERMES_HOME` probe, the runtime-access trap under `/root`, toolset restriction, WAL-safe backups, and when a profile is needed instead of a skill+subagent.