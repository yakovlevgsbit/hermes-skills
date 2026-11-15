---
name: vps-nginx-static-deploy
version: 1.0.0
author: hermes-curator
license: MIT
description: Deploy static sites/demos on the hostkey nginx docker.
metadata:
  hermes:
    tags: [deploy, nginx, docker, vps, landing, demo, static]
    related_skills: [publish-site, web-panel-on-existing-vps]
---

## When to Use
Use when you need to deploy or update a static site, landing page, or client demo
app on the hostkey VPS (openclaw70846.hostkey.in and related routes): auditing what
is live, shipping a file change into the nginx container, editing the vhost, or
verifying demo links before telling the user something shipped.

# Static site deploy on the hostkey nginx docker

The public site (openclaw70846.hostkey.in) and its demo apps are served by ONE docker
container `nginx-nginx-1` (image jonasal/nginx-certbot:6.2.0-nginx1.31.0,
network_mode host). Static content lives INSIDE the container at
`/usr/share/nginx/html/<path>/`. Local sources in /root/<app> are NOT auto-synced —
to ship a change you must copy into the container.

## Audit and prepare the release

1. Fetch the public URL with `terminal` and retain its bytes, final URL, status,
   MIME type and cache headers. Treat the served document as production truth;
   a similarly named host file may be an older, unpublished version.
2. Inspect only the container image and mounts with `docker inspect --format`,
   then read the actual host-mounted vhost with `read_file`. Do not dump the
   full container environment to discover a static route.
3. Create one backup directory under `/root/n8n-backups/`, deriving its timestamp
   once. Use `docker cp` **from container to backup** for the complete affected
   site subtree; separately preserve local sources, the vhost and Compose file.
   Copying only the host source does not back up the site visitors receive.
4. Inventory the snapshot with `search_files` and Python. Save a manifest of
   relative paths, sizes and SHA-256; compare the backed-up index hash with the
   public response. Inventory nested prototypes and other existing pages before
   deciding which files the release may replace.
5. Extract the existing links and check each unique target. Verify redirects,
   MIME type and rendered content as well as status: a 200 login screen is not
   an open demo, and a 200 HTML fallback is not a working robots.txt or sitemap.
6. Build the redesign from the served snapshot in a separate working directory
   within the existing project. Preserve published prices, URLs and unrelated
   subpages. Record which source is canonical instead of silently overwriting
   a divergent local version.
7. Check the nginx location selected for **every new resource path**. An exact
   `location = /portfolio/` matches only the index; it does not establish a
   prefix for sibling stylesheets, fonts or images. Prepare narrow static
   resource and sitemap routes instead of changing the shared root catch-all
   or global robots policy.
8. Validate the local candidate configuration without reloading production;
   use `references/nginx-validation.md`. Test the release over loopback HTTP,
   then provide screenshots and a downloadable preview built from the same
   source, not a separately maintained mockup.

## Approval and deployment

1. **Freeze the approved artifact.** Keep the working version private until the
   required approval; present the tested files and scoped nginx diff. At approval,
   verify the release manifest and source hash instead of rebuilding a potentially
   different page. A public staging upload is also a publication decision.
2. **Take a fresh write-time backup and baseline.** Recheck the current index,
   preserved subpages and vhost against the preparation snapshot; stop and rebase
   on drift. Back up the affected live subtree and only the local mirror files
   that will change, not the entire development tree with dependencies. Record
   sibling-route status/MIME and container ID/StartedAt before the change so old
   failures and actual restarts can be distinguished from deployment regressions.
3. **Stage only manifest entries.** Install fingerprinted dependencies before the
   document, using temporary files and hash checks. Reject an existing fingerprint
   filename with different bytes. Leave the old index active and stage the new
   index on the same filesystem; never copy the whole project or erase prototypes.
4. **Activate routing before the document.** Apply only the approved host-mounted
   vhost patch with `patch`, assert the result matches the inspected candidate,
   then run `docker exec nginx-nginx-1 nginx -t && docker exec nginx-nginx-1 nginx -s reload`.
   Keep HTML non-stale and immutable caching limited to fingerprinted assets.
5. **Prove dependency readiness over public HTTP.** After reload, fetch every new
   resource and the scoped sitemap; compare decoded bytes with the manifest and
   check MIME/cache headers. A file on disk or a successful reload does not prove
   nginx selected its route instead of a catch-all HTML response. Do not switch
   the index until these dependencies are reachable correctly.
6. **Switch with a final drift guard.** Immediately recheck both the old live index
   hash and the pending index hash, then atomically rename the pending file into
   place. Refuse an intervening edit rather than overwriting it with the release.
7. **Verify the public release, not another copy.** Read back every manifest URL,
   canonical redirect and security/cache headers. For gzip, compare the decoded
   body hash and retain compressed wire size separately. Reuse a browser suite
   with a configurable origin for preview and public HTTPS; keep its reports
   separate. Check preserved subpages byte-for-byte and compare sibling health
   with the baseline, reporting pre-existing failures rather than claiming every
   neighbour is healthy. Verify container identity/start time when claiming no
   restart; the HTTP recipe is in `references/nginx-validation.md`.
8. **Synchronize and record only after a pass.** Update the generated local mirror
   from the verified release, retain a distinct canonical source, and record the
   live URL, release manifest, fresh backup and verification results. Mark older
   preparation reports as historical so a later session does not apply the same
   routing patch twice or mistake a published release for an unapproved draft.
9. **Guard rollback as well as deployment.** Restore the old index only if the
   current one is still the release being rolled back. Reverse only the scoped
   routing change after checking for newer config edits; never restore an old
   whole vhost over another application's work. Keep harmless fingerprinted
   assets and prototypes so already-open clients retain their dependencies.

## Diagnosing "the site is unreachable" before changing anything

Isolate layers in this order and stop at the first failing one. Reporting "blocked" without the layer is how a DNS problem gets mistaken for a firewall.

1. **DNS**: `dig +short @8.8.8.8`, `@1.1.1.1`, `@77.88.8.8`, `@9.9.9.9` AND the zone's authoritative nameservers (`dig +short <zone> NS`, then query each NS directly). Identical answers everywhere = DNS is correct, go to layer 2. A user's `nslookup` citing "non-authoritative answer" with the right IP is also correct — that flag does not mean stale.
2. **Port reachability**: raw TCP to 80 and 443 (`cat </dev/null >/dev/tcp/<ip>/443`). Timeout on both ports while HTTPS+HTTP both listen locally means packets never arrive.
3. **From the user's network vs from elsewhere** — this is the decisive test. `check-host.net` gives a third-party vantage point without needing the user's machine:
   ```bash
   curl -s -H 'Accept: application/json' \
     'https://check-host.net/check-tcp?host=IP:443&node=ru1.node.check-host.net&node=ru2.node.check-host.net&node=nl1.node.check-host.net'
   # → {"request_id": "..."}  then poll:
   curl -s -H 'Accept: application/json' https://check-host.net/check-result/<request_id>
   ```
   Different verdicts per node (one node times out, another connects in 5 ms) PROVES per-network filtering by IP/AS, not a server fault. `check-host.net/nodes/hosts` lists every node so you can pick the right country.
4. **Certificate**: `openssl s_client -connect IP:443 -servername HOST -verify_return_error` must print `Verify return code: 0 (ok)`. A valid cert rules out expiry/SNI problems.

When the answer is "filtered for this IP but fine elsewhere", the fix is a different front door (own domain behind a CDN proxy), not a server change. Say so plainly and do not rewrite working config hoping a reload helps.

**Curl and Playwright from the server cannot reach the public hostname.** Many hosts lack hairpin NAT, so `curl https://<public-host>/` hangs even though the site is up. Always test with `curl --resolve <host>:443:127.0.0.1 https://<host>/...` and give Playwright `--host-resolver-rules=MAP <host> 127.0.0.1`. A timeout here is the test harness, never evidence the deploy failed.

## Pitfalls
- Verify the target files, not just the presence of a `location` block: a
  configured static route can point at an absent directory or index.
- Diagnose a 500 from the selected location and nginx error log, not from the
  status alone. A missing index behind a `try_files` fallback can cause an
  internal-redirection cycle; a refused proxy connection commonly yields 502.
  Inspect listening ports only after establishing that the route is proxied.
- Check security-header inheritance when adding location-level `add_header`.
  Under nginx's default inheritance, adding a local Cache-Control header can
  suppress server-level HSTS and other headers. Preserve the intended headers
  explicitly in the scoped change and verify the actual HTTP response.
- Respect nginx's exact-match and longest-prefix selection rules; moving a
  static prefix above the root proxy is not what makes it match. Diagnose the
  scoped route without stopping services used by neighbouring applications.
- For proxy apps with cache-busted bundles, edit source in the app repository
  and rebuild; do not hand-edit generated minified files.
- **Neighbour regression must be a before/after diff, not a memory of "looked fine".** Snapshot every route's status, MIME and body hash in a JSON baseline before the vhost edit, re-probe after the reload, and diff. Pre-existing oddities (a `/` that answers 302 because it proxies to another app with a login redirect) show up as differences against an older baseline — check that file's timestamp before blaming the deploy. Report the diff verbatim; "all neighbours fine" without the rows is not evidence.

See references/site-map.md for the endpoint → backend port map.

When a self-contained single-page app has to reach users who cannot reach this
host — bundling it into one block for an external page host, keeping a
server-backed mode behind a config flag, and the cookie/origin rules for the
account layer — see `references/tilda-block-and-hybrid-delivery.md`.
