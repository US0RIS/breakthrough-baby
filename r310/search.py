"""Lazy (CEGAR) SAT search for sigma-invariant (3, t, n)-graphs.

usage: python3 search.py p k f [--t 10] [--lo 4] [--hi 9] [--max-iter N]

Outcomes, written to runs/<tag>/:
  WITNESS   graph6 of a triangle-free graph with alpha < t (re-verified);
  UNSAT     final CNF (base + all cuts) for independent proof checking;
  LIMIT     iteration limit reached; nothing is claimed.
"""
import argparse
import json
import os
import time

from pysat.solvers import Solver

from graphs import alpha, alpha_bruteforce, dom_violations, find_indep, to_g6, triangle_free
from symenc import SymEncoding


def write_cnf(path, nvars, clauses):
    with open(path, "w") as fh:
        fh.write(f"p cnf {nvars} {len(clauses)}\n")
        for cl in clauses:
            fh.write(" ".join(map(str, cl)) + " 0\n")


def run(p, k, f, t=10, lo=4, hi=9, max_iter=10**7, per_model=64, seeds=4, symbreak=True,
        solver_name="cadical153", outdir=None, quiet=False, max_seconds=None, min_edges=0, cube=None, cube_id=None, dom=0, nonindep=None, lazydom=0):
    if cube is not None:
        symbreak = "fixed"
    enc = SymEncoding(p, k, f, lo, hi, symbreak, min_edges, dom, t, nonindep)
    if cube is not None:
        enc.fix_moving_part(cube)
    tag = f"p{p}_k{k}_f{f}_t{t}_lo{lo}_hi{hi}" + ("" if symbreak else "_nosb") + (f"_e{min_edges}" if min_edges else "") + (f"_cube{cube_id}" if cube is not None else "") + (f"_dom{dom}" if dom else "") + (f"_ni{nonindep}" if nonindep is not None else "") + (f"_ld{lazydom}" if lazydom else "")
    outdir = outdir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", tag)
    os.makedirs(outdir, exist_ok=True)
    cuts, seen, cutsets = [], set(), []
    domsets, domseen = [], set()
    t0 = time.time()
    status = "LIMIT"
    witness = None
    with Solver(name=solver_name, bootstrap_with=enc.clauses) as s:
        it = 0
        while it < max_iter:
            if max_seconds and time.time() - t0 > max_seconds:
                break
            it += 1
            if not s.solve():
                status = "UNSAT"
                break
            adj = enc.graph(s.get_model())
            new = 0
            for sd in range(seeds):
                for S in find_indep(adj, t, per_model, seed=1 + sd + 7919 * it):
                    cl = enc.cut(S)
                    key = tuple(cl)
                    if key not in seen:
                        seen.add(key)
                        cuts.append(cl)
                        cutsets.append(S)
                        s.add_clause(cl)
                        new += 1
                if sd == 0 and new == 0:
                    break
            if new and lazydom:
                # Ramsey-aware lazy cuts: independent s-set S with |N(S)| < need
                for sz in range(2, lazydom + 1):
                    need = enc.n - sz - enc.M_UPPER[t - 1 - sz]
                    if need <= 0:
                        continue
                    for S in dom_violations(adj, sz, need, maxout=40):
                        key = enc.orbit_key(S)
                        if key in domseen:
                            continue
                        domseen.add(key)
                        start = len(enc.clauses)
                        enc.add_domination_set(list(key), need)
                        for cl in enc.clauses[start:]:
                            s.add_clause(cl)
                        domsets.append((need, list(key)))
            if new == 0:
                # no independent t-set found by the complete search
                assert triangle_free(adj)
                assert alpha(adj) < t
                assert not alpha_bruteforce(adj, t)
                witness = adj
                status = "WITNESS"
                break
            if not quiet and it % 200 == 0:
                print(f"[{tag}] iter {it} cuts {len(cuts)} {time.time()-t0:.1f}s", flush=True)
    elapsed = time.time() - t0
    summary = dict(p=p, k=k, f=f, n=enc.n, t=t, lo=lo, hi=hi, symbreak=symbreak, min_edges=min_edges, dom=dom, nonindep=nonindep, status=status,
                   iterations=it, cuts=len(cuts), lazydom=lazydom, domcuts=len(domsets), edge_vars=enc.nedge_vars,
                   total_vars=enc.top, base_clauses=len(enc.clauses),
                   seconds=round(elapsed, 2), solver=solver_name)
    if status == "WITNESS":
        summary["graph6"] = to_g6(witness)
        with open(os.path.join(outdir, "witness.g6"), "w") as fh:
            fh.write(summary["graph6"] + "\n")
    if cube is not None:
        summary["cube_edges"] = [list(e) for e in cube]
    if status == "UNSAT":
        write_cnf(os.path.join(outdir, "final.cnf"), enc.top, enc.clauses + cuts)
        with open(os.path.join(outdir, "cutsets.txt"), "w") as fh:
            for S in cutsets:
                fh.write(" ".join(map(str, S)) + "\n")
        with open(os.path.join(outdir, "domsets.txt"), "w") as fh:
            for need, S in domsets:
                fh.write(str(need) + " " + " ".join(map(str, S)) + "\n")
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    if not quiet:
        print(json.dumps(summary), flush=True)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("p", type=int)
    ap.add_argument("k", type=int)
    ap.add_argument("f", type=int)
    ap.add_argument("--t", type=int, default=10)
    ap.add_argument("--lo", type=int, default=4)
    ap.add_argument("--hi", type=int, default=9)
    ap.add_argument("--max-iter", type=int, default=10**7)
    ap.add_argument("--per-model", type=int, default=64)
    ap.add_argument("--solver", default="cadical153")
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--no-symbreak", action="store_true")
    ap.add_argument("--min-edges", type=int, default=0)
    ap.add_argument("--dom", type=int, default=0)
    ap.add_argument("--nonindep", type=int, default=None)
    ap.add_argument("--lazydom", type=int, default=0)
    a = ap.parse_args()
    run(a.p, a.k, a.f, a.t, a.lo, a.hi, a.max_iter, a.per_model, symbreak=not a.no_symbreak,
        solver_name=a.solver, max_seconds=a.max_seconds, min_edges=a.min_edges, dom=a.dom, nonindep=a.nonindep, lazydom=a.lazydom)
