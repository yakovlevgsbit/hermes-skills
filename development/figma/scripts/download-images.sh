#!/usr/bin/env bash
# Downloads Figma image renders to /tmp/figma-images/ in parallel.
# Usage: bash download-images.sh <name> <url> [<name> <url> ...]
#
# Example:
#   bash download-images.sh frame-01 "https://..." frame-02 "https://..."

set -euo pipefail

FIGMA_TMP="/tmp/figma-images"

if [[ $# -lt 2 ]] || (( $# % 2 != 0 )); then
  echo "Usage: $0 <name> <url> [<name> <url> ...]" >&2
  exit 1
fi

mkdir -p "$FIGMA_TMP"

pids=()
while [[ $# -ge 2 ]]; do
  name="$1"
  url="$2"
  curl -sS -o "$FIGMA_TMP/${name}.png" "$url" &
  pids+=($!)
  shift 2
done

for pid in "${pids[@]}"; do
  wait "$pid"
done

echo "Saved to $FIGMA_TMP:"
ls -lh "$FIGMA_TMP"
