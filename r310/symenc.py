"""CNF encoding of (3, t, n)-graphs invariant under a permutation sigma.

sigma has prime order p, k cycles of length p and f fixed points, with
n = f + k*p. Vertex labels: fixed points are 0..f-1; cycle c position i is
f + c*p + i, and sigma maps (c, i) to (c, i+1 mod p).

A sigma-invariant graph is a union of sigma-orbits of vertex pairs, so we
use one Boolean variable per pair orbit. Constraints:
  * triangle-free: one clause per triangle (deduplicated over orbits);
  * lo <= deg(v) <= hi for one representative of every vertex orbit;
  * independence number < t: added lazily (each clause says "this t-set
    contains an edge"; it is valid for every graph in the class).
"""
from itertools import combinations


class SymEncoding:
    def __init__(self, p, k, f, lo=4, hi=9, symbreak=True):
        self.p, self.k, self.f = p, k, f
        self.n = f + k * p
        assert self.n <= 64
        self.sigma = list(range(f)) + [
            f + c * p + (i + 1) % p for c in range(k) for i in range(p)
        ]
        self.pair_var = {}
        self.var_pairs = {}
        nv = 0
        for u, v in combinations(range(self.n), 2):
            if (u, v) in self.pair_var:
                continue
            nv += 1
            orbit = []
            a, b = u, v
            while True:
                key = (min(a, b), max(a, b))
                if key in self.pair_var:
                    break
                self.pair_var[key] = nv
                orbit.append(key)
                a, b = self.sigma[a], self.sigma[b]
            self.var_pairs[nv] = orbit
        self.nedge_vars = nv
        self.top = nv
        self.clauses = []
        self._triangles()
        self.vertex_reps = list(range(f)) + [f + c * p for c in range(k)]
        for v in self.vertex_reps:
            self._degree(v, lo, hi)
        if symbreak:
            self.add_symmetry_breaking()

    def var(self, u, v):
        return self.pair_var[(min(u, v), max(u, v))]

    def _triangles(self):
        seen = set()
        for a, b, c in combinations(range(self.n), 3):
            cl = frozenset((self.var(a, b), self.var(b, c), self.var(a, c)))
            if cl not in seen:
                seen.add(cl)
                self.clauses.append([-x for x in sorted(cl)])
        self.ntriangle = len(seen)

    def _new(self):
        self.top += 1
        return self.top

    def _totalizer(self, lits):
        """Return unary outputs o[0..m-1], o[j] <-> (#true lits >= j+1).

        Duplicate literals count with multiplicity, which is exactly the
        degree semantics we need (a pair orbit may contain several edges
        at one vertex)."""
        if len(lits) == 1:
            return [lits[0]]
        mid = len(lits) // 2
        a = self._totalizer(lits[:mid])
        b = self._totalizer(lits[mid:])
        out = [self._new() for _ in range(len(a) + len(b))]
        # a_i & b_j -> out_{i+j}   (i, j counted from 0 meaning ">= 0")
        for i in range(len(a) + 1):
            for j in range(len(b) + 1):
                if i + j == 0:
                    continue
                cl = [out[i + j - 1]]
                if i:
                    cl.append(-a[i - 1])
                if j:
                    cl.append(-b[j - 1])
                self.clauses.append(cl)
        # ~a_{i+1} & ~b_{j+1} -> ~out_{i+j+1}
        for i in range(len(a) + 1):
            for j in range(len(b) + 1):
                if i + j >= len(out):
                    continue
                cl = [-out[i + j]]
                if i < len(a):
                    cl.append(a[i])
                if j < len(b):
                    cl.append(b[j])
                self.clauses.append(cl)
        return out

    def degree_lits(self, v):
        return [self.var(v, u) for u in range(self.n) if u != v]

    def _degree(self, v, lo, hi):
        out = self._totalizer(self.degree_lits(v))
        if lo >= 1:
            self.clauses.append([out[lo - 1]])
        if hi < len(out):
            self.clauses.append([-out[hi]])

    # ---- symmetry breaking -------------------------------------------
    #
    # Any vertex permutation pi in the normalizer of <sigma> maps
    # sigma-invariant graphs to sigma-invariant graphs and preserves
    # triangle-freeness, alpha and degrees, so it permutes the solution
    # set of the *problem*. For a fixed variable order, the lex-least
    # member of each orbit satisfies x <=_lex pi(x) for every such pi.
    # Hence adding these constraints for any collection of normalizer
    # elements keeps at least one representative of every solution orbit.
    # (Lazy cut clauses are implied by the problem, so they are unaffected.)

    def induced_var_map(self, pi):
        """phi[x] = variable of the orbit pi(orbit x); checks pi normalizes."""
        phi = {}
        for x, pairs in self.var_pairs.items():
            imgs = {self.var(pi[u], pi[v]) for u, v in pairs}
            assert len(imgs) == 1, "permutation does not normalize <sigma>"
            phi[x] = imgs.pop()
        assert sorted(phi.values()) == list(range(1, self.nedge_vars + 1))
        return phi

    def add_lex_leader(self, pi):
        """Clauses for x <=_lex y with y_i = x_{phi(i)} (vars 1..N in order)."""
        phi = self.induced_var_map(pi)
        eq_prev = None  # literal meaning "x_j == y_j for all earlier j"; None = true
        for i in range(1, self.nedge_vars + 1):
            j = phi[i]
            if j == i:
                continue
            g = [] if eq_prev is None else [-eq_prev]
            # prefix equal -> x_i <= y_i   i.e. not (x_i and not y_i)
            self.clauses.append(g + [-i, j])
            e = self._new()
            # prefix equal and x_i == y_i -> e  (the other direction is not needed)
            self.clauses.append(g + [i, j, e])
            self.clauses.append(g + [-i, -j, e])
            eq_prev = e

    def normalizer_elements(self):
        p, k, f = self.p, self.k, self.f
        ident = list(range(self.n))
        out = []
        for a in range(f):  # transpositions of fixed points
            for b in range(a + 1, f):
                pi = ident[:]
                pi[a], pi[b] = b, a
                out.append(pi)
        for c in range(k):  # swaps of aligned cycles
            for d in range(c + 1, k):
                pi = ident[:]
                for i in range(p):
                    pi[f + c * p + i], pi[f + d * p + i] = f + d * p + i, f + c * p + i
                out.append(pi)
        for c in range(k):  # independent rotations of one cycle
            for r in range(1, p):
                pi = ident[:]
                for i in range(p):
                    pi[f + c * p + i] = f + c * p + (i + r) % p
                out.append(pi)
        for a in range(2, p):  # multipliers i -> a*i on every cycle
            pi = ident[:]
            for c in range(k):
                for i in range(p):
                    pi[f + c * p + i] = f + c * p + (a * i) % p
            out.append(pi)
        return out

    def add_symmetry_breaking(self):
        for pi in self.normalizer_elements():
            self.add_lex_leader(pi)

    def cut(self, vertices):
        """Clause: the vertex set is not independent."""
        return sorted({self.var(u, v) for u, v in combinations(vertices, 2)})

    def graph(self, model):
        true = {x for x in model if 0 < x <= self.nedge_vars}
        adj = [0] * self.n
        for x in true:
            for u, v in self.var_pairs[x]:
                adj[u] |= 1 << v
                adj[v] |= 1 << u
        return adj
