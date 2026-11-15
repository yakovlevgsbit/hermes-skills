#!/usr/bin/env python3
"""Adapt gstack's review specialists into Hermes-native reference files.

Source: https://github.com/garrytan/gstack (MIT, Garry Tan)
  review/specialists/*.md, review/checklist.md, review/sections/adversarial.md,
  review/sections/review-army.md, ETHOS.md, agents-digest/gstack-AGENTS.md

Adaptations:
  - gstack bin helpers (gstack-diff-scope, gstack-specialist-stats,
    gstack-gate-diff, gstack-review-log, gstack-decision-search) -> plain git
    commands or removed; they do not exist on a Hermes box.
  - Claude tool names -> Hermes tool names.
  - gstack-specific markers (gstack-shortcut(dec-*), /test-audit) -> generic
    wording, since the ledger those reference is not installed here.
  - Path references to ~/.claude/skills/gstack/... -> dropped.
"""
import os
import re
import pathlib

SRC = "/root/work/gstack"
DST = "/root/.hermes/skills/software-development/adversarial-code-review/references"
SPEC_DST = os.path.join(DST, "specialists")

TOOL_REWRITES = [
    (r"`Read` tool", "`read_file`"),
    (r"\bRead tool\b", "`read_file`"),
    (r"\bGrep tool\b", "`search_files`"),
    (r"\bGlob tool\b", "`search_files(target='files')`"),
    (r"\bBash tool\b", "`terminal`"),
    (r"\bWrite tool\b", "`write_file`"),
    (r"\bEdit tool\b", "`patch`"),
    (r"native Read calls", "`read_file` calls"),
    (r"Use Grep to find", "Use `search_files` to find"),
    (r"`Agent` tool", "`delegate_task`"),
    (r"the Agent tool", "`delegate_task`"),
]

DROP_PATTERNS = [
    r"~/.claude/skills/gstack/[^\s`]*",
    r"gstack-shortcut\(dec-\*\)",
    r"`gstack-decision-search`",
    r"gstack-decision-search",
    r"`gstack-specialist-stats`",
    r"gstack-specialist-stats",
    r"`gstack-gate-diff`",
    r"gstack-gate-diff",
    r"`gstack-review-log`[^\n]*",
    r"`gstack-diff-scope`[^\n]*",
    r"`gstack-config`[^\n]*",
    r"`gstack-brain-sync`[^\n]*",
    r"gstack-brain-sync",
    r"`/test-audit`",
    r"/test-audit",
    r"`GSTACK_[A-Z_]+`[^\n]*",
    r"GSTACK_[A-Z_]+",
    r"`gstack-[a-z-]+`",
]


def adapt(text, drop_gstack_bits=True):
    for pat, rep in TOOL_REWRITES:
        text = re.sub(pat, rep, text)
    if drop_gstack_bits:
        for pat in DROP_PATTERNS:
            text = re.sub(pat, "", text)
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # tidy artifacts left by removals
    text = text.replace("  ,", ",").replace(" ,", ",")
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"the  ledger", "the ledger", text)
    text = re.sub(r"\bthe\s+\.\s*", "", text)
    return text.strip() + "\n"


HEADER = """<!--
Adapted from gstack by Garry Tan — https://github.com/garrytan/gstack (MIT License).
Adaptations for Hermes: gstack bin helpers and the decision ledger are not
installed here, so those references were removed; Claude tool names were mapped
to Hermes tools. Methodology unchanged.
-->
"""


def main():
    pathlib.Path(SPEC_DST).mkdir(parents=True, exist_ok=True)

    written = []
    # specialists
    for f in sorted(os.listdir(os.path.join(SRC, "review/specialists"))):
        if not f.endswith(".md"):
            continue
        raw = open(os.path.join(SRC, "review/specialists", f), encoding="utf-8").read()
        out = HEADER + adapt(raw)
        path = os.path.join(SPEC_DST, f)
        open(path, "w", encoding="utf-8").write(out)
        written.append(("specialists/" + f, len(out)))

    # design checklist (frontend lens)
    src = os.path.join(SRC, "review/design-checklist.md")
    if os.path.exists(src):
        out = HEADER + adapt(open(src, encoding="utf-8").read())
        open(os.path.join(SPEC_DST, "design.md"), "w", encoding="utf-8").write(out)
        written.append(("specialists/design.md", len(out)))

    # core two-pass checklist
    out = HEADER + adapt(open(os.path.join(SRC, "review/checklist.md"), encoding="utf-8").read())
    open(os.path.join(DST, "core-checklist.md"), "w", encoding="utf-8").write(out)
    written.append(("core-checklist.md", len(out)))

    for name, size in written:
        print(f"  {name:<34} {size:>6} bytes")
    print(f"\ntotal: {len(written)} files -> {DST}")


if __name__ == "__main__":
    main()
