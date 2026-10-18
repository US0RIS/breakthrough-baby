"""Small-graph utilities: ctypes wrapper around indep.c plus plain checks."""
import ctypes
import os
import subprocess
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
_SO = os.path.join(HERE, "libindep.so")


def _lib():
    src = os.path.join(HERE, "indep.c")
    if not os.path.exists(_SO) or os.path.getmtime(_SO) < os.path.getmtime(src):
        subprocess.check_call(["gcc", "-O3", "-march=native", "-shared", "-fPIC", "-o", _SO, src])
    lib = ctypes.CDLL(_SO)
    lib.find_indep.restype = ctypes.c_int
    lib.find_indep.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint64), ctypes.c_int,
                               ctypes.c_int, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
    lib.alpha.restype = ctypes.c_int
    lib.alpha.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint64)]
    return lib


LIB = _lib()


def find_indep(adj, t, maxout=64, seed=0):
    n = len(adj)
    arr = (ctypes.c_uint64 * n)(*adj)
    out = (ctypes.c_uint64 * maxout)()
    m = LIB.find_indep(n, arr, t, maxout, out, seed)
    return [[v for v in range(n) if out[i] >> v & 1] for i in range(m)]


def alpha(adj):
    n = len(adj)
    return LIB.alpha(n, (ctypes.c_uint64 * n)(*adj))


def triangle_free(adj):
    n = len(adj)
    for u in range(n):
        for v in range(u + 1, n):
            if adj[u] >> v & 1 and adj[u] & adj[v]:
                return False
    return True


def alpha_bruteforce(adj, limit):
    """Independent check by plain recursion (no bounds); returns True iff
    some independent set of size `limit` exists."""
    n = len(adj)

    def rec(start, size, chosen_mask):
        if size == limit:
            return True
        for v in range(start, n):
            if not (adj[v] & chosen_mask) and n - v >= limit - size:
                if rec(v + 1, size + 1, chosen_mask | (1 << v)):
                    return True
        return False

    return rec(0, 0, 0)


def to_edges(adj):
    n = len(adj)
    return [(u, v) for u, v in combinations(range(n), 2) if adj[u] >> v & 1]


def from_edges(n, edges):
    adj = [0] * n
    for u, v in edges:
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return adj


def to_g6(adj):
    n = len(adj)
    bits = [adj[i] >> j & 1 for j in range(n) for i in range(j)]
    bits += [0] * (-len(bits) % 6)
    s = chr(n + 63)
    for i in range(0, len(bits), 6):
        s += chr(63 + int("".join(map(str, bits[i:i + 6])), 2))
    return s


def from_g6(s):
    s = s.strip()
    n = ord(s[0]) - 63
    bits = []
    for ch in s[1:]:
        x = ord(ch) - 63
        bits += [(x >> (5 - b)) & 1 for b in range(6)]
    adj = [0] * n
    idx = 0
    for j in range(n):
        for i in range(j):
            if bits[idx]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
            idx += 1
    return adj


def circulant(n, dists):
    edges = set()
    for i in range(n):
        for d in dists:
            j = (i + d) % n
            edges.add((min(i, j), max(i, j)))
    return from_edges(n, edges)
