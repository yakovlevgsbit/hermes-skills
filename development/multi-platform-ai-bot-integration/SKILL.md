---
name: multi-platform-ai-bot-integration
description: "Use when building a multi-platform AI bot."
version: 1.0.0
license: MIT
platforms: [linux]
author: Hermes Agent
metadata:
  hermes:
    tags: [max, telegram, ai-bot, payments, media, webhooks]
---

# Multi-platform AI bot integration

## When to Use

Use when one product must serve Telegram and MAX (or another messenger) without duplicating billing and generation logic.

Use this skill when one product must serve Telegram and MAX (or another messenger) without duplicating billing and generation logic.

## Procedure

1. **Inspect the live system before changing it.** Read the current service unit, production logs, provider client, billing schema, platform transport, and reverse-proxy configuration. Identify the exact interpreter and active container-mounted config. Do not assume the host-side config is the one nginx loads.
2. **Back up before every production write.** Copy the files being changed, the live SQLite database before schema migration, the active proxy config, and the systemd unit into `/root/n8n-backups/<project>-<purpose>-<timestamp>/`.
3. **Separate internal identity from platform identity.** Keep one internal `users.id`; map `(platform, external_user_id)` to it in a durable table. Store conversational state in SQLite/DB, not in process memory, so a restart cannot lose a pending email or prompt.
4. **Keep the billing core platform-neutral.** Store `platform` and `external_user_id` with a payment/subscription mapping, preserve amount and grant fields, and use one idempotent ledger. Resolve a webhook by durable contract mapping first, then verified metadata/custom fields, then a controlled fallback.
5. **Build a pipeline per product, not per post.** For social content, the pipeline is content plan → media generation → media published through the platform's media endpoint → native post/attachment → durable status in the content DB. Each platform gets its own `publish_<platform>()` adapter that owns transport (which token, which endpoint, which payload shape) and returns a durable ID back to the content table.
6. **Route providers per capability, not per product.** When the same kind (e.g. image generation) is offered across channels and may swap providers, add a single capability-scoped router module (e.g. `providers/image_router.py`) with three functions: `preflight(required)`, `generate_*`, `edit_*`. Both Telegram and MAX adapters call the router; the router chooses AnyModel vs KIE by env. This keeps platform adapters thin and makes provider rollback a single env var. The router must accept every input shape a caller can hand it (local file path, https URL, data URL) and normalize to the active provider's expected form — AnyModel wants base64 data URLs for image-to-image, KIE wants public URLs and uploads local files itself.
7. **Treat provider capacity as a preflight gate.** Query the live provider balance before charging the bot user. If the balance check fails or is insufficient, do not spend user credits. If the provider fails after charging, refund exactly once.
8. **Make the charge last.** The flow is `select kind → collect prompt → validate → provider preflight → spend user balance → create provider task → poll → deliver artifact`; never charge on a button press before the required prompt or target is valid.
9. **Deliver media through the destination platform.** A provider URL is not automatically a native messenger attachment. Download it, upload it through the platform's media endpoint, extract the returned token, then send the native attachment. If delivery fails after a successful generation, mark the generation failed and refund.
10. **Use production webhooks for MAX.** Register an HTTPS endpoint on port 443 with a secret, verify `X-Max-Bot-Api-Secret`, deduplicate updates durably, return HTTP 200 quickly, and process provider work asynchronously. Read the subscription back after registration.
11. **Verify both transport and user-visible behavior.** Read the stored message back through the platform API, inspect attachment types and callback/message events, then perform one real user interaction. A successful API response alone does not prove the client rendered the keyboard.
12. **Test without spending money.** Mock provider creation/polling and platform upload/send; assert state transitions, recipient identity, no-spend preflight behavior, exact refund behavior, keyboard payloads, and media attachment construction. Run compile/import tests before restarting production.
13. **Restart and verify.** Restart only after the tests pass; check `systemctl is-active`, recent logs for exceptions, health endpoints, and the platform webhook subscription. Report what was verified and what remains blocked by missing provider balance or user-side action.
14. **Add a provider as a scoped route, not a whole-product replacement.** Keep Telegram, existing KIE paths, billing, and delivery stable; route only the target platform/kind through the new provider until its live balance, endpoint, polling, artifact download, and delivery have passed the same mock and live read-only checks.

## Always-on pitfalls

- **Do not reuse a shared token key when several bots exist.** A valid token for another MAX bot can make health checks pass while sending the product's messages from the wrong account.
- **Use `callback.user.user_id` for MAX button presses.** `message.sender.user_id` is the bot that sent the keyboard, so using it sends the response to the bot or maps the wrong identity.
- **Do not infer client rendering from API storage.** MAX can store an `inline_keyboard` while a particular client fails to display it; test official button types and inspect an actual `message_callback` or `message_created` event.
- **Use `message` buttons when callback rendering is unreliable.** They generate ordinary `message_created` updates and avoid coupling navigation to callback-client behavior; retain callback compatibility when needed.
- **Do not put `user_id` or `chat_id` in the JSON body of MAX `/messages`.** The recipient belongs in the query string, while the body contains message content and attachments.
- **Do not block a webhook on KIE/Lava/media calls.** MAX retries failed or slow deliveries; acknowledge first and run the slow work asynchronously.
- **Do not use a provider URL as the final MAX media attachment.** MAX requires its own upload token, and a successful KIE task is not proof that delivery succeeded.
- **Do not list generation as “connected” while returning a placeholder.** Connect the complete prompt → charge → provider → upload → send path or state the exact missing stage.
- **Do not test a paid provider with the live account when preflight is already insufficient.** Mock the provider and report the live balance; a failed paid request teaches less than a deterministic state-machine test and risks inconsistent billing.
- **Do not overwrite a live proxy config from the wrong mount.** Inspect `nginx -T` inside the running container and patch the active file inside the correct `server` block; otherwise the endpoint may be captured by a different location or authentication layer.
- **Do not switch every platform to a newly added provider at once.** Provider-specific endpoint, billing, and artifact semantics can differ even when the model name looks equivalent; isolate the route and preserve a rollback path.
- **Never hard-code a literal `***` placeholder into a curl Authorization header.** When you build a command list for `subprocess.run`, always substitute the live key from a `_key()` helper at runtime. A literal placeholder returns 401 "Invalid API key" even when the surrounding code looks correct. The display in `read_file`/`grep`/echoes will show `***` for secrets regardless of the actual file content — that is expected redaction, not a bug to "fix" by removing the value.
- **When `patch` keeps failing on a long, multi-branch function, switch to `write_file` of the full module.** Repeated `old_string`/`new_string` matches against complex dispatch functions silently fail on whitespace and exact-string divergence; rewrite the whole file once instead of stacking patches that each touch overlapping regions.
- **A provider router must normalize every input shape the callers can hand it.** Telegram uploads land as local file paths in `data/uploads/`; MAX attachments arrive as `https://` URLs; some flows already pass data URLs. The router decides whether to base64-encode, download, or upload-to-provider-CDN based on the active backend, so adapters can stay format-agnostic.
- **Do not trust a provider's generic chat endpoint for media.** Read the provider's media API docs and use its create → poll → content route; media models often return a misleading model/endpoint error when sent to chat.

## References

- `references/max-production.md` — MAX webhook, identity, buttons, and delivery checklist.
- `references/ai-generation-billing.md` — provider preflight, spend/refund state machine, and media delivery test matrix.
