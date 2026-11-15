# Evaluating reconstruction and cloning tools

Use for tools that study websites/apps/games, delegate code generation and compare the result with the reference. `/root/kb/projects/craft-anything.md` records one source-backed evaluation.

- Separate the inspection engine, coding agent and verifier. Open-source orchestration does not include free model access or prove every builder works.
- Distinguish visible-reference reconstruction from deep source/binary inspection. Use only targets and materials the user is authorized to analyze; do not assume a tool's license covers copied text, photos, code or trademarks.
- Read status/limitations alongside the README. Record live-tested backends separately from adapters tested only against stand-ins.
- Inspect the real adapter arguments and compare them to the installed agent's help without executing a generation. Matching flags prove only the CLI shape, not end-to-end compatibility.
- Do not confuse a clean-room policy with OS sandboxing. The external builder and dependency installers retain their own privileges and need an isolated workspace with restricted secrets and network access.
- Separate source-build requirements from native-release requirements; users do not need a Rust compiler merely to run every prebuilt Rust binary.
- Preserve the workflow that transfers: capture evidence and acceptance criteria, build separately, test multiple viewports and interaction states, report discrepancies, then refine within a budget.
- Do not certify functionality from visual similarity. Forms, navigation, storage and payments require their own behavior tests.
- Treat logos and bundled media licenses independently from MIT/Apache source code. Fork branding restrictions can survive permissive code licensing.
- On an approved pilot, use one owned fixture, compare against the existing builder on the same acceptance criteria, and measure cost/time/manual corrections. Do not replace production based on a successful demo or doctor command alone.
