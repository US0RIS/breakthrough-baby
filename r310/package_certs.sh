#!/bin/bash
# Copy every independently verified UNSAT case into certificates/ (gzipped cut sets + summaries).
cd "$(dirname "$0")"
mkdir -p ../certificates
for d in runs/p*_t10_*; do
  [ -f "$d/audit.json" ] || continue
  grep -q '"lrat_trim": "VERIFIED"' "$d/audit.json" && grep -q '"drat_trim": "VERIFIED"' "$d/audit.json" || continue
  name=$(basename "$d"); out="../certificates/$name"; mkdir -p "$out"
  cp "$d/summary.json" "$d/audit.json" "$out/"
  gzip -9 -c "$d/cutsets.txt" > "$out/cutsets.txt.gz"
done
ls ../certificates
