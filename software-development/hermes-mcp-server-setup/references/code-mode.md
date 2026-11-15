# Code Mode and tool-context reduction

Use when a large MCP catalog or repeated model round-trips makes a workflow expensive. Research and source links: `/root/kb/projects/cloudflare-code-mode.md`. Recheck the installed SDK and server before implementation; do not install a bridge merely because a video recommends one.

## Distinguish the mechanisms

- MCP is the connectivity/discovery/call contract. Programmatic orchestration can use MCP; it does not replace the protocol.
- Progressive disclosure keeps the full catalog outside model context and reveals selected operations/types on demand.
- Code execution composes dependent calls, filters, pagination and aggregations without returning every intermediate value to the model.
- A single code tool that embeds every TypeScript definition can still have a large prompt. A small tool count does not prove a small schema footprint.
- Separate host-side/client-side wrapping from server-side Code Mode. The server-side pattern can expose discovery and execution to an ordinary MCP client without a client sandbox.

## Choose the existing path first

1. Use ordinary tools for a single operation or when the next step needs the user's decision.
2. Use `tool_search` and `tool_describe` for deferred catalogs; when the exact name is listed, describe it directly. Treat a lexical search miss as a reason to broaden the query, not proof the capability is absent.
3. Use `execute_code` for three or more supported tool calls with mechanical logic between them. Aggregate/deduplicate in code, save complete evidence in files, and print only necessary results and failure counts.
4. Check actual `hermes_tools` exports. The documented built-in set is web_search, web_extract, read_file, write_file, search_files, patch and foreground terminal. Do not assume arbitrary MCP tools or `tool_call` are importable.
5. Only consider a new MCP/OpenAPI connector/runtime after an approved pilot shows that existing discovery and execution are insufficient. Do not bypass the normal approval dispatcher with a direct credentialed client just to batch calls.

## Verify benchmark claims

- State what was counted: raw OpenAPI, full tool schemas, minimal schemas, selected types, generated code, tool output, or total task tokens.
- Cloudflare's approximately 1.17M-to-1K claim is a published static-description comparison, not proof that arbitrary workflows cost 1K tokens or are 1000x faster.
- Count live or source-registered tools for the version under review. Do not repeat a video's or README table's total when a newer tool list disagrees. Separate the two core functions, search/execute, from auxiliary docs/identity tools.
- Compare the same task and acceptance criteria. Measure model rounds and backend API calls separately: fewer model turns does not eliminate HTTP requests or rate limits.
- Record latency, retries, correctness and complete result counts as well as tokens. Never present arithmetic on vendor numbers as an independent runtime benchmark.

## Security and side effects

- Run untrusted generated code only in a real restricted executor. A simple eval, AsyncFunction or Node VM is not a secure sandbox.
- Keep credentials on the host/supervisor and expose narrowly authorized callable bindings. Inspect effective outbound destinations and tool-returned sensitive data; hidden auth credentials do not make every API response safe.
- A sandbox can still invoke destructive functions that its bindings permit. Enforce per-operation policy, least-privilege credentials, account/project scope, budgets and approvals at the host boundary.
- Cloudflare's execution tool is write-capable/destructive. Do not mark a generic execute wrapper read-only because a particular current script only reads.
- Preserve an audit log of every underlying operation. Avoid treating approval of an opaque outer code block as unlimited approval for all later internal writes.
- Check SDK approval semantics: connector/runtime approvals and legacy createCodeTool filtering of needsApproval tools are different mechanisms.
- Before production writes, back up and present the exact plan. Read back every external target before reporting success.
- A multi-call program is not a transaction. Return succeeded, failed, uncertain and unstarted operations separately; do not retry an entire write batch after a timeout. Resolve uncertain outcomes by readback.
- Stop on ambiguous entity matches and ask the user instead of selecting the first result.

## Bounded execution and data completeness

- Limit concurrency, calls, time, input/output size and pagination. Retain cursor, has_more and declared totals until verified complete.
- Save full batches as files; aggregate by stable IDs in Python/JavaScript. Large Git trees should be saved first, then filtered to non-generated relevant paths before printing.
- Distinguish empty results, unavailable services, truncated results and partial failures.
- Returning a summary reduces LLM context, not the need for source evidence. Include source IDs/paths and counts so the agent can inspect details.
- Do not disable server-side truncation unless the client bounds the data presented to the model and has a plan for large results.
- Match executor guarantees to the runtime. Hermes Python/RPC execution and Cloudflare Dynamic Worker isolates are not interchangeable security boundaries.

## Pilot acceptance

Use read-only synthetic or approved non-sensitive inputs first. Require parity with direct calls on output completeness; successful paging/dedup; useful error reporting; no unauthorized internal operation; measured model/API counts; correct handling of timeouts; and safe cancellation. Add writes only after those pass with an approved scope and rollback/readback strategy.

## Primary references

- https://blog.cloudflare.com/code-mode-mcp/
- https://github.com/cloudflare/mcp/blob/main/src/server.ts
- https://github.com/cloudflare/mcp/blob/main/src/tools/execute.ts
- https://github.com/cloudflare/agents/tree/main/packages/codemode
- https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution
- https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
