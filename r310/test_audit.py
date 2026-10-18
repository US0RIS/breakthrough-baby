"""Check the auditor's base encoding semantically on random invariant graphs:
with all edge variables fixed, the CNF (without lex-leader and cuts) must be
satisfiable iff the graph is triangle-free with lo <= deg <= hi."""
import random
from pysat.solvers import Solver
from audit import Audit


def check(p, k, f, lo, hi, trials=300, dens=0.2):
    A = Audit(p, k, f, lo, hi)
    A.triangles(); A.degrees()
    rng = random.Random(p * 1000 + k * 10 + f)
    agree = [0, 0]
    with Solver(name="minisat22", bootstrap_with=A.cls) as s:
        for _ in range(trials):
            on = {v for v in range(1, A.N + 1) if rng.random() < dens}
            adj = [set() for _ in range(A.n)]
            for u in range(A.n):
                for v in range(u + 1, A.n):
                    if A.x(u, v) in on:
                        adj[u].add(v); adj[v].add(u)
            tf = all(not (adj[u] & adj[v]) for u in range(A.n) for v in adj[u])
            ok = tf and all(lo <= len(a) <= hi for a in adj)
            sat = s.solve(assumptions=[v if v in on else -v for v in range(1, A.N + 1)])
            assert sat == ok, (p, k, f, ok, sat)
            agree[ok] += 1
    return agree


for case in [(7, 5, 5, 4, 9), (5, 8, 0, 4, 9), (3, 13, 1, 4, 9), (2, 20, 0, 4, 9), (2, 5, 4, 1, 4),
             (3, 4, 2, 2, 5), (5, 2, 3, 1, 4), (7, 2, 2, 0, 3)]:
    for d in (0.03, 0.08, 0.2):
        print(case, d, "invalid/valid graphs checked:", check(*case, dens=d))
print("auditor base-encoding tests passed")
