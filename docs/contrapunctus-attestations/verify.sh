#!/bin/sh
# Verify every attestation record in this directory against its signature.
# Each record R.txt must have a detached signature R.txt.sig. The signer
# principal is the record's `signer:` field and must appear in allowed_signers.
# Namespace is fixed to `contrapunctus` so signatures cannot be replayed.
set -eu
cd "$(dirname "$0")"
NS=contrapunctus
AS=allowed_signers
[ -f "$AS" ] || { echo "no allowed_signers file"; exit 1; }
n=0; ok=0; bad=0
for rec in *.txt; do
  [ -e "$rec" ] || continue          # no records yet: the glob stays literal
  case "$rec" in *.sig) continue ;; esac
  sig="$rec.sig"
  n=$((n + 1))
  if [ ! -e "$sig" ]; then
    echo "FAIL  $rec  (no signature $sig)"; bad=$((bad + 1)); continue
  fi
  signer=$(sed -n 's/^signer:[[:space:]]*//p' "$rec" | head -1)
  if [ -z "$signer" ]; then
    echo "FAIL  $rec  (no signer: field)"; bad=$((bad + 1)); continue
  fi
  if ssh-keygen -Y verify -f "$AS" -I "$signer" -n "$NS" -s "$sig" < "$rec" >/dev/null 2>&1; then
    echo "ok    $rec  ($signer)"; ok=$((ok + 1))
  else
    echo "FAIL  $rec  ($signer)"; bad=$((bad + 1))
  fi
done
echo "---"
echo "$n records: $ok ok, $bad failed"
[ "$bad" -eq 0 ]
