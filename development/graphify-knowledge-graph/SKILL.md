---
name: graphify-knowledge-graph
description: "Use when building queryable knowledge graphs from code."
---

# Graphify — Knowledge Graph from Codebase

GitHub: https://github.com/Graphify-Labs/graphify
Apache-2.0, 124.1k stars. By Safi Safishamsi.

> **Полный разбор**: `/root/kb/projects/graphify-knowledge-graph.md`

## What It Is

Превращает любой codebase в queryable knowledge graph. Типишь `/graphify .` — получаешь:

```
graphify-out/
├── graph.html        — интерактивный граф в браузере (force-directed)
├── GRAPH_REPORT.md   — ключевые концепции, connections, suggested questions
└── graph.json        — полный граф для запросов
```

## Architecture

```
Sources: Code (37 AST grammars) | Docs | PDFs | Images | Video
  ↓
graphify extract (local, no API for code)
  ├─ tree-sitter AST → nodes (functions, classes, imports)
  ├─ edges (calls, imports, inherits, mixes_in)
  ├─ # NOTE:/# WHY: comments → rationale nodes
  ├─ Leiden community detection (no LLM)
  └─ God nodes (most-connected concepts)
  + semantic pass (LLM, optional) for docs/PDFs/images/video
  ↓
graph.json
  nodes: [{id, label, type, file, line, community}]
  edges: [{source, target, type, confidence}]
    confidence: EXTRACTED (explicit) / INFERRED (derived)
  ↓
graphify query / path / explain
```

## Key Concepts

1. **EXTRACTED vs INFERRED** — каждое ребро с confidence tag
2. **God Nodes** — самые коннекченные концепции
3. **Communities (Leiden)** — подсистемы без LLM
4. **Local-first** — tree-sitter для кода, no LLM, no API
5. **Not vector index** — настоящий graph traversal
6. **Confidence tags** — EXTRACTED / INFERRED / AMBIGUOUS

## Commands

```bash
graphify .                      # build graph
graphify update .               # re-extract changed files
graphify query ""    # subgraph
graphify path A B       # shortest path
graphify explain ""     # node context
graphify mcp                     # MCP server
graphify wiki .                 # markdown wiki
graphify obs .                  # Obsidian export
graphify pr . --deep 42         # deep dive on PR #42
graphify merge graph1 graph2     # combine graphs
```

## MCP Tools

query_graph, get_node, get_neighbors, shortest_path, list_prs, get_pr_impact, triage_prs

## Multi-platform (20+)

Claude Code, Codex, Cursor, Gemini CLI, Hermes, OpenClaw, GitHub Copilot, VS Code Copilot, Aider, Windsurf, Devin CLI, Antigravity, Kiro, Factory Droid, Trae, Kimi Code, Amp, Pi, Agent Skills

## Git Hooks

```bash
graphify hook install   # один раз после clone
# git commit → автоматический rebuild (AST only, no API)
# git checkout → автоматический rebuild
# git pull → graphify update .
```

## Benchmarks

| Benchmark | Graphify | Competitors |
|-----------|----------|------------|
| LOCOMO recall@10 | 0.497 | mem0 0.048 |
| LongMemEval-S | 76% | tied dense RAG |
| ERPNext coverage | 82.0% | grep 70.8% |
| LLM credits | 0 | per-token |

## Installation

```bash
uv tool install graphifyy
pipx install graphifyy
graphify install
graphify .  # build graph
```

## Key Patterns

1. **EXTRACTED/INFERRED** — confidence tags on every edge
2. **God nodes** — most-connected concepts
3. **Local-first AST** — tree-sitter, no LLM for code
4. **Not vector index** — real graph traversal
5. **Git hooks auto-rebuild** — always current
6. **Multi-platform skill** — one install, 20+ platforms
7. **Strict mode** — block raw reads, redirect to graph
8. **MCP tools** — structured graph access
9. **Merge driver** — no conflict markers
10. **Business model** — free local, paid platform (app.graphify.com)