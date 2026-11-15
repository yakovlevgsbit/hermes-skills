# Reviewing design-agent skill bundles

Use when a repository joins a hosted design service, local extraction/build helpers, and agent instructions. A skill is neither the hosted model nor a running agent; installing it does not configure credentials, grant project access, or equip a separate code-generation executor.

## Inventory and contracts

Pin a source revision and reconcile actual SKILL.md files with README tables and plugin manifests. Hidden helpers and cross-plugin dependencies matter more than the advertised count. Preserve original names, then check namespaced names and tool references against the chosen host before any authorized adaptation.

Check local name collisions before copying. The name `design-md` can identify a prose-oriented Stitch analyzer or a formal design-token specification workflow; an identical filename does not imply an identical schema.

Trace each producer to its consumer. Verify required YAML keys, section names, project/screen ID shapes, and where tokens belong. Do not combine instructions that both prohibit and require injecting the theme into generation prompts. Choose one authoritative theme route and validate the resulting artifact against the actual consumer.

Preserve extracted source values before proposing normalization. Near-duplicate colors can encode different states; merging them during extraction silently redesigns the source. Distinguish declared styles, rendered styles, inferred roles, and approved design changes.

Keep project state, tokens, client assets, and sync IDs in the project rather than in shared installed-skill resources. A globally overwritten style-guide.json can carry the previous client's settings into the next job.

## Runtime and safety boundaries

Treat static HTML as a captured visual state, not preserved application behavior or a sanitizer. Check scripts, event attributes, network dependencies, sensitive DOM data, and omitted resources separately. A successful file write does not establish offline completeness or visual fidelity.

Review browser sandbox settings, local-file containment, DNS/IP validation and redirect handling before exposing helpers to untrusted inputs. A base directory used for path resolution is not automatically a sandbox. Do not test SSRF against live internal services during desk research.

Use atomic download replacement: write to a new temporary file, validate the result, then replace the target. Error cleanup must not remove a file that predated the current attempt.

Keep secrets out of model-visible commands, argv and logs. Shell expansion of an API key still puts it in argv. Use the agreed credential channel and validate the destination origin. Do not search every other agent's config for a convenient key. Preserve explicit approval of the files and destination before cloud upload.

Distinguish an MCP endpoint from a REST base URL; appending REST paths to an endpoint ending in /mcp is not a valid conversion unless the provider documents it. Authentication, scopes, quota project and token refresh are client-specific; one published OAuth recipe does not establish universal refresh or least-privilege behavior.

## Quality and bounded automation

Read validator implementation rather than trusting labels such as COMPONENT VALID. Parsing an AST and checking a Props interface or some color literals is not type checking, navigation testing, accessibility verification, or a complete app build. In an authorized implementation, test negative fixtures and real interactions separately.

Inspect optional-verification sections even when the opening says every step is mandatory. Keep compile, rendered output, interaction tests and deployment approval explicit in our acceptance contract.

An iteration baton is not a scheduler. Set allowed pages, generation/iteration ceilings, budget and stop conditions; do not let an empty backlog authorize invented pages. A local directory named public is not evidence of deployment.

Treat taste presets as opinions. Preserve brand requirements, readable UI, reduced-motion behavior and real data; do not impose font bans, perpetual animation, or a particular layout on every project.

## Prose-only design bundles

A bundle can be pure markdown with example pages and no code at all. Judge it by measured substance, not by its manifest.

- Count lines and code blocks per file yourself. README totals routinely exclude housekeeping files, so a "7 842 lines / 18 files" claim can coexist with 9 000 lines across 23 files.
- Separate vocabulary files from transferable files. Prose on aesthetics and copy gives you naming and direction; a code-first component file with all interaction states is where the reusable detail lives. Budget the reading accordingly.
- Render the bundle's own examples before trusting its rules. They are the author's demonstration of the rules and often contradict them: a bundle preaching responsive discipline shipped two of four examples with horizontal overflow at a 390px viewport. Prefer the guidance over the samples, and never copy a sample page as a template.
- Check claimed floors against the numbers inside. A document that names WCAG AA as its floor but allows 3:1 for placeholder text contradicts AA, which needs 4.5:1 for anything that is text.
- The transferable artifact is a compressed contract plus a render check, not an installation: condense the scale, the bans and the state list into the engine's prompt, then gate the output on measured layout (see `web-code-delegation`). Installing hundreds of kilobytes of prose into the manager's profile adds context cost without changing what the generator emits.

## Hosted service and license checks

Separate the bundle's code license from the design service, fonts/assets and rendering dependencies. Read the license for the version actually under consideration; an upcoming terms page is not automatically the current contract. Finished-video delivery and transfer of a runnable Remotion codebase can have different licensing implications.

Separate training opt-in from data transfer, human review, feedback context and workspace sharing. Never infer client-data suitability from a permissive GitHub license or a default no-training statement. Start an explicitly authorized pilot with sanitized material and minimal permissions.

For source-backed examples, reviewed scope and the complete module inventory see `/root/kb/projects/stitch-skills.md`. No upstream bundle installation follows from that research note.
