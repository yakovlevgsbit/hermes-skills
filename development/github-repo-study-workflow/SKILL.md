---
name: github-repo-study-workflow
description: "Use when studying a GitHub repo and saving as skill."
---

# GitHub Repo Study → Skill → Push Workflow

When Georgy asks to "изучи" (study) a GitHub repo and save it, follow this exact sequence.

## Standard Workflow

### 1. Study the Repository
- Read README, key source files, structure via `web_extract` and `read_file`
- For large repos: read tree structure first, then batch-read key files
- Extract: architecture, key patterns, dependencies, business model

### 2. Save Full Analysis
- Write to `/root/kb/projects/<slug>.md`
- Slug: short kebab-case, e.g. `dewiar-reverse-engineering`, `strix-ai-pentesting`
- Include: full architecture, all modules, patterns, comparison with similar projects

### 3. Create Skill
```
skill_manage(operations=[{
    'action': 'create',
    'name': '<slug>',
    'category': '<category>',
    'content': '---\nname: <slug>\ndescription: "Use when <trigger>."\n---\n\n# <Title>\n\nFull research: `/root/kb/projects/<slug>.md`\n\n<Reusable procedure and verification boundaries>'
}])
```
- Category: `development`, `productivity`, `devops`, `creative`, `payments`, `email`
- Make the first 57 description characters a self-contained trigger; additional detail can follow.
- Prefer extending a relevant existing skill over creating a duplicate. Store reusable procedures, not a research log; link the KB for project-specific findings.

### 4. Copy to Repo
```bash
mkdir -p /root/hermes-skills/<category>
cp -r /root/.hermes/skills/<category>/<slug> /root/hermes-skills/<category>/
```

### 5. Commit only the intended files
Before staging, inspect `git status --short` and any existing staged diff. Update the matching README category row before committing. Stage the exact skill directory and README only; never use `git add -A` in a shared workspace. Commit only this task's files.

Push or copy research to a public repository only when the user requested publication or repository synchronization. Studying a link or saving a local skill is not publication authorization. After an authorized push, verify the remote commit before reporting success.

### 6. Update README
- Add one line to the matching category table in `/root/hermes-skills/README.md` before the scoped commit.
- Use `patch` tool, not full rewrite.

## Variant: the repo is already an Agent Skill

Some repos ship a ready-made skill folder (a `SKILL.md` plus optional scripts, data files, reference documents and tests). For a research-only request, inspect it and record the verdict without activating it. Only when installation is explicitly in scope is the job to install the vetted folder and verify it rather than re-authoring it.

1. Inspect the current installer's supported targets and the actual output. A successful `npx skills add <owner>/<repo>` process can still report `skipped: Hermes Agent (project directory not found)`; verify the destination and discovery rather than inferring success from exit 0. Do not generalize one version's missing target into permanent lack of Hermes support.
2. If manual installation is needed, clone into a new directory under `$TMPDIR` (Hermes scratch) and review the skill before execution. Copy the subfolder containing `SKILL.md` (often `skills/<name>/`, not the repository root) only after checking whether the target already exists. Preserve or back up an existing skill instead of nesting or overwriting it accidentally.
3. Confirm Hermes sees it: `skills_list` must now include `<name>`. Frontmatter needs `name` + `description`.
4. In an authorized installation task, inspect this repository's actual prerequisites and documented self-checks. A text-only skill may need no packages; a skill is not required to have `doctor.py` or Playwright. Run only the verified commands that apply, with bounded resources, and report which checks passed. Do not pre-download heavy models or run a paid API as incidental setup.
5. CLI tools installed under `~/.local/bin` may not be on the tool shell's PATH. Check resolution and use an explicit executable path or a deliberate PATH update. Never replace an existing `/usr/local/bin` executable or symlink with `ln -sf` merely to make lookup convenient.
6. Keep acquisition files in scratch, where they can be pruned normally. Do not delete an existing clone outside scratch as incidental cleanup; it may contain independent work.

## Variant: the repo is a collection of skills

A vendor repo (`anthropics/skills`, marketplaces, `plugins/*/skills/*`) is not one artefact. When studying it:

1. **Inventory every folder, not the README table.** Per skill: file count, total size, `SKILL.md` line count, script count, and whether a `LICENSE` sits in that folder. One row per skill in the KB note.
2. **Read the licence per folder.** A collection can carry no root licence while each skill has its own, and can mix permissive and proprietary entries. A folder without a licence file is unusable — say so and exclude it from the verdict.
3. **Separate the vendor's production skills from its showcase demos.** The skills powering the vendor's own product are far deeper (validators, OOXML handling, eval harnesses); the demos beside them are thin. Weight the verdict by the production half and label each row.
4. **Check what the advertised tooling actually needs.** Eval or benchmark scripts that shell out to a vendor CLI, document skills that need LibreOffice and per-format packages — verify the binary or package exists before recommending the feature. Missing dependency means port the methodology, not the code.
5. **Give a verdict per skill, four buckets:** adopt whole / port the methodology / take one specific file / skip. A repo-wide verdict hides that half the bundle is noise.
6. **Do not create a skill per studied collection.** Extend the skill that already owns the class (design guidance → `claude-design`, repo vetting → `third-party-tool-vetting`) and keep the per-repo findings in the KB note.

## Pitfalls

1. **Weak description prefix** — make the first 57 characters identify the trigger without relying on the rest of a long description.
2. **Repo name ≠ slug** — slug is kebab-case, not the raw repo name. Strip common prefixes.
3. **`write_file` on tokens.env after partial read** — use `patch` for small additions to secrets files.
4. **`hermes config set` for aliases** — must pass JSON object, not separate calls. Separate calls timeout.
5. **`cp -r` of skill to wrong category** — double-check category path before copying.
6. **Skill repo vs skill folder** — when a repo already is an Agent Skill, copy the subfolder containing `SKILL.md` (e.g. `skills/<name>/`), not the repo root; verify this installer's Hermes target and resulting discovery instead of assuming either success or permanent incompatibility.

## Example Repo → Slug Mapping

| Repo | Slug |
|------|------|
| `dwr-git/dewiar-app` | `dewiar-reverse-engineering` |
| `usestrix/strix` | `strix-ai-pentesting` |
| `upstash/context7` | `context7-docs` |
| `Graphify-Labs/graphify` | `graphify-knowledge-graph` |
| `morluto/rea` | `rea-reverse-engineering` |
| `NationalSecurityAgency/ghidra` | `ghidra-reverse-engineering` |