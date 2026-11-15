# Bounded functional-app generation

Use this sequence for an interactive application rather than a one-off visual.
Keep the main skill's delegation, CSP and publication gates in force.

## 1. Fix the contract and the acceptance scope

- Supply the executor with exact data/API shapes, field locations, function signatures, URL prefix and allowed files before generation. Separate frontend acceptance from genuine content coverage and live-service integration; a fixture cannot establish those other gates.
- Keep fixtures under tests and inject them through an explicit test transport. Mark demonstrations visibly and provide a separate traversal command for the genuine release bundle; never overwrite a release data file with a developer fixture.
- Identify one end-to-end tracer flow and its failure cases before dispatch: input, validation, result, navigation and persisted state. Define the saved source, executable check and user-testable preview that constitute the handoff.

## 2. Generate and record complete candidates

- Use the existing engine and credential resolver without modifying provider order or global settings. Keep raw responses, actual model, finish reason and extraction status beside each candidate.
- Validate final content before trusting extraction. A long reasoning trace can contain a tiny example document; `generate_html(...).status == 'ok'` proves neither a final answer nor a working application.
- Split an application into explicitly contracted artifacts, then exercise the tracer flow before commissioning more screens. Do not wait until the whole application has been generated to discover that its DOM factory cannot render a string.

## 3. Review compatibility before integration

- Syntax-check each candidate, then compare signatures, return types and schema paths with its real callers. Valid JavaScript can still change `render(diagram)` into a different API, read root fields instead of `params`, or omit unseen tasks from a total.
- Verify the generated DOM factory in a browser: accept strings, single Nodes and arrays; omit false/null children and false boolean attributes; assign select values after options; avoid uninitialized callback bindings and nonexistent DOM constructors.
- Preserve working markup, styling and functions. Reject an incompatible replacement instead of widening the caller contract merely to accommodate model output.

## 4. Repair only the failed slice

- Send the smallest affected function or exact source region, its caller contract and the failing assertion. Do not resend the entire application to repair one handler; duplicated context and echoed source consume the answer budget.
- Use short unique declaration prefixes as patch boundaries, with the following declaration explicitly excluded. Check those boundaries before applying; a full old function serialized as a boundary is wasteful and prone to truncation.
- Save raw patch responses before parsing. Recover only fully parsed objects or complete functions from an unfinished envelope; never guess missing code or reconstruct an unterminated string. Preserve the original failure/finish status and label salvage separately.
- Drop the full-page response-size floor for genuinely bounded fragments only after structural validation; a correct short repair must not be rejected for being smaller than a landing page.
- Apply concurrent patches in dependency order. Declarations inserted before another patch's end marker expand that patch's range; apply the earlier range first or review recomputed boundaries. Syntax-check and exercise the combined file, not only isolated patches.
- Keep a bounded generation ceiling. After a failed run, inspect its saved output and existing checks before commissioning another attempt; a worker failure is not proof that all persisted work must be replaced.

## 5. Exercise real behavior and geometry

- Use an isolated test dependency environment and discover the browser executable through the selected Playwright installation. Use `PLAYWRIGHT_SKIP_BROWSER_GC=1`, preferably with a project-specific `PLAYWRIGHT_BROWSERS_PATH`, so a browser installation does not delete another project's cache.
- Serve the exact candidate on a free loopback port under the intended URL prefix and strict CSP. Use locator assertions instead of eval-based polling; do not weaken the application's policy for the harness.
- Drive actual controls through valid/invalid input, wrong/correct outcomes, hints or disclosures, retry, navigation, reload, export and confirmed/cancelled reset. Verify unique record counts, not click counts; test storage denial and malformed saved state separately.
- Treat AI/API mocks as explicitly labeled tests. Exercise success, non-2xx and empty responses, quota exhaustion, cancellation and late responses; an unavailable backend must not turn into a fabricated successful conversation.
- Cross each claimed bound in the test fixture: send more turns than the history window, render an over-limit reply, and exceed a quota. A passing example already below the limit does not test enforcement.
- Validate SVG geometry rather than merely finding an `<svg>` element: finite attributes, primitives inside the viewBox, uniform coordinate scale, complete circle/solid extents and meaningful dimension ratios. For interactive diagrams, measure the drawn angle or position as well as the changing label.
- Measure the requested viewport sizes and accessibility states, and preserve screenshots. Keep DOM/layout evidence distinct from visual judgement; do not claim an image review that was not performed.

## 6. Freeze and hand off the verified artifact

- Read back machine reports and check declared totals against their enumerated test cases. Store coverage counts and other informational measurements outside the test-case list so they cannot inflate the pass count. Save the actual command, exit code and hashes of the source that passed; package those bytes, not a later untested working copy.
- Distinguish accepted engine output, recovered complete fragments and bounded integrator corrections in the report. Keep rejected candidates and real failure evidence separate from final acceptance.
- State separately what rendered, what interactions passed, whether real data/API integration was exercised and whether publication occurred. Unverified source-version or content-coverage assumptions remain open even when all fixture UI tests pass.
- For an authorized public preview, copy an allowlisted tested snapshot into separate staging, include only visibly marked demo data when needed, and exclude keys, logs, research originals and test dependencies. Verify the remote HTML/assets against the snapshot and exercise the main flow at the actual URL before delivering a clickable link, expiry and concise test steps.
