# Probing an MCP Endpoint Without an MCP Client

Use this when you need to know whether an endpoint is alive, which protocol versions it speaks, and what it demands — before writing a client or configuring Hermes.

## Minimal handshake

StreamableHTTP servers accept JSON-RPC POSTs. A bare `initialize` is enough to learn the server identity and supported protocol revisions:

```bash
curl -s -X POST "https://host/api/mcp/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}'
```

A reply naming `serverInfo` means the endpoint is live and the version is accepted. An error listing `supported` protocol versions tells you exactly which revisions to try.

## Strict servers demand extra headers and `_meta`

Modern servers reject a plain handshake with header/param errors, in a fixed order. Add them one at a time — each error names the next missing piece:

| Error | Fix |
|---|---|
| `Header mismatch: MCP-Protocol-Version header is required` | add `-H "MCP-Protocol-Version: <version>"` |
| `Header mismatch: Mcp-Method header is required` | add `-H "Mcp-Method: <method>"` (echo the method being called, e.g. `tools/list`) |
| `Invalid params: _meta is required` | add `"_meta": {}` to `params` |
| `Invalid params: _meta.io.modelcontextprotocol/protocolVersion is required` | add `"_meta": {"io.modelcontextprotocol/protocolVersion": "<version>"}` |
| `Invalid params: _meta.io.modelcontextprotocol/clientCapabilities is required` | add `"io.modelcontextprotocol/clientCapabilities": {}` |
| `Invalid params: _meta.io.modelcontextprotocol/clientInfo is required` | add `"io.modelcontextprotocol/clientInfo": {"name": "...", "version": "..."}` |

`GET` on the same path returns `405 Only POST is supported` — that confirms the endpoint exists and is an MCP transport rather than a static file.

## Diagnosing an `invalid_token`

Test three things before concluding a key is bad:

1. **Same key, every plausible host.** Services with regional domains (`service.cc` vs `service.ru`) often issue keys valid on only one. A key rejected on one host can work verbatim on the other.
2. **A deliberately fake key.** If the fake key returns the identical error, the server is rejecting the request at the token layer — the diagnostic value is in confirming the rejection path is real, not in the fake key itself.
3. **The response headers.** `www-authenticate: Bearer realm="...", error="invalid_token"` names the realm and confirms the server reached token validation.

Only after the key authenticates on the correct host do you have a working setup — otherwise you are debugging the wrong layer.
