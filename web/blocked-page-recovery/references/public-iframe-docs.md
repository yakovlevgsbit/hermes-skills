# Public documentation inside iframe wrappers

Use when a canonical public page loads but its top-level body is empty. Check the page structure before calling it blocked, missing, or login-only. A public Sign In button does not by itself mean the documentation requires authentication.

## Recovery

1. Navigate to the canonical URL, wait, and inspect iframe src values. Preserve the relationship between the canonical page and the observed child URL; never invent a mirror host.
2. A nested same-origin documentation iframe may expose a public static index.html URL. Fetch that observed URL directly when possible, and record both canonical and fetched URLs.
3. Page.getFrameTree can omit an out-of-process frame. Enumerate Target.getTargets, select the exact public iframe URL, and attach with Target.attachToTarget using flatten=true. The Browser Use helper accepts the returned session through cdp(..., session_id=sid).
4. Wait for the child's actual content, not only the outer document load event. Assert the expected page identity and a meaningful text marker; an empty early snapshot is not a negative finding.
5. If direct CDP return handling does not expose the child's value reliably, evaluate a read-only public-DOM capture in that target and send it to a temporary listener on the canonical parent. Check event.origin and a task-specific message marker. This is a local browser observation, not a network upload; use it only for public documents, never to evade authentication or inspect an unauthorized private frame.
6. Detach only the session created by the probe. Save canonical URL, sanitized frame origin/path, text, retrieval method and time. Do not copy transient RPC fragments, cookies, authorization values or login state into reports.

Keep innerText (visible content) separate from textContent (which can include collapsed FAQ answers and style text). If using textContent, label that method and quote only the relevant published wording. Product FAQ claims are not measurements of the user's account, quota or privacy settings.

For a proven instance of this pattern see the public-document evidence described in `/root/kb/projects/stitch-skills.md`. No service login or generation API is needed to read those notices.
