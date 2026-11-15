# Adapting foreign (Claude-Code-era) skills for Hermes

Recipes for porting third-party agent skills into this environment. Distilled
from adapting gstack, ui-ux-pro-max, and VoltAgent subagents.

## Tool-name rewrites that always apply

| Claude Code | Hermes |
|---|---|
| `Read` tool | `read_file` |
| `Write` tool | `write_file` |
| `Edit` tool | `patch` |
| `Bash` tool | `terminal` |
| `Grep` / `Glob` | `search_files` (target='content' / 'files') |
| `Agent` tool | `delegate_task` |
| `AskUserQuestion` | `clarify` (one question per call, options as choices) |
| `WebFetch` / `WebSearch` | `web_extract` / `web_search` |
| `TodoWrite` | `todo_list` |

Also: `CLAUDE.md` → `AGENTS.md`; `~/.claude/skills/...` paths → the Hermes
skill path; `.claude-plugin/` manifests → drop.

## What to strip from adapted prompts

- JSON "communication protocol" blocks calling a context-manager service that
  does not exist in Hermes.
- "Integration with other agents" blocks naming Claude sibling agents.
- Fenced JSON `status`/`progress` examples carrying invented metrics — they read
  as templates and invite a subagent to fabricate numbers in its report.
- Capability claims the subagent cannot keep: a `delegate_task` child has no
  browser, no Chrome MCP, no Computer Use. Rewrite "screenshot the page" into
  "work from the source files; ask the orchestrator for page evidence" and state
  the limitation outright, or the agent will invent visual observations.

## Engine porting checklist

1. Copy the engine scripts + data; skip CLI wrappers, galleries, screenshots.
2. Confirm the engine is stdlib-only (`grep '^import \|^from '` and reject
   anything outside the stdlib unless it is already installed).
3. Run the project's own validator if it has one (`validate_data.py` style) —
   it catches corrupted copies.
4. Test from the destination path, several modes: main output, JSON mode,
   persistence, error path, `--help`.
5. Write SKILL.md last, from the observed `--help` and real output — flag names
   and behaviour come from the tool, not from the README.
6. Record attribution (upstream, license, what changed) in each file header and
   in `/root/kb/projects/`.

## When a repo is a fork of a renamed upstream

Check `parent` in the GitHub API response. A fork of a renamed project points at
dead URLs in its README and issues, and the canonical repo may be far more
alive (15k stars vs 200). Vet the parent, not the fork the user pasted.
