# Turning one workflow into a niche template

A working bot is a product. The job: produce a second workflow, identical in
behaviour, carrying a different niche — persona, username, knowledge base —
without ever touching the production original.

## Procedure

1. **Back up first, work on the copy.** Fetch the live workflow to a timestamped
   file under the backups directory and treat it as read-only. Nothing here
   writes to the instance; the deliverable is a JSON the user imports.
2. **Patch BOTH node lists.** A fetched workflow carries `nodes` and
   `activeVersion.nodes`, and the snapshot is what the trigger executes. Write
   one `_patch_nodes(nodes, cfg, changes)` helper and call it on each list, or
   the stale snapshot keeps serving the old niche.
3. **Replace the persona in both fields of the agent node.** The standing rules
   live in `parameters.options.systemMessage`; the per-run prompt lives in
   `parameters.text` and carries the context placeholders. Replacing one leaves
   the other niche's text live. Keep the placeholders
   (`{{ $json.context }}`, `{{ $json.question }}`) in the replacement text —
   they are what binds the retrieved knowledge base into the prompt.
4. **Replace every hardcoded identity inside code nodes.** The mention/reply
   filter carries the bot username as a literal; grep `jsCode` for it and
   substitute from config. Bump the memory `sessionKey` suffix in the same pass
   so conversations from the old niche do not bleed into the new one.
5. **Strip the read-only envelope before import:** `id`, `active`,
   `activeVersionId`, `versionId`, `versionCounter`, `createdAt`, `updatedAt`,
   `triggerCount`, `isArchived`, `pinData`, `staticData`, `tags`, `meta`,
   `shared`. Credential references (`credentials.<type>.id` / `.name`) must
   SURVIVE — they are what makes the copy exercise the real accounts.
6. **Guard with a fingerprint list.** Define the source niche's marker words and
   refuse to write the output while any of them survives anywhere in the
   serialized body. Scan the whole JSON, not per node — the leak is usually in a
   field nobody was thinking about.
7. **Verify before handing it over:** node count matches the source, credential
   references preserved, agent prompt placeholders present, guard clean. Report
   those four numbers, then prove the production original is untouched by
   re-reading it and showing `active` and `updatedAt` unchanged.

## Pitfalls

- **`activeVersion.nodes` is the copy that runs.** Patching only `nodes`
  produces a workflow that still carries the original persona in the live
  snapshot, and the import reports no error. Diff the two lists before and
  after every patch run.
- **The agent's prompt is two fields, not one.** `options.systemMessage` holds
  the standing rules, `parameters.text` holds the per-run prompt with the
  context placeholders. A patch that touches one ships the other niche's text
  to the client.
- **A node object is a dict — comparing it to a name string never matches, and
  it fails silently.** `for node in wf["nodes"]: if node == "AI Agent"` does
  nothing and reports no error; index `node["name"]`. When a patch "applies"
  but the changes list comes back empty, suspect the selector before the
  payload.
- **A guard that fires is evidence, not a false positive.** Locate the surviving
  words in the serialized body before weakening the list — the first firing
  found both a missed field and a second copy of the graph. Only drop a word
  after proving it belongs to every persona of the target niche.
- **Dropping the context placeholders disconnects the knowledge base** from the
  agent: the bot answers from model priors alone and every status is still
  green. Assert the placeholders are present in the built file.
- **Credentials are references, so a template inherits the owner's accounts.**
  Say plainly that the imported copy will act with the same Telegram/OpenRouter
  bindings as the original, and that the client's own credentials must replace
  them before it goes live.
