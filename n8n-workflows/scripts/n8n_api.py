"""Read-only n8n public-API helper. Key comes from the environment, never a literal.

  export N8N_KEY=<api key>            # user pastes it per session
  export N8N_BASE=https://host.tld/n8n # keep any path prefix

Usage from execute_code:
  import sys; sys.path.insert(0, "/root/.hermes/skills/n8n-workflows/scripts")
  from n8n_api import get, get_workflow, executions, execution

Everything returns parsed JSON or raises RuntimeError with the HTTP status, so a
failed auth never masquerades as an empty result.
"""

import json
import os
import urllib.error
import urllib.request


def _base() -> str:
    base = os.environ.get("N8N_BASE", "").rstrip("/")
    if not base:
        raise RuntimeError("N8N_BASE is not set (include the path prefix, e.g. https://host.tld/n8n)")
    return base


def _key() -> str:
    key = os.environ.get("N8N_KEY", "")
    if not key:
        raise RuntimeError("N8N_KEY is not set — ask the user for it, do not persist it")
    return key


def get(path: str, timeout: int = 60):
    """GET <base><path> with X-N8N-API-KEY; path starts with /api/v1/..."""
    req = urllib.request.Request(_base() + path, headers={"X-N8N-API-KEY": _key()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {exc.code} on {path}: {body}") from exc


def get_workflow(workflow_id: str):
    """Full single workflow: connections + unabridged node parameters."""
    return get(f"/api/v1/workflows/{workflow_id}")


def executions(workflow_id: str | None = None, limit: int = 250, status: str | None = None):
    """Execution summaries, filtered by workflow_id and/or status.

    Project-scoped listing (/api/v1/workflows/<id>/executions) is not reliable on
    every instance: it answers 404 "Version not found". Fall back to the GLOBAL
    list and filter client-side rather than concluding "no executions" — an empty
    result and an unreachable endpoint look identical otherwise.
    """
    q = [f"limit={limit}"]
    if status:
        q.append(f"status={status}")
    rows = get("/api/v1/executions?" + "&".join(q))["data"]
    if workflow_id:
        rows = [r for r in rows if r.get("workflowId") == workflow_id]
    return rows


def execution_counts(limit: int = 100, status: str | None = None):
    """{workflow_id: n} for the retained window — the cheapest health signal.

    Counted client-side over one global call, because the per-workflow endpoint
    is the unreliable one and N round trips is the expensive way to get a sum.
    """
    q = [f"limit={limit}"]
    if status:
        q.append(f"status={status}")
    rows = get("/api/v1/executions?" + "&".join(q))["data"]
    counts: dict = {}
    for r in rows:
        counts[r.get("workflowId")] = counts.get(r.get("workflowId"), 0) + 1
    return counts


def execution(execution_id: int):
    """One execution with runData and error. Dump to disk before parsing if large."""
    data = get(f"/api/v1/executions/{execution_id}?includeData=true")
    return data.get("data") or data


def node_statuses(exec_data: dict) -> dict:
    """{node_name: executionStatus} — the fastest read of where a run stopped."""
    run = (exec_data.get("resultData") or {}).get("runData") or {}
    return {name: runs[0].get("executionStatus") for name, runs in run.items()}


def main() -> None:
    # Smoke test: a 200 here is the only proof the key works.
    print(f"workflows: {len(get('/api/v1/workflows?limit=100').get('data', []))}")


if __name__ == "__main__":
    main()