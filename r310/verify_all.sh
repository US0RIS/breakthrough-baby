#!/bin/bash
# Re-verify every certificate from scratch: regenerate the CNF with the
# independent auditor, refute it with CaDiCaL, check DRAT and LRAT proofs.
# usage: SAT_TOOLS=/dir r310/verify_all.sh   (run r310/build_tools.sh first)
set -e
cd "$(dirname "$0")"
for c in ../certificates/*/; do
  w=$(mktemp -d); cp "$c/summary.json" "$w/"; gunzip -c "$c/cutsets.txt.gz" > "$w/cutsets.txt"
  echo "$(basename $c): $(python3 audit.py "$w")"; rm -rf "$w"
done
for c in "7 1 33" "7 2 26" "7 3 19" "5 1 35" "5 2 30" "5 3 25" "3 1 37" "3 2 34" "3 3 31" "2 1 38" "2 2 36"; do
  python3 audit_quotient.py $c
done
