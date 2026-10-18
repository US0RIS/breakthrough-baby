"""Semantic test of the domination constraints on random maximal
triangle-free sigma-invariant graphs (both outcomes occur)."""
import random
from itertools import combinations
from pysat.solvers import Solver
from symenc import SymEncoding


def direct(adj, n, size, need):
    for S in combinations(range(n), size):
        if any(adj[u] >> v & 1 for u, v in combinations(S, 2)):
            continue
        nb = 0
        for u in S:
            nb |= adj[u]
        if bin(nb).count("1") < need:
            return False
    return True


def test(p, k, f, size, need, trials=40, seed=0):
    rng = random.Random(seed)
    E = SymEncoding(p, k, f, lo=0, hi=63, symbreak=False)
    E.add_domination(size, need)
    n, res = E.n, [0, 0]
    with Solver(name="cadical153", bootstrap_with=E.clauses) as s:
        for _ in range(trials):
            order = list(range(1, E.nedge_vars + 1)); rng.shuffle(order)
            on = set()
            for x in order:
                adj = E.graph(list(on | {x}))
                if all(not (adj[u] & adj[v]) for u in range(n) for v in range(n) if adj[u] >> v & 1):
                    if rng.random() < 0.9:
                        on.add(x)
            adj = E.graph(list(on))
            ok = direct(adj, n, size, need)
            r = s.solve(assumptions=[v if v in on else -v for v in range(1, E.nedge_vars + 1)])
            assert r == ok, (p, k, f, size, need, r, ok)
            res[ok] += 1
    return res


for case in [(5, 4, 0, 2, 8), (3, 6, 2, 2, 9), (2, 8, 2, 2, 7), (5, 4, 0, 3, 9), (3, 5, 1, 3, 8), (7, 3, 1, 2, 9), (2, 6, 2, 3, 8)]:
    print(case, "violating/satisfying:", test(*case))
print("domination tests passed")
