# Delivering a single-page app as a Tilda block, and as a hybrid

Use when a self-contained learning/trainer/quiz app must reach users who cannot
reach your own VPS, while a server-backed mode stays switchable without a
rebuild. Tilda specifics live in the `tilda-agent` skill (user-owned); this file
covers the app-side shape that any block host shares.

## Build the static block

1. **One `<script>` per source file.** Concatenating several IIFE files into one
tag throws `Identifier '$' has already been declared`. Data goes first, then
core libs, then the app, in the app's original load order.
2. **Ship the DOM the app expects inside the block** — the `#app` mount point and
   any chrome the app decorates. Missing mount = empty shell with no error.
3. **Reject `</script` anywhere in inlined sources**; a stray occurrence silently
   truncates the block.
4. **Assert content size at build time** ("48 lessons / 144 tasks") so a
   partially regenerated bundle fails the build rather than shipping.
5. **Test inside a page wrapper**, not standalone `file://`:
   `<body><div class="t-container">BLOCK</div></body>` under Playwright.
   Standalone rendering hides container and cascade breakage.
6. **Assert zero network calls** in that run. A trainer that quietly fetches an
   API is broken for exactly the audience this delivery exists for.

## Hybrid: static first, server optional

```js
// '' = pure static, '/' = same-origin API, 'https://host' = cross-origin API
window.HYBRID_CONFIG = { remoteOrigin: '' };
```

The runtime shims only the calls the app makes, returning an honest
`ai_disabled`/`offline` JSON body when no API is configured so the app renders
its normal "not available" state instead of throwing. Every account/sync call
goes through one wrapper that converts a network rejection into
`{ok:false, body:{message:…}}` — an unhandled rejection from a blocked sync is
what makes the whole course look broken.

- **`localStorage` progress is the source of truth**; sync is an explicit
  push/pull. Never auto-overwrite non-empty local progress on boot.
- **Update account state from the API response, not from a reload** — login
  returns the email; write it into local state and repaint, or the UI keeps
  saying "offline" after a successful signup.
- **Validate only the envelope server-side** (`schema_version`, `tasks` is a dict,
  bounded size) and store the payload verbatim; validating app-owned fields
  couples the server to every future client change.

## Cookie flags for cross-origin auth from a hosted page

`SameSite=None; Secure` is required for a page on one origin calling an API on
another, and it is only honoured over **HTTPS**. Over plain HTTP the browser drops
the cookie: login returns 200 while every following request is anonymous. Test the
full flow against a local HTTPS harness (self-signed cert + `ignoreHTTPSErrors`),
never over HTTP.

A same-origin browser POST still sends `Origin`, so an allow-list must accept your
own origin and return matching `Access-Control-Allow-Origin` + `-Credentials`.

## Hosting reality checks

- A block host cannot run Python, hold a secret, or sync devices. Do not promise
  accounts or an LLM chat on the static build.
- If the API host is unreachable from the user's network, keep the account
  backend behind the `remoteOrigin` flag. Enabling it removes the only working
  path the user has.
- Verify the delivered URL as a visitor: open a lesson, answer a question, read
  the feedback, reload, confirm progress survived.
