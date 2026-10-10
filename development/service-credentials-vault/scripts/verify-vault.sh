#!/usr/bin/env bash
# Audit a secrets vault: modes, inventory, leftover artifacts.
# Read-only: never prints a secret value, only key NAMES.
# Usage: verify-vault.sh [VAULT_PATH]   (default: /root/.secrets)
set -uo pipefail
VAULT="${1:-${SECRETS_VAULT:-/root/.secrets}}"

echo "== vault perms"
stat -c '%a %n' "$VAULT" 2>/dev/null || { echo "MISSING: $VAULT"; exit 1; }

echo "== contents"
find "$VAULT" -maxdepth 1 -type f -printf '%m %s %f\n' | sort -k3

echo "== mode violations (expect none: dirs 700, files 600)"
find "$VAULT" -maxdepth 1 \( -type f ! -perm 600 -o -type d ! -perm 700 \) -printf '%m %p\n'
find "$VAULT" -maxdepth 1 \( -type f ! -perm 600 -o -type d ! -perm 700 \) -printf '' | grep -q . \
  && echo "FIX: chmod 700 $VAULT; chmod 600 $VAULT/*" || echo "ok"

echo "== env keys declared (names only)"
for f in "$VAULT"/*.env; do
  [ -e "$f" ] || continue
  n=$(grep -c '^[A-Z_][A-Z0-9_]*=' "$f" 2>/dev/null)
  echo "$(basename "$f"): $n key(s)"
  [ "$n" -gt 0 ] || echo "  note: empty file — future sessions will assume the credential exists"
done

echo "== leftover signing artifacts (expect none)"
find "$VAULT" -maxdepth 1 -type f \( -name '.*' -o -name '*.sig' -o -name '*.jwt' -o -name '*.out' -o -name '*.pem' \) \
  -printf '%p\n' | grep . && echo "FIX: shred -u them" || echo "ok"

echo "== json key sanity (fields only, no values)"
for f in "$VAULT"/*.json; do
  [ -e "$f" ] || continue
  python3 -c "
import json,sys
try:
    d=json.load(open('$f'))
    print('$(basename $f): valid JSON, type=%s, keys=%s' % (d.get('type','n/a'), ','.join(sorted(d))))
except Exception as e:
    print('$(basename $f): INVALID —', e)
" 2>/dev/null
done

echo "== stray credentials outside the vault"
for p in /root/.hermes/.env /root/.hermes/cache/scratch; do
  [ -e "$p" ] && echo "check by hand: $p"
done
echo "done — liveness of each credential still requires a real API call"