"""Quotient bound for cycle types with many fixed points.

Let sigma have k p-cycles (moving set M) and f fixed points F, and let
H = G[M]. A fixed vertex adjacent to one vertex of an orbit O is adjacent to
all of O (Lemma L2), so every vertex of O has the same set T_O of fixed
neighbours, and |T_O| <= 9 - deg_H(O). For any independent set I of H, the
fixed vertices outside T(I) = U_{O meets I} T_O have no neighbour in I, so

    alpha(G) >= |I| + a(f - sum_{O meets I} (9 - deg_H(O)))

(with |T_O| = 0 when O has an internal edge, Lemma L5) where a(m) = min alpha of a triangle-free graph on m vertices, i.e. the
least s with m <= R(3, s+1) - 1. If this is >= 10 for some I, H cannot be
the moving part of a (3,10,40)-graph. We enumerate every sigma-invariant
triangle-free H with degrees <= 9 (up to the lex-leader symmetry breaking
of SymEncoding with f = 0, which is sound for the same reason as before:
the bound is invariant under the normalizer acting on M) and report the
survivors.

Uses R(3,s) for s <= 9 (classical) only.
"""
import sys
from itertools import combinations

from pysat.solvers import Solver

from graphs import alpha
from symenc import SymEncoding

M_OF = [0, 2, 5, 8, 13, 17, 22, 27, 35]   # m(s) = R(3,s+1)-1, s = 0..8


def a_min(m):
    """Least alpha of a triangle-free graph on m vertices (m <= 35)."""
    if m <= 0:
        return 0
    for s, ms in enumerate(M_OF):
        if m <= ms:
            return s
    return 9  # 36..39 vertices force alpha >= 9


def killed(adj, p, k, f, t=10, maxdeg=9):
    """True if some independent I in H gives the bound >= t."""
    n = k * p
    orbit = [v // p for v in range(n)]
    # Lemma L5: an orbit with an internal edge has no fixed neighbours
    # (a fixed neighbour would see both ends of that edge: a triangle), so
    # its vertices get all >= 4 neighbours inside M.
    slack = []
    for c in range(k):
        block = ((1 << p) - 1) << (c * p)
        internal = adj[c * p] & block
        deg = bin(adj[c * p]).count("1")
        if internal:
            if deg < 4:
                return True
            slack.append(0)
        else:
            slack.append(maxdeg - deg)
    # The bound depends on I only through |I| and the orbits it meets, and
    # meeting fewer orbits only lowers the subtracted slack, so it suffices
    # to take, for every set U of orbits, a maximum independent set of H[U].
    for mask in range(1, 1 << k):
        orbs = [c for c in range(k) if mask >> c & 1]
        verts = [c * p + i for c in orbs for i in range(p)]
        idx = {v: j for j, v in enumerate(verts)}
        sub = [0] * len(verts)
        for v in verts:
            for u in verts:
                if adj[v] >> u & 1:
                    sub[idx[v]] |= 1 << idx[u]
        free = f - sum(slack[c] for c in orbs)
        if alpha(sub) + a_min(free) >= t:
            return True
    return False


def survivors(p, k, f, t=10, limit=10**6):
    enc = SymEncoding(p, k, 0, lo=0, hi=9, symbreak=True)
    out, count = [], 0
    with Solver(name="cadical153", bootstrap_with=enc.clauses) as s:
        while s.solve():
            m = s.get_model()
            proj = [x for x in m[:enc.nedge_vars]]
            s.add_clause([-x for x in proj])  # block this H
            count += 1
            adj = enc.graph(proj)
            if not killed(adj, p, k, f, t):
                out.append(sorted(x for x in proj if x > 0))
            if count >= limit:
                raise RuntimeError("enumeration limit")
    return count, out


if __name__ == "__main__":
    p, k, f = map(int, sys.argv[1:4])
    count, surv = survivors(p, k, f)
    print(f"p={p} k={k} f={f}: {count} moving-part graphs (after symmetry breaking), "
          f"{len(surv)} survive the quotient bound")
