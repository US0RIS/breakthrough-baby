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

    def lexleader(self):
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


def run(rundir, p, k, f, t=10, lo=4, hi=9, symbreak=True):
    A = Audit(p, k, f, lo, hi)
    A.triangles()
    A.degrees()
    if symbreak:
        A.lexleader()
    ncut = A.cuts(os.path.join(rundir, "cutsets.txt"), t)
    cnf = os.path.join(rundir, "audit.cnf")
    with open(cnf, "w") as fh:
        fh.write(f"p cnf {A.nv} {len(A.cls)}\n")
        for c in A.cls:
            fh.write(" ".join(map(str, c)) + " 0\n")
    res = {"vars": A.nv, "clauses": len(A.cls), "cuts": ncut}
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
                         s.get("symbreak", True))))
