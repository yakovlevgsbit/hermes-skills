# Does it fit this box?

Measure a project's real footprint before advising. Registry manifests and
per-service estimates beat any README table — and a measured number is arguable
in a way an adjective is not.

## 1. Read the current state first

```bash
free -h                    # total / used / available
cat /proc/loadavg          # 1m 5m 15m + running/total
nproc
df -h /
docker system df           # images / containers / volumes / build cache
docker ps --format '{{.Names}}\t{{.Image}}'
```

**Check swap before anything else.** Swap already in use means RAM is in deficit.
The production services already running there are the first casualty of any new
memory load — say so explicitly when the numbers are tight.

## 2. Measure image sizes from the registry, not the README

Docker Hub's tag API does not return `full_size` for every namespace — do not
treat a missing field as a small image. Pull and inspect instead:

```bash
docker pull <image>:<tag> >/dev/null 2>&1
docker image inspect <image>:<tag> --format '{{.Size}}'   # bytes
```

For a very large image, read the manifest without downloading layers:

```bash
# Docker Hub
curl -s "https://hub.docker.com/v2/repositories/<ns>/<repo>/tags?name=<tag>"

# GHCR — token, then the index, then the per-arch manifest
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:<ns>/<repo>:pull&service=ghcr.io" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://ghcr.io/v2/<ns>/<repo>/manifests/<tag>" \
  -H "Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.v2+json"
```

A multi-arch manifest is an **index** — it holds no layer sizes. Pick the
`amd64` digest out of `manifests[]`, fetch that manifest, and sum `layers[].size`
for the compressed figure. Multiply by ~2.2 for the on-disk footprint.

Registry filenames vary: `docker-compose.yml` and `docker-compose.yaml` are both
common. List the repo root rather than guessing a path.

## 3. Enumerate services from the compose file

Count the containers — the headline service is rarely the only one.

```bash
grep -nE "^  [a-z_-]+:|image:|shm_size:|cpus|memory:|reservations:|limits:" docker-compose.yaml
```

Per-service idle RAM, for estimating:

| Service | Idle RAM |
|---|---|
| Node/Nest/Next app | 400–600 MB |
| PostgreSQL | 100–200 MB |
| Redis | 20–50 MB |
| Workflow orchestrator (Go, e.g. Temporal) | 200–400 MB |
| Temporal-style web UI | ~100 MB |
| Sentry-style debug sidecar | ~50 MB |
| Elasticsearch (JVM) | **512 MB minimum heap** — it will not start stably below it, and heap is only the Java part |

An orchestrator that drives scheduled/queued work is **load-bearing, not
optional**: removing it silently removes the feature it implements. Say which
feature dies rather than presenting the trimmed stack as equivalent.

## 4. The verdict rule

```
estimated stack RAM + current used  vs  total RAM
```

- Comfortably under: fits.
- Just under, or swap already in use: **fits but tight** — name the production
  service at risk instead of a bare yes.
- Over: does not fit. Do not recommend trimming below the point where a core
  feature stops working.

## 5. GPU is binary

```bash
nvidia-smi            # absent → CUDA/`runtime: nvidia` projects cannot run
ls /dev/nvidia*
```

`runtime: nvidia` in every service, or a README stating all compute is local,
means a CPU-only box is an immediate no — regardless of how good the project is.
There is no partial-credit path here.
