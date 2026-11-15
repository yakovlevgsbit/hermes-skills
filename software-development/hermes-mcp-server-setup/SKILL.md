---
name: hermes-mcp-server-setup
description: Use when connecting MCP or reducing tool-context costs.
version: 1.1.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, code-mode, tool-discovery, context, security]
    related_skills: [hermes-agent]
---

# Adding an MCP Server to Hermes

## When to Use

Wiring any external service into Hermes over MCP — HTTP/StreamableHTTP or stdio. Use when the user says "connect <service> to Hermes", "add MCP", or when a service offers an MCP endpoint and you need its tools available in chat.

## Code Mode and large catalogs

For MCP token pressure, programmatic composition or Cloudflare Code Mode, read [references/code-mode.md](references/code-mode.md). Distinguish schema discovery from execution batching, verify current tool counts, and retain per-operation approvals. Do not replace working integrations based only on a video benchmark.

## Procedure

1. **Get the exact endpoint and auth scheme.** Probe it before configuring (see `references/mcp-client-protocol-requirements.md` for the raw handshake). Confirm the host — a service may serve different regions/domains with the same key, and only one accepts it.
2. **Configure without exposing credentials.** Check the installed CLI and current MCP config reference. For non-interactive API-token setup, provision the secret through the active profile's secret source, then write only an environment reference (single quotes prevent shell expansion):

```bash
hermes config set mcp_servers.<name>.url 'https://host/api/mcp/'
hermes config set mcp_servers.<name>.headers.Authorization 'Bearer ${SERVICE_API_TOKEN}'
```

Hermes supports `${VAR}` and `${env:VAR}` in MCP entries. Never write a token value into the command, config example, report or repository. For OAuth use the supported login flow rather than treating it as a static bearer token.

3. **Verify with the built-in test before doing anything else.**

```bash
hermes mcp test <name>     # connects, discovers tools, lists them
hermes mcp list           # shows transport + tool count + status
```

4. **Apply using the supported reload path.** Current Hermes documentation provides `/reload-mcp` for MCP configuration changes. A long-lived process may still need a restart after Python dependency-generation changes; distinguish that from a normal server-config reload and agree the production interruption first. Verify discovery in the actual active client; use returned tool names rather than guessing a prefix.

5. **Save a sanitized setup note and preserve scope.** Record paths, endpoint, auth method and verification in the project KB, without secret values. A remote backup or public skills-tap push is a separate action: do it only for an explicitly authorized repository, stage only intended files, and never publish credentials or private transcripts.

## Pitfalls

- **`mcp.client.streamable_http is not available` on an HTTP server is a missing-venv-extra, not a broken SDK.** `hermes doctor` printing `✓ Runtime venv staged (…) (active in this process)` proves nothing about the *gateway*: the gateway is a long-lived process that activates the PM-selected venv **once, at boot**. If `mcp` was absent from that venv (it is an optional extra — `hermes-agent[mcp]` — not a core dep), every HTTP MCP server fails forever until the gateway restarts, even though `hermes mcp list` cheerfully shows `✓ enabled`.

  Diagnose in this order:

  ```bash
  hermes mcp test <name>            # the real acceptance criterion: tools discovered
  hermes doctor | grep -i "Runtime venv"   # which venv THIS process activated
  ```

  Then check the venv the *gateway* actually uses — resolve it from the gateway's own workspace, not from the repo:

  ```bash
  cd "$(hermes gateway status | grep -oE '/root/[^ ]*workspace' | head -1)"
  python3 -c "import sys; sys.path.insert(0,'/root/.hermes/hermes-agent');
  from pathlib import Path
  from pm.environments import committed_venv
  print(committed_venv(Path('.').resolve()))"
  ls "$(that)/lib/python3.14/site-packages/" | grep -c '^mcp'
  ```

  Fix and apply:

  ```bash
  hermes pm install --extra mcp     # syncs mcp into the committed generation
  hermes gateway restart            # only if applying a new Python generation
  hermes mcp test <name>            # must print "Tools discovered: N"
  ```

  `hermes pm doctor` may also report `✗ python: realized bytes do not match recorded digest` — cosmetic here; ignore unless `pm install` itself fails.

- **"requires HTTP transport but mcp.client.streamable_http is not available" usually means the wrong Python ran, not a broken SDK.** The CLI can resolve its interpreter from `PATH` (a bare `/root/.hermes/tools/python-*/bin`) instead of the Hermes venv that actually has `mcp` installed. Confirm which interpreter imports the SDK, then run Hermes with the venv's python first on PATH:

```bash
/root/.hermes/installs/<hash>/environments/<hash>/venv/bin/python3 -c "import mcp.client.streamable_http as m; print(hasattr(m,'streamable_http_client'), hasattr(m,'streamablehttp_client'))"
```

- **Probe the client API of the SDK you actually have before writing a probe script against it.** The MCP SDK renamed its streamable-HTTP client: mcp 1.x shipped `streamablehttp_client` and added `streamable_http_client` (>= 1.24); **mcp 2.0 dropped the old alias**. In 2.0 the signature also changed — there is no `headers=` keyword at all, so build the client with the httpx module the SDK itself imports and pass it via `http_client=`:

  ```python
  import mcp.client.streamable_http as T
  HTTPX = getattr(T, "httpx2", None) or getattr(T, "httpx")   # 2.0 moved to httpx2
  import inspect; print(inspect.signature(T.streamable_http_client))
  client = HTTPX.AsyncClient(headers={...}, timeout=300)
  async with T.streamable_http_client(URL, http_client=client) as streams:
      read, write = streams[0], streams[1]        # 2.0 yields a 2-tuple, not 3
  ```

  Three traps in one call, each with its own error, and the errors do not name the real cause: `cannot import name 'streamablehttp_client'` on a 1.x-only name; `got an unexpected keyword argument 'headers'` on a 2.0-only kwarg; `not enough values to unpack (expected 3, got 2)` on the tuple shape. **Read the signature with `inspect.signature` first** — one line that tells you the client name, the kwarg set and the return arity, and it costs nothing. Two more shape notes for the same call: pydantic models in 2.0 are snake_case, so `tool.input_schema`, not `tool.inputSchema`; and the module the SDK was built against is importable off the transport module (`T.httpx2` or `T.httpx`) — constructing a client from a differently-sourced httpx fails at the transport layer rather than at import.

  Hermes itself already handles this: `tools/mcp_tool.py` binds `streamable_http_client` OR the deprecated `streamablehttp_client`, whichever the installed version exposes. Prefer `hermes mcp test <name>` over hand-rolling any of the above.

- **`hermes config set` on `mcp_servers.<name>.headers.<Header>` works non-interactively** — store a literal SecretRef such as `Bearer ${SERVICE_API_TOKEN}`, never the token value. Ensure the reference resolves in the active profile.

- **A 401/`invalid_token` from an MCP endpoint is not automatically a bad key.** Test the same key against every plausible host/domain of that service first — regional domains often reject keys issued for the main one. Only after the key works on the correct host is it safe to conclude the key is dead.

- **Do not hand-roll an MCP client to test connectivity when `hermes mcp test` exists** — it does the full initialize + `list_tools` and reports the tool count, which is the actual acceptance criterion.

- **Credentials committed to a public repo need revoking, not just deleting.** An API key or token pushed to a git remote is compromised whether or not a later commit removes it — history keeps it. Rotate the credential at the provider, then fix the file. Keep secrets in a gitignored env file and pass them by reference.

## Support Files

- `references/mcp-client-protocol-requirements.md` — what a server's MCP handshake requires, and how to probe an endpoint with curl when you have no MCP client handy.
