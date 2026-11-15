#!/usr/bin/env python3
"""Add gate-integrity catalog + fix leftover artifacts in the adapted refs."""
import os
import re
import pathlib

SRC = "/root/work/gstack/review/gate-integrity.md"
DST = "/root/.hermes/skills/software-development/adversarial-code-review/references"

HEADER = """<!--
Adapted from gstack by Garry Tan — https://github.com/garrytan/gstack (MIT License).
Adaptations for Hermes: the `gstack-gate-diff` tagger and the decision ledger are
not installed here, so detection is manual — read the diff and apply the patterns
below yourself. Methodology unchanged.
-->
"""


def adapt(text):
    # strip gstack tooling references, keep the taxonomy
    text = re.sub(r"`gstack-[a-z-]+`", "the gate scanner", text)
    text = text.replace("emitted by the gate scanner", "read manually from the diff")
    text = re.sub(r"gstack-shortcut\(dec-\*\)[^,.]*", "a decision marker", text)
    text = re.sub(r"`ship-measure`[^\n,.]*", "a measurement report", text)
    text = text.replace("`/review`", "the reviewer").replace("`/ship`", "the shipper")
    text = text.replace("/review", "the reviewer").replace("/ship", "the shipper")
    text = text.replace("gstack's own SKILL.md goldens regenerate on every template edit by design, so RH-3 is\nnever auto-blocked; the PR-body line makes a product snapshot regeneration visible to the human.",
                        "A generated-file golden that regenerates by design is inventory, not a finding.")
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main():
    p = pathlib.Path(DST)
    # 1. gate integrity catalog
    raw = open(SRC, encoding="utf-8").read()
    # keep from the tagged-patterns heading onward; drop the gstack controls table
    start = raw.find("## Tagged patterns")
    body = raw[start:] if start > 0 else raw
    cut = body.find("## Where the controls live")
    if cut > 0:
        body = body[:cut]
    (p / "gate-integrity.md").write_text(HEADER + adapt(body), encoding="utf-8")
    print("  gate-integrity.md written")

    # 2. fix leftovers in already-adapted files
    fixes = [
        (r"The caller's Diff scans step ran\s+and printed its `GATE_SUMMARY:` line plus a read-level listing \(`\[<id>\] <tag> <path> @<hunk>`\)\. The tag definitions below are complete for review; gstack's `review/gate-integrity\.md` documents each pattern's pathology and countermeasure\.",
         "Apply the tagged patterns in `references/gate-integrity.md` by reading the diff yourself — the scanner that normally emits the tags is not installed here."),
        (r"should show both human and CC\+gstack time", "should show both human and AI-assisted time"),
    ]
    for f in list(p.glob("*.md")) + list((p / "specialists").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        o = t
        for pat, rep in fixes:
            t = re.sub(pat, rep, t)
        if t != o:
            f.write_text(t, encoding="utf-8")
            print(f"  fixed {f.name}")


if __name__ == "__main__":
    main()
