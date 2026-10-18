"""Collect run summaries and audits into ../RESULTS.md."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for d in sorted(glob.glob(os.path.join(HERE, "runs", "p*_t10_*"))):
    if not os.path.exists(os.path.join(d, "summary.json")):
        continue
    s = json.load(open(os.path.join(d, "summary.json")))
    a = {}
    if os.path.exists(os.path.join(d, "audit.json")):
        a = json.load(open(os.path.join(d, "audit.json")))
    if s["status"] == "UNSAT":
        ok = a.get("drat_trim") == "VERIFIED" and a.get("lrat_trim") == "VERIFIED"
        st = "independently verified (DRAT+LRAT)" if ok else ("audit FAILED" if a else "tested (audit pending)")
    elif s["status"] == "WITNESS":
        st = "WITNESS FOUND"
    else:
        st = "inconclusive (limit)"
    rows.append((s["p"], -s["k"], s, st))
rows.sort(key=lambda r: (-r[0], r[1]))
out = ["# Results: σ-invariant (3,10,40)-graphs, by cycle type of σ\n",
       "Degree bounds 4 ≤ deg ≤ 9 (unconditional). UNSAT means no (3,10,40)-graph has an",
       "automorphism of this cycle type. See docs/02-symmetry-program.md.\n",
       "| p | k (p-cycles) | f (fixed) | outcome | status | orbit vars | α-cuts | solve s |",
       "| --- | --- | --- | --- | --- | --- | --- | --- |"]
for p, _, s, st in rows:
    out.append(f"| {p} | {s['k']} | {s['f']} | {s['status']} | {st} | {s['edge_vars']} | {s['cuts']} | {s['seconds']} |")
open(os.path.join(HERE, "..", "RESULTS.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
