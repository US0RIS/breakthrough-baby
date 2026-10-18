"""Exhaustive soundness test of the lex-leader symmetry breaking.

For small parameter sets, enumerate every sigma-invariant graph directly,
keep those satisfying the problem (triangle-free, alpha < t, degree bounds),
and check that each one's normalizer orbit contains a model of the
symmetry-broken CNF (enumerated by SAT, projected onto edge variables).
Also check the converse: every model is a valid graph of the class.
"""
import itertools

from pysat.solvers import Solver

from graphs import alpha, triangle_free
from symenc import SymEncoding


def valid(adj, t, lo, hi):
    if not triangle_free(adj) or alpha(adj) >= t:
        return False
    return all(lo <= bin(a).count("1") <= hi for a in adj)


def check(p, k, f, t, lo, hi):
    enc = SymEncoding(p, k, f, lo, hi, symbreak=True)
    N = enc.nedge_vars
    assert N <= 22, N
    gens = [enc.induced_var_map(pi) for pi in enc.normalizer_elements()]
    models = set()
    with Solver(name="cadical153", bootstrap_with=enc.clauses) as s:
        while s.solve():
            m = s.get_model()
            proj = tuple(1 if m[i - 1] > 0 else 0 for i in range(1, N + 1))
            models.add(proj)
            s.add_clause([-i if proj[i - 1] else i for i in range(1, N + 1)])
    nvalid = 0
    for bits in itertools.product([0, 1], repeat=N):
        adj = enc.graph([i if bits[i - 1] else -i for i in range(1, N + 1)])
        if not valid(adj, t, lo, hi):
            continue
        nvalid += 1
        orbit, frontier = {bits}, [bits]
        while frontier:
            x = frontier.pop()
            for phi in gens:
                y = [0] * N
                for i in range(1, N + 1):
                    y[phi[i] - 1] = x[i - 1]
                y = tuple(y)
                if y not in orbit:
                    orbit.add(y)
                    frontier.append(y)
        assert orbit & models, ("orbit lost", p, k, f, t, bits)
    for bits in models:  # base CNF (no alpha cuts) must imply triangle/degree
        adj = enc.graph([i if bits[i - 1] else -i for i in range(1, N + 1)])
        assert triangle_free(adj)
        assert all(lo <= bin(a).count("1") <= hi for a in adj)
    return nvalid, len(models)


CASES = [(3, 2, 2, 5, 1, 4), (3, 3, 0, 5, 1, 4), (2, 3, 2, 5, 1, 3), (2, 4, 0, 5, 1, 3),
         (5, 2, 0, 5, 1, 4), (2, 3, 1, 4, 0, 4), (3, 2, 1, 5, 1, 3), (5, 1, 3, 6, 1, 5),
         (2, 2, 3, 4, 1, 3), (7, 1, 2, 6, 1, 4), (3, 3, 1, 5, 2, 3), (2, 4, 1, 5, 1, 4),
         (5, 2, 1, 5, 2, 4), (3, 2, 2, 4, 1, 4), (2, 3, 2, 4, 1, 3)]

if __name__ == "__main__":
    for c in CASES:
        print(c, "valid graphs / symmetry-broken models:", check(*c), flush=True)
    print("symmetry-breaking soundness tests passed")
