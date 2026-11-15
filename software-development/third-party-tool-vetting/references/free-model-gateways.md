# Vetting free-model gateways

Use for keyless model plugins, free API routers and subscription bridges. The research note `/root/kb/projects/dsh-our-free-model.md` is an example, not permission to install or use a provider.

## Identify the actual service

- Trace prompts, tool outputs and images to their actual upstream destinations. A local OpenAI-compatible listener is not local inference.
- Separate anonymous free pools, paid/BYOK providers, account-login channels and contributor/sponsor lanes. Do not apply one lane's no-signup claim to the whole product.
- Read both the plugin's disclaimer and the upstream provider's current terms. An official free tier can restrict permitted clients, geography, trial purpose or sensitive data.
- Do not implement client-fingerprint or identity-rotation workarounds to defeat eligibility or quota limits. Prefer the approved client or an explicitly supported API plan.

## Check packaging and dependencies

- Verify canonical repository, publisher, scoped package name, version and release provenance before copying an install command. A same-named unscoped npm package can be an unrelated repackaging; attribute such warnings to the publisher unless independently verified.
- Inspect manifests and native helpers rather than repeating zero-dependencies badges. Plugin host peer dependencies, standalone UI builds and Bun/native transport requirements are separate costs.
- Check code and vendored licenses. A software license does not grant permission to use an upstream service or its quota by any method.

## Inspect trust boundaries

- Preserve caller instructions and verify tool-call round trips. Some proxies inject their own system context, rename tools, compact tool results or silently change models; they are not transparent transports.
- Inspect authentication and bind address separately for local API, management UI and optional LAN relay. A loopback main listener does not prove every surface is local or protected.
- Verify conversation-ID handling before multi-user use. Missing identifiers can collapse requests into a shared upstream session or cache.
- Keep API credentials, customer conversations, private source and secret-bearing tool output out of free pools whose logging/training terms do not permit that workload.
- Distinguish local usage telemetry from prompt egress. Local statistics do not mean prompts stay on the machine.

## Evaluate reliability honestly

- Separate model-list probes, offline fixtures and actual generation tests. A successful listing or one PONG is not evidence of reliable streaming, tools, long context or production capacity.
- Treat 403 eligibility/region refusals and 429 quotas as constraints, not an instruction to rotate identities or bypass checks.
- Treat documented quota/latency/empty-response failures as findings even when the headline says unlimited.
- Compare with the user's existing provider registry before suggesting another proxy. Distinguish configured routes from freshly tested availability and cost.
- Keep study tasks read-only. If a pilot is authorized, use non-sensitive synthetic inputs, explicit provider terms, bounded calls and no production configuration changes.

## Sources to consult

- Canonical package README/manifest and outbound adapter source.
- Upstream privacy, free-tier and permitted-client documentation.
- The user's existing `/root/kb/ops/llm-providers.md`.
