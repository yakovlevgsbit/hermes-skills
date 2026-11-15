---
name: qa-agent-production-suites
description: "Use when QA-ing live production surfaces and APIs."
version: 1.0.0
author: Hermes Agent (Мария)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [qa, testing, production, api, security]
    related_skills: [dogfood, web-app-change-verification]
---

# QA-Agent: testing production surfaces

## When to use

Checking a live panel/API/bot still works, or hunting for regressions and
auth holes in a shipped product. Complements `dogfood` (which drives a browser
against a web page) — this skill is for **HTTP/API surfaces** plus the
orchestration pattern that makes QA reproducible.

## The core rule: pin the REAL surface, not your idea of it

Before writing a single assertion, probe the live service and record the actual
response. Guessing endpoints, ports or status codes produces tests that fail for
the wrong reason and teach you nothing.

```bash
# probe first, always — record status + content-type + body head
for p in / /healthz /api/stock; do
  printf "%-14s -> " "$p"
  curl -s -o /tmp/r -w "%{http_code} " "https://host$p"
  head -c 80 /tmp/r; echo
done
```

## Pick the interpreter that has the deps

`python3` in PATH may be a bundled agent python WITHOUT `requests`. Detect and
fall back:

```python
PYTHON_CANDIDATES = ["/usr/bin/python3", "/usr/bin/python3.12", "python3"]
def pick_python():
    for cand in PYTHON_CANDIDATES:
        r = subprocess.run([cand, "-c", "import requests"], capture_output=True)
        if r.returncode == 0:
            return cand
    return sys.executable
```

A runner that silently uses the wrong interpreter turns every test into
`ModuleNotFoundError` — looks like a code bug, is actually an environment bug.

## Separate the modules from the tests

A shared HTTP client (`helpers.py`, `api_client.py`) sitting in the tests dir gets
run as a test and passes vacuously. Exclude by name:

```python
NON_TEST_MODULES = {"helpers.py", "api_client.py"}
files = [f for f in glob("api-tests/*.py") if os.path.basename(f) not in NON_TEST_MODULES]
```

## Browser tests cannot run from a subprocess

The `browser_exec` helpers (`new_tab`, `js`, `fill_input`, `capture_screenshot`)
exist ONLY inside that tool's context. Running a browser test via
`subprocess.run([python, "browser_test.py"])` fails with
`ModuleNotFoundError: No module named 'browser_exec'`. Keep browser scenarios
in a separate directory and drive them through the tool; keep HTTP/API scenarios
subprocess-runnable. Do not write an orchestrator that pretends otherwise.

## Status 200 is not proof of a working API

A reverse proxy often serves the web UI for ANY path — `/workflows`,
`/executions` and `/` all return 200 with an HTML shell. Verify the
`Content-Type` is JSON before trusting a 200, or you will report "API works"
when it does not.

## Split expectations into buckets — and never tune a test to go green

The trap: a test that flags a DESIGNED-public endpoint as a leak. You then
"fix" the app and break it, or soften the test and hide the real hole.

Bucket explicitly:

- `MUST_BE_GATED` — an anonymous 200 here is a real leak (e.g. a proxy that
  speaks to the DB with a service-role key).
- `DESIGNED_PUBLIC` — open on purpose (boot data rendered before auth). Assert
  it is REACHABLE; if it silently stops being reachable the app broke, so the
  test must fail.
- `OPEN_OK` — health checks.

If a test fails, first ask "is the expectation wrong or the system wrong?".
Prove it against the live service before editing either one.

## Auth-check the proxy, not just the routes

The highest-value finding is usually a **catch-all proxy** (e.g.
`/api/supabase/**`) that forwards to the database with a privileged key and
carries no actor check. Gating inside the proxy handler covers every verb;
gating at each call site is easy to miss one. Verify with a minted signed
request (should be 200) AND an anonymous one (should be 403).

## Verify a signature format empirically, don't assume it

When minting a test signature, try the variants and check the validator's
return value directly. Signing-string construction is easy to get subtly wrong
(param quoting, which params are included) and then the GATE looks broken when
it is fine. Load the app's own validator function and call it in-process before
blaming production.

## Report honestly

Exit non-zero on failure, write JSON + HTML reports, and name what was verified
vs. what is still unknown. Never mark a check as passing because it is convenient.
