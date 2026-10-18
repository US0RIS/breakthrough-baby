# 2. Automorphisms of a hypothetical (3,10,40)-graph

Throughout, G is a **(3,10,40)-graph**: 40 vertices, triangle-free, α(G) ≤ 9.
Such a G exists iff R(3,10) = 41. σ ∈ Aut(G) has prime order p, with k cycles
of length p and f = 40 − kp fixed points. F is the fixed set and M the moving set.

Write m(s) = R(3, s+1) − 1 for the maximum order of a triangle-free graph with
α ≤ s. Known values: m(1..9) = 2, 5, 8, 13, 17, 22, 27, 35, 39 (R(3,9)=36 is
Grinstead–Roberts 1982; R(3,10) ≥ 40 is Exoo 1989).

## Lemmas (proved by hand; status: proved)

**L0 (degrees).** 4 ≤ deg(v) ≤ 9. Every neighbourhood is independent, which gives
the upper bound. G − N[v] has α ≤ 8, so 39 − deg(v) ≤ m(8) = 35.

**L1 (connectivity).** G is connected. If not, take components A and B with
α(A) + α(B) ≤ 9. Then |A| + |B| ≤ max over s of (m(s) + m(9−s)) = m(1) + m(8) = 37 < 40.

**L2 (fixed vertices).** If x ∈ F is adjacent to y ∈ M, then x is adjacent to
the whole σ-orbit of y, so deg(x) ≥ p.

**Theorem A (primes ≥ 11).** G has no automorphism of prime order p ≥ 11.
*Proof.* By L0 and L2, no edge joins F to M. By L1, F = ∅ or M = ∅. Since
σ ≠ id, F = ∅, so p | 40, which forces p ∈ {2, 5}. ∎

**L3 (one 7-cycle).** p = 7 with k = 1 (f = 33) is impossible. The orbit O induces
a triangle-free circulant on ℤ₇: either empty (α = 7) or a single 7-cycle
(α = 3, internal degree 2). Each fixed vertex sees all of O or none of it, so
at most 9 − 2 = 7 (respectively 9) fixed vertices see O. That leaves at least
24 fixed vertices with no neighbour in O, and they contain an independent set of
size ≥ 7 because 24 > m(6) = 22. Adding α(O) ≥ 3 gives α(G) ≥ 10. ∎

**L4 (one 5-cycle).** p = 5 with k = 1 (f = 35) is impossible. If O is a C₅
(α = 2), at most 7 fixed vertices see O. The other ≥ 28 > m(7) fixed vertices
give an independent 8-set, so α ≥ 10. If O is empty (α = 5), the other ≥ 26 > m(6)
fixed vertices give 7, so α ≥ 12. ∎

**L5 (orbits with internal edges).** If a σ-orbit O contains an edge yy′, no
fixed vertex is adjacent to O, since it would be adjacent to both y and y′. Hence
every vertex of O has all of its ≥ 4 neighbours in M. (For p = 3 an internal
edge would make O a triangle, so 3-orbits are always independent.)

**Quotient bound (QB).** Let H = G[M]. Write slack(O) = 0 if O has an internal
edge, and otherwise 9 − deg_H(O), an upper bound on |T_O|. For every set U of
orbits, the fixed vertices outside ∪_{O∈U} T_O have no neighbour in H[U], so

  α(G) ≥ α(H[U]) + a(f − Σ_{O∈U} slack(O)),

where a(m) = min α over triangle-free graphs on m vertices, i.e. the least s
with m ≤ m(s). If some U makes the right side ≥ 10, then H is impossible.
`quotient.py` enumerates every σ-invariant triangle-free H with Δ ≤ 9, up to
lex-leader symmetry. **Theorem (QB exclusions).** These cycle types admit no H:
(7,1,33), (7,2,26), (7,3,19), (5,1,35), (5,2,30), (5,3,25), (5,4,20),
(3,1,37), (3,2,34), (3,3,31), (2,1,38), (2,2,36).
`audit_quotient.py` re-checks every case with p·k ≤ 15 by brute force with
no symmetry breaking and shares no code with the enumerator. The other QB
results are corroborated by SAT. Cycle types written (p, k, f).

**Domination constraints (D2, D3).** If S is an independent set of size s, then
V ∖ N[S] has α ≤ 9 − s. Hence |N(S)| ≥ 40 − s − m(9 − s): this is ≥ 11 for s = 2
(R(3,8) = 28) and ≥ 15 for s = 3 (R(3,7) = 23). They are encoded as one
cardinality constraint per σ-orbit of pairs or triples. This feeds the solver
Ramsey knowledge it cannot rediscover cheaply from α-cuts. They are tested
in both directions against direct computation (`test_dom.py`) and re-encoded
independently in `audit.py`.

**Two kinds of cubes.**
- *Moving-part cubes* (`cubes.py`) fix G[M] to a lex-leader survivor of QB.
  They are combined **only** with fixed-point lex-leader constraints, which act
  on F alone. Mixing in M-symmetries would compare different lex orders and
  could discard the cube's own representative.
- *Invariant cubes* (`--nonindep j`) fix "exactly j orbits have an internal
  edge". That count is preserved by every normalizer element, so they are
  compatible with full symmetry breaking. They partition the solution set,
  which was checked exhaustively on small cases.

## Computational method (status: implemented, tested)

For each cycle type (p, k, f), we use one Boolean variable per σ-orbit of vertex
pairs, so every assignment is a σ-invariant graph and vice versa. The constraints are:

- triangle clauses;
- 4 ≤ deg ≤ 9 at every vertex (L0), enforced only at one representative per
  vertex orbit, which suffices by invariance;
- α ≤ 9, added lazily (CEGAR). Each SAT model is a graph; a complete
  branch-and-bound finds independent 10-sets S in it, and the clause
  "some pair in S is an edge" is added. That clause is valid for **every**
  graph with α ≤ 9, so no solution is ever lost;
- lex-leader symmetry breaking for normalizer elements of ⟨σ⟩: transpositions
  of fixed points, swaps of aligned cycles, rotations of single cycles, and
  multipliers i ↦ ai. Each such π preserves the problem, so the
  lex-least graph of every orbit survives all these constraints simultaneously.

The loop ends in one of two ways. **WITNESS** means a model has no independent 10-set; it is
then re-checked by two independent α routines, and its existence would mean
R(3,10) = 41. **UNSAT** means no σ-invariant (3,10,40)-graph of this cycle type exists.

### Verification pipeline (for "independently verified")

1. `audit.py` shares no code with the encoder. From (p, k, f) and the list of
   recorded 10-sets (`cutsets.txt`), it re-derives every clause. It uses its own
   orbit arithmetic, a Sinz sequential counter instead of a totalizer, a
   different lex-leader auxiliary encoding, and degree constraints at *every*
   vertex.
2. The standalone CaDiCaL binary refutes the auditor's CNF and emits DRAT
   and LRAT proofs. **drat-trim** and **lrat-trim** check both.
3. Tests:
   - `test_symbreak.py` enumerates every σ-invariant graph exhaustively for 15
     small parameter sets. It checks that each valid graph's normalizer orbit keeps
     a model under symmetry breaking (up to 13,188 valid graphs per case).
   - `test_audit.py` checks that, with edge variables fixed, the auditor's base
     CNF is satisfiable iff the graph is triangle-free with the stated degree bounds.
4. Controls:
   - (3,9,35) with order-7 and order-5 symmetry returns WITNESS (the unique
     (3,9,35)-graph is cyclic on ℤ₃₅).
   - (3,9,36) with a fixed-point-free order-3 symmetry returns UNSAT (R(3,9)=36).
   - `indep.c` reproduces the 3360 independent 8-sets of the (3,9,35)-graph.

**Trusted base.** These results rest on:
- R(3,9) = 36, used only for deg ≥ 4;
- the soundness of the lex-leader argument, plus the exhaustive tests above;
- drat-trim / lrat-trim;
- the correctness of `audit.py`'s encoding, which is small enough to read and is tested.

The results do **not** rely on the unrefereed δ ≥ 5 result or on any other AI-lab
claim.

## Results ledger

See `RESULTS.md` (auto-generated) for the per-case table with timings, cut
counts and proof-check outcomes.
