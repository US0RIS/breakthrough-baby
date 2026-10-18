"""Cube-and-conquer for cycle types with many fixed points.

Cover argument. Let G be a sigma-invariant (3,10,40)-graph with moving part
H = G[M]. The normalizer elements that act on M only (cycle swaps,
rotations, multipliers; all fix F pointwise) map G to another
sigma-invariant (3,10,40)-graph, so G may be replaced by one whose H is the
lex-leader H0 enumerated in quotient.py. If H0 is killed by the quotient
bound, no G exists. Otherwise H0 is a cube: we fix G[M] = H0 by unit
clauses and solve the rest with lex-leader constraints for fixed-point
transpositions only. Those act on F alone and leave G[M] unchanged, so they
are compatible with the cube. (Mixing in the M-symmetries would compare
different lex orders and could wrongly discard the cube's representative.)

usage: python3 cubes.py p k f [--max-seconds S] [--min-edges E]
"""
import argparse
import json
import os

from quotient import survivors
from search import run
from symenc import SymEncoding

ap = argparse.ArgumentParser()
ap.add_argument("p", type=int)
ap.add_argument("k", type=int)
ap.add_argument("f", type=int)
ap.add_argument("--max-seconds", type=float, default=1800)
ap.add_argument("--min-edges", type=int, default=0)
a = ap.parse_args()

total, surv = survivors(a.p, a.k, a.f)
encm = SymEncoding(a.p, a.k, 0, lo=0, hi=9, symbreak=False)
print(f"{total} moving-part graphs, {len(surv)} cubes", flush=True)
results = []
for cid, trues in enumerate(surv):
    edges = [(u + a.f, v + a.f) for x in trues for (u, v) in encm.var_pairs[x]]
    r = run(a.p, a.k, a.f, cube=edges, cube_id=cid, max_seconds=a.max_seconds,
            min_edges=a.min_edges, quiet=True)
    print(cid, r["status"], r["iterations"], r["cuts"], r["seconds"], flush=True)
    results.append(r["status"])
summary = dict(p=a.p, k=a.k, f=a.f, moving_part_graphs=total, cubes=len(surv),
               cube_status=results, min_edges=a.min_edges,
               status="UNSAT" if all(s == "UNSAT" for s in results) else
               ("WITNESS" if "WITNESS" in results else "INCOMPLETE"))
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs",
                 f"cubes_p{a.p}_k{a.k}_f{a.f}" + (f"_e{a.min_edges}" if a.min_edges else ""))
os.makedirs(d, exist_ok=True)
json.dump(summary, open(os.path.join(d, "summary.json"), "w"), indent=1)
print(json.dumps(summary))
