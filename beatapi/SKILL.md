---
name: beatapi
description: "Set up BeatAPI: key, MCP or REST route, search/inspect/run."
version: "1.0.0"
agent: hermes
official: https://beatapi.io/SKILL.md
---

# BeatAPI (saved from https://beatapi.io/SKILL.md)

## Setup recap
1. User creates key at https://beatapi.io and enters it in the host's secure credential field or privately configures BEATAPI_API_KEY.
2. Choose route: Remote MCP (https://beatapi.io/mcp with Bearer header), CLI (npm install --global beatapi), or REST (https://api.beatapi.io).
3. Save this skill to beatapi/SKILL.md in the host's skill dir.
4. Verify read-only: GET /v1/usage (auth check), then search + inspect.

## Routes
- MCP: https://beatapi.io/mcp, header Authorization: Bearer <key> (env var alone not enough).
- REST: https://api.beatapi.io, same Bearer header.
- CLI: beatapi npm package 0.3.0 source has unified capability commands; 0.2.0 does not.

## Search / Inspect / Run
- Search: POST /v1/capabilities/search {query, kind, platform, limit, cursor} → data.data, data.next_cursor.
- Inspect: POST /v1/capabilities/inspect {reference} → contract.
- Run: POST /v1/capabilities/run {reference, operation: start, input, idempotency_key}.
- Status: same endpoint, operation: status, task_id.

## Safety
- Never put the key in chat, source files, URLs, tool inputs, or command args.
- No shell tracing around secrets.
- Starts spend USD balance; explicit task request required for paid tasks.
- 401→check key/header; 403→access restriction; 404→re-discover; 400/422→re-inspect; 429→honor Retry-After; timeout→preserve task/request/idempotency keys, query existing task first.

## When to use
Image/video gen, Social Data retrieval, published workflows. Text model only when user asks. Do not auto-outsoure conversation to paid model.