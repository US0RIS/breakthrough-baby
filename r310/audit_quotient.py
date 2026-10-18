"""Independent check of the quotient-bound exclusions (shares no code with
quotient.py / symenc.py / graphs.py).

Enumerates EVERY sigma-invariant triangle-free graph H on the moving set
(k cycles of length p, no symmetry breaking) with max degree <= 9 by
backtracking over pair orbits, and checks that each is excluded by:
  (L5)  an orbit with an internal edge has no fixed neighbour, so its
        vertices need degree >= 4 inside H;
  (QB)  some set U of orbits has alpha(H[U]) + a(f - slack(U)) >= 10, where
        slack(O) = 0 if O has an internal edge, else 9 - deg_H(O), and
        a(m) = least s with m <= R(3, s+1) - 1.
Prints the number of graphs checked; exits non-zero if any graph survives.
"""
import sys
from itertools import combinations

RAMSEY3 = {1: 1, 2: 3, 3: 6, 4: 9, 5: 14, 6: 18, 7: 23, 8: 28, 9: 36}  # R(3,s)


def a_of(m):
    if m <= 0:
        return 0
    s = 0
    while not (m <= RAMSEY3[s + 1] - 1):
        s += 1
    return s


def alpha_brute(vertices, nbr):
    best = 0

    def rec(cands, size):
        nonlocal best
        if size + len(cands) <= best:
            return
        if not cands:
            best = max(best, size)
            return
        v = cands[0]
        rec([u for u in cands[1:] if u not in nbr[v]], size + 1)
        rec(cands[1:], size)

    rec(list(vertices), 0)
    return best


def main(p, k, f):
    n = p * k
    vert = [(c, i) for c in range(k) for i in range(p)]
    # pair orbits: within cycle c, distance d in 1..p//2 ; between c<e, shift s
    orbits = []
    for c in range(k):
        for d in range(1, p // 2 + 1):
            orbits.append(("in", c, d))
    for c, e in combinations(range(k), 2):
        for s in range(p):
            orbits.append(("bt", c, e, s))

    def edges_of(o):
        if o[0] == "in":
            _, c, d = o
            return {frozenset({(c, i), (c, (i + d) % p)}) for i in range(p)}
        _, c, e, s = o
        return {frozenset({(c, i), (e, (i + s) % p)}) for i in range(p)}

    E = [edges_of(o) for o in orbits]
    count = 0
    survivors = 0
    nbr = {v: set() for v in vert}

    def triangle_free_with(es):
        for ed in es:
            a, b = tuple(ed)
            if nbr[a] & nbr[b]:
                return False
        return True

    def check():
        deg = {v: len(nbr[v]) for v in vert}
        slack = []
        for c in range(k):
            internal = any(w[0] == c for w in nbr[(c, 0)])
            if internal:
                if deg[(c, 0)] < 4:
                    return True
                slack.append(0)
            else:
                slack.append(9 - deg[(c, 0)])
        for r in range(1, k + 1):
            for U in combinations(range(k), r):
                vs = [v for v in vert if v[0] in U]
                if alpha_brute(vs, nbr) + a_of(f - sum(slack[c] for c in U)) >= 10:
                    return True
        return False

    def rec(j):
        nonlocal count, survivors
        if j == len(orbits):
            count += 1
            if not check():
                survivors += 1
            return
        rec(j + 1)  # orbit j absent
        es = E[j]
        # add orbit j if triangle-free and degrees stay <= 9
        added = []
        ok = True
        for ed in es:
            a, b = tuple(ed)
            if b in nbr[a]:
                continue
            if nbr[a] & nbr[b]:
                ok = False
                break
            nbr[a].add(b); nbr[b].add(a); added.append((a, b))
        if ok and all(len(nbr[v]) <= 9 for v in vert):
            rec(j + 1)
        for a, b in added:
            nbr[a].discard(b); nbr[b].discard(a)

    rec(0)
    print(f"p={p} k={k} f={f}: {count} invariant moving parts checked, {survivors} survive")
    return survivors


if __name__ == "__main__":
    sys.exit(1 if main(*map(int, sys.argv[1:4])) else 0)
