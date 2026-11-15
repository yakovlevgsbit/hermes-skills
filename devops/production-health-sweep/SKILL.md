---
name: production-health-sweep
description: "Use when asked whether everything still works on the server."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [production, healthcheck, systemd, nginx, docker, bots, cron]
    related_skills: [qa-agent-production-suites, docker-management, web-code-delegation]
---

# Production health sweep

## When to use

«проверь всё», «всё работает в штатном режиме», a check after a deploy, before a
client demo, or any request that means "walk the box and report". The deliverable is
a verdict plus the real tool output behind it — every service, every public route,
every bot, every scheduled job — not a sample.

This user's systems are production for real clients. Assume nothing is fine because
`systemctl is-active` says `active`; a service can be restarting cleanly into a
failure, and a route can return 200 while rendering an empty page.

## Sweep order

Batch each step into one command; feed the output into the report as you go.

1. **Box.** `date -Is`, `uptime`, `df -h /`, `free -m`, `systemctl --failed`.
2. **Units.** List running custom units, then for each one:
   `systemctl show -p ActiveState,NRestarts,ExecMainStartTimestamp --value <u>`.
   A four- or five-digit restart count is a crash loop, not a healthy service.
3. **Journals.** `journalctl -u <u> --since '24 hours ago' -p err --no-pager -q | wc -l`
   per unit. Zero is the pass condition; anything else needs the actual lines.
4. **Ports.** `ss -ltnp` for listeners, then `ps -o args= -p <pid>` to map each
   port to the process that owns it. Do not infer the owner from the port number
   or from a doc.
5. **Public routes.** Read the proxy config *from inside the container* — the
   host copy is often absent or stale:
   `docker exec <nginx> grep -nE 'server_name|location|proxy_pass|root ' /etc/nginx/conf.d/*.conf`
   Then curl every declared route and print `%{http_code} %{time_total}`. The
   config is the contract; paths you invented are not.
6. **5xx triage.** `docker logs --since 10m <nginx> | grep -E '<route>'`.
   Read the message, not just the code: `rewrite or internal redirection cycle`
   is a config/file problem, not an application crash.
7. **Bots.** Telegram: `getMe` per token. MAX: `GET https://botapi.max.ru/me` with
   an `Authorization` header. Print the returned bot name and compare it with the
   product the token is supposed to serve.
8. **Automation.** Hermes cron `jobs.json` (`enabled`, `last_status`, `last_run_at`),
   root crontab, n8n `/api/v1/workflows` (active flags) and
   `/api/v1/executions?limit=250` (failure count, newest timestamp).
9. **Data.** sqlite `PRAGMA integrity_check`; Supabase
   `/rest/v1/<table>?select=id&limit=1` with `Prefer: count=exact` and read
   `Content-Range`.
10. **Durability.** Newest file in the backup directory, and certificate expiry:
    `echo | openssl s_client -servername <host> -connect <host>:443 2>/dev/null | openssl x509 -noout -dates`.

## Pitfalls that cost real time

- **Static site content lives in the container layer, not a volume.** Recreating
  the proxy container wipes deployed sites while the sources on disk stay intact.
  Symptom: a route that used to serve pages returns 5xx although `location` and
  `root` look right. Compare the container's html tree against the project's
  `sites/`/`static/` directories before debugging the config.
- **A missing file behind `try_files $uri $uri/ /path/index.html` is a 500, not a
  404** — the internal redirect re-enters the same location and loops. Fix by
  restoring the file, and say in the report that the container has no volume for
  it, otherwise it recurs on the next recreation.
- **`error.log` in a stock nginx image is a symlink to stderr.** Opening it with
the file tool returns nothing and shell readers stall on it; use `docker logs`
instead.
- **A failed distro unit beside a working container is noise.** `nginx.service`
  fails with `bind() to 0.0.0.0:80 failed (98: Address already in use)` because
  docker owns the port. `systemctl disable` + `mask` + `reset-failed`, or every
  later sweep re-reports it as breakage.
- **A process that is not a unit dies on reboot.** `pgrep -af <name>` finding a
  bot with no matching `systemctl cat` means it was started by hand: create the
  unit, `enable --now`, kill the manual PID, then confirm exactly one process is
  polling (two would fight over the same long-poll).
- **Crash loops hide in `NRestarts` and log growth**, not in the active state. A
  demo bot sat in `activating` for weeks at a six-figure restart count, writing
  megabytes per day of an identical `ModuleNotFoundError` traceback.
- **401 from a bot API can be the auth channel, not the token.** MAX rejects
  `?access_token=` with `verify.token … deprecated`; the header form works.
- **Leftover headless browsers outlive their deleted binaries** after a playwright
  upgrade and keep a port plus ~100 MB: `ps -eo pid,etime,rss,args | grep chrome`.

## Fixing during the sweep

Restoring something that is already broken and additive — copying missing static
files, enabling a unit, masking a duplicate, killing a stale process — is part of
the sweep. Anything that changes behaviour, spends money, or removes data gets a
numbered proposal and a wait, per the standing rule about production writes.

After any fix, re-run the affected checks and re-state the verdict; do not report
"fixed" from a successful command alone.

## Report shape

1. Verdict in the first two sentences: what was broken, what was fixed, whether
the rest is clean.
2. A table of surfaces: route or service → status, so the user can scan it.
3. A short "not breakage" list — gated routes answering 401, empty demo data,
   demos deliberately switched off. This prevents the next sweep from re-raising
   them as findings.
4. What was NOT verified, named explicitly (e.g. message-level bot behaviour that
   needs a real inbound message).
