"""Independent re-derivation and proof check of an UNSAT result.

This file deliberately shares no code with symenc.py / search.py.

Input: cycle type (p, k, f), degree bounds, and the certificate file
cutsets.txt (each line: a set of t vertices claimed to be independent in any
graph of the class... rather, each line is a t-set S; the clause "S contains
an edge" is valid for every graph with alpha < t, regardless of S).

The auditor builds its own CNF:
  * one variable per sigma-orbit of vertex pairs (orbits computed via
    explicit cycle arithmetic, not by iterating a permutation table),
  * triangle clauses for every vertex triple,
  * degree bounds lo <= deg <= hi at every vertex (Sinz sequential counter),
  * lex-leader clauses x <=_lex x o phi for the same normalizer elements
    (fixed-point transpositions, cycle swaps, cycle rotations, multipliers),
    built with a different auxiliary encoding,
  * one clause per certificate t-set,
then runs the standalone CaDiCaL binary with a DRAT proof and an LRAT proof,
and checks them with drat-trim and lrat-trim.
"""
import json
import os
import subprocess
import sys
from itertools import combinations

TOOLS = os.environ.get("SAT_TOOLS", "/tmp/claude-0/-home-user-breakthrough-baby/"
                       "72f92ea9-970c-5272-8687-6f892d5444a0/scratchpad/tools")
CADICAL = os.path.join(TOOLS, "cadical/build/cadical")
DRAT_TRIM = os.path.join(TOOLS, "drat-trim/drat-trim")
LRAT_TRIM = os.path.join(TOOLS, "lrat-trim/lrat-trim")


class Audit:
    def __init__(self, p, k, f, lo, hi):
        self.p, self.k, self.f, self.lo, self.hi = p, k, f, lo, hi
        self.n = f + p * k
        self.vid = {}       # canonical orbit key -> var
        self.nv = 0
        for u in range(self.n):
            for v in range(u + 1, self.n):
                key = self.okey(u, v)
                if key not in self.vid:
                    self.nv += 1
                    self.vid[key] = self.nv
        self.N = self.nv
        self.cls = []

    # vertex u -> ("F", x) or ("C", c, i)
    def dec(self, u):
        if u < self.f:
            return ("F", u)
        c, i = divmod(u - self.f, self.p)
        return ("C", c, i)

    def okey(self, u, v):
        """Canonical key of the orbit of {u,v} under (c,i) -> (c,i+1)."""
        a, b = self.dec(u), self.dec(v)
        if a[0] == "F" and b[0] == "F":
            return ("FF", min(a[1], b[1]), max(a[1], b[1]))
        if a[0] == "F" or b[0] == "F":
            x, y = (a, b) if a[0] == "F" else (b, a)
            return ("FC", x[1], y[1])
        if a[1] == b[1]:
            d = (b[2] - a[2]) % self.p
            return ("CC", a[1], min(d, self.p - d))
        if a[1] > b[1]:
            a, b = b, a
        return ("CD", a[1], b[1], (b[2] - a[2]) % self.p)

    def x(self, u, v):
        return self.vid[self.okey(u, v)]

    def new(self):
        self.nv += 1
        return self.nv

    def triangles(self):
        s = set()
        for a, b, c in combinations(range(self.n), 3):
            s.add(tuple(sorted({-self.x(a, b), -self.x(b, c), -self.x(a, c)})))
        self.cls += [list(c) for c in s]

    def atmost(self, lits, K):
        """Sinz sequential counter: sum(lits) <= K (duplicates allowed)."""
        m = len(lits)
        if K >= m:
            return
        if K == 0:
            self.cls += [[-l] for l in lits]
            return
        s = [[self.new() for _ in range(K)] for _ in range(m)]
        # s[i][j] : at least j+1 of lits[0..i] are true
        self.cls.append([-lits[0], s[0][0]])
        for j in range(1, K):
            self.cls.append([-s[0][j]])
        for i in range(1, m):
            self.cls.append([-lits[i], s[i][0]])
            self.cls.append([-s[i - 1][0], s[i][0]])
            for j in range(1, K):
                self.cls.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
                self.cls.append([-s[i - 1][j], s[i][j]])
            self.cls.append([-lits[i], -s[i - 1][K - 1]])

    def atleast_edges(self, K):
        """Sequential counter, at-least form: >= K edges in the whole graph
        (every vertex pair counted once, via its orbit variable)."""
        lits = [self.x(u, v) for u in range(self.n) for v in range(u + 1, self.n)]
        m = len(lits)
        s = [[self.new() for _ in range(K)] for _ in range(m)]
        # s[i][j] -> "at least j+1 of lits[0..i] true"  (only the needed direction)
        self.cls.append([-s[0][0], lits[0]])
        for j in range(1, K):
            self.cls.append([-s[0][j]])
        for i in range(1, m):
            for j in range(K):
                self.cls.append([-s[i][j], s[i - 1][j], lits[i]])
                if j:
                    self.cls.append([-s[i][j], s[i - 1][j], s[i - 1][j - 1]])
        self.cls.append([s[m - 1][K - 1]])

    def sig(self, u):
        d = self.dec(u)
        if d[0] == "F":
            return u
        return self.f + d[1] * self.p + (d[2] + 1) % self.p

    def atleast(self, lits, K):
        """Return a literal r with r -> (at least K of lits true)."""
        m = len(lits)
        s = [[self.new() for _ in range(K)] for _ in range(m)]
        self.cls.append([-s[0][0], lits[0]])
        for j in range(1, K):
            self.cls.append([-s[0][j]])
        for i in range(1, m):
            for j in range(K):
                self.cls.append([-s[i][j], s[i - 1][j], lits[i]])
                if j:
                    self.cls.append([-s[i][j], s[i - 1][j], s[i - 1][j - 1]])
        return s[m - 1][K - 1]

    def domination_set(self, S, need):
        ys = []
        for w in range(self.n):
            if w in S:
                continue
            y = self.new()
            self.cls.append([-y] + [self.x(u, w) for u in S])
            ys.append(y)
        r = self.atleast(ys, need)
        self.cls.append([self.x(u, v) for u, v in combinations(S, 2)] + [r])

    def domination(self, size, need):
        """Independent size-set S => |N(S)| >= need (one per sigma-orbit)."""
        done = set()
        for S in combinations(range(self.n), size):
            if frozenset(S) in done:
                continue
            T = list(S)
            for _ in range(self.p):
                done.add(frozenset(T))
                T = [self.sig(v) for v in T]
            ys = []
            for w in range(self.n):
                if w in S:
                    continue
                y = self.new()
                self.cls.append([-y] + [self.x(u, w) for u in S])
                ys.append(y)
            r = self.atleast(ys, need)
            self.cls.append([self.x(u, v) for u, v in combinations(S, 2)] + [r])

    def degrees(self):
        for u in range(self.n):
            lits = [self.x(u, v) for v in range(self.n) if v != u]
            self.atmost(lits, self.hi)
            self.atmost([-l for l in lits], len(lits) - self.lo)

    def perms(self):
        p, k, f, n = self.p, self.k, self.f, self.n
        out = []
        for a, b in combinations(range(f), 2):
            pi = list(range(n)); pi[a], pi[b] = b, a; out.append(pi)
        for c, d in combinations(range(k), 2):
            pi = list(range(n))
            for i in range(p):
                pi[f + c * p + i], pi[f + d * p + i] = f + d * p + i, f + c * p + i
            out.append(pi)
        for c in range(k):
            for r in range(1, p):
                pi = list(range(n))
                for i in range(p):
                    pi[f + c * p + i] = f + c * p + (i + r) % p
                out.append(pi)
        for m in range(2, p):
            pi = list(range(n))
            for c in range(k):
                for i in range(p):
                    pi[f + c * p + i] = f + c * p + (m * i) % p
            out.append(pi)
        return out

    def fix_moving(self, edges):
        on = {self.x(u, v) for u, v in edges}
        for u in range(self.f, self.n):
            for v in range(u + 1, self.n):
                self.cls.append([self.x(u, v)] if self.x(u, v) in on else [-self.x(u, v)])

    def lexleader(self, fixed_only=False):
        # variable order: the order of first appearance over pairs (u,v), u<v
        order = []
        seen = set()
        for u in range(self.n):
            for v in range(u + 1, self.n):
                xv = self.x(u, v)
                if xv not in seen:
                    seen.add(xv); order.append((xv, (u, v)))
        assert [o[0] for o in order] == list(range(1, self.N + 1))
        for pi in self.perms():
            if fixed_only and any(pi[v] != v for v in range(self.f, self.n)):
                continue
            # phi(var of {u,v}) = var of {pi u, pi v}; must be well defined
            phi = {}
            for u in range(self.n):
                for v in range(u + 1, self.n):
                    a, b = self.x(u, v), self.x(pi[u], pi[v])
                    assert phi.setdefault(a, b) == b
            # x <=_lex y, y_i = x_phi(i). Aux q_i <-> (x_1..x_i == y_1..y_i).
            q = None
            for i in range(1, self.N + 1):
                j = phi[i]
                if j == i:
                    continue
                pre = [] if q is None else [-q]
                self.cls.append(pre + [-i, j])
                nq = self.new()
                # nq -> q ; nq -> (i == j) ; (q & i==j) -> nq
                if q is not None:
                    self.cls.append([-nq, q])
                self.cls.append([-nq, -i, j])
                self.cls.append([-nq, i, -j])
                self.cls.append(pre + [i, j, nq])
                self.cls.append(pre + [-i, -j, nq])
                q = nq

    def cuts(self, path, t):
        cnt = 0
        with open(path) as fh:
            for line in fh:
                S = list(map(int, line.split()))
                assert len(S) == t and len(set(S)) == t and all(0 <= s < self.n for s in S)
                self.cls.append(sorted({self.x(a, b) for a, b in combinations(S, 2)}))
                cnt += 1
        return cnt


def run(rundir, p, k, f, t=10, lo=4, hi=9, symbreak=True, min_edges=0, cube=None, dom=0, nonindep=None):
    A = Audit(p, k, f, lo, hi)
    A.triangles()
    A.degrees()
    if min_edges:
        A.atleast_edges(min_edges)
    if nonindep is not None:
        # exactly `nonindep` cycles contain an internal edge: count with the
        # sequential counters (at most) on z and on not-z
        zs = []
        for c in range(k):
            w = sorted({A.x(A.f + c * p, A.f + c * p + d) for d in range(1, p)})
            z = A.new()
            A.cls.append([-z] + w)
            A.cls += [[-x, z] for x in w]
            zs.append(z)
        A.atmost(zs, nonindep)
        A.atmost([-z for z in zs], k - nonindep)
    if dom >= 2:
        A.domination(2, 40 - 2 - 27)   # R(3,8) = 28
    if dom >= 3:
        A.domination(3, 40 - 3 - 22)   # R(3,7) = 23
    if cube is not None:
        A.fix_moving(cube)
    if symbreak:
        A.lexleader(fixed_only=(symbreak == "fixed"))
    ncut = A.cuts(os.path.join(rundir, "cutsets.txt"), t)
    ndom = 0
    dpath = os.path.join(rundir, "domsets.txt")
    if os.path.exists(dpath):
        # m(s) = R(3,s+1) - 1 (exact for s <= 8; s = 9 uses R(3,10) <= 41)
        m_of = {0: 0, 1: 2, 2: 5, 3: 8, 4: 13, 5: 17, 6: 22, 7: 27, 8: 35, 9: 40}
        for line in open(dpath):
            need, *S = map(int, line.split())
            assert len(set(S)) == len(S) and all(0 <= v < A.n for v in S)
            assert need <= A.n - len(S) - m_of[t - 1 - len(S)], "unjustified domination need"
            A.domination_set(S, need)
            ndom += 1
    cnf = os.path.join(rundir, "audit.cnf")
    with open(cnf, "w") as fh:
        fh.write(f"p cnf {A.nv} {len(A.cls)}\n")
        for c in A.cls:
            fh.write(" ".join(map(str, c)) + " 0\n")
    res = {"vars": A.nv, "clauses": len(A.cls), "cuts": ncut, "domcuts": ndom}
    drat = os.path.join(rundir, "audit.drat")
    r = subprocess.run([CADICAL, "-q", "--no-binary", cnf, drat], capture_output=True, text=True)
    res["cadical_exit"] = r.returncode  # 20 = UNSAT
    if r.returncode == 20:
        d = subprocess.run([DRAT_TRIM, cnf, drat, "-t", "20000"], capture_output=True, text=True)
        res["drat_trim"] = "VERIFIED" if "s VERIFIED" in d.stdout else d.stdout[-300:]
        lrat = os.path.join(rundir, "audit.lrat")
        subprocess.run([CADICAL, "-q", "--lrat", "--no-binary", cnf, lrat], capture_output=True)
        l = subprocess.run([LRAT_TRIM, cnf, lrat], capture_output=True, text=True)
        res["lrat_trim"] = "VERIFIED" if "s VERIFIED" in l.stdout else (l.stdout + l.stderr)[-300:]
        for pth in (drat, lrat):
            res[os.path.basename(pth) + "_bytes"] = os.path.getsize(pth)
            os.remove(pth)
    with open(os.path.join(rundir, "audit.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    return res


if __name__ == "__main__":
    rundir = sys.argv[1]
    s = json.load(open(os.path.join(rundir, "summary.json")))
    print(json.dumps(run(rundir, s["p"], s["k"], s["f"], s["t"], s["lo"], s["hi"],
                         s.get("symbreak", True), s.get("min_edges", 0), s.get("cube_edges"), s.get("dom", 0), s.get("nonindep"))))
