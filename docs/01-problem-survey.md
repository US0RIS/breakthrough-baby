# 1. Problem survey and target selection

Date: 2026-10-18. Literature access in this session is limited to web-search
snippets and public GitHub (arXiv and most journal hosts are blocked by the
sandbox network policy). Every state-of-the-art claim below cites the source it
came from. A claim marked *(secondary)* was seen only in a summary.

## Classification key

| Code | Meaning |
| --- | --- |
| **THM** | Proven impossible. A named theorem forbids it under stated assumptions. |
| **CONJ** | Believed impossible or false, but unproven. |
| **BARRIER** | Proven theorem that rules out a *class of proof techniques*, not the statement. |
| **ENG** | Finite or physical problem. The obstacle is search size, compute or materials, not a theorem. |
| **OPEN** | No consensus on the truth value. |

## The ten candidates

| # | Problem | Status | Responsible theorem / assumption | What could be relaxed |
| --- | --- | --- | --- | --- |
| 1 | P ≠ NP | CONJ + BARRIER | Relativization (Baker–Gill–Solovay 1975), natural proofs (Razborov–Rudich 1997), algebrization (Aaronson–Wigderson 2008) | Barriers bind relativizing/natural/algebrizing proofs only. Non-natural circuit lower bounds remain possible in principle |
| 2 | Rank ≤ 22 for 3×3 matrix multiplication; ω = 2 | OPEN / CONJ | Lower bound 19 over general fields (Bläser 2003); 21 over F₂ (2026 preprints, *secondary*). Laser-method barriers (Ambainis–Filmus–Le Gall; Alman–Williams) | Barriers limit the laser method, not ω. Rank 22 over ℚ/ℂ is not excluded |
| 3 | Hadamard matrix of order 668 | **Resolved Aug 2026** (*secondary*: Epoch AI page, X post); reported construction by Alpöge et al. with Claude | Was ENG: 167 is prime, so compression methods do not apply | Eliminated. The general Hadamard conjecture stays OPEN |
| 4 | R(5,5) = 43? (bounds 43 ≤ R(5,5) ≤ 46) | CONJ (McKay–Radziszowski: none of the 656 known (5,5,42)-graphs extends) | No theorem. Search space is about 2^903 | Witness search would need a fundamentally new structure |
| 5 | **R(3,10): 40 or 41?** | OPEN, ENG | Angeltveit, EJC 32(4) P4.30 (2025): R(3,10) ≤ 41. Exoo 1989: ≥ 40. The obstacle is enumerating (3,9)-graphs on 30–34 vertices | A finite question. A (3,10,40)-graph would prove R(3,10)=41; its nonexistence would prove 40 |
| 6 | Hadwiger–Nelson: χ(ℝ²) ∈ {5,6,7}; is it ≥ 6? | OPEN | de Grey 2018 (≥5); Polymath16 | A 6-chromatic unit-distance graph would be checkable by SAT/DRAT |
| 7 | Navier–Stokes finite-time blow-up (3D) | OPEN (Millennium) | Energy-supercritical scaling. Computer-assisted proofs exist for related models (Chen–Hou: Euler with boundary) | Rigorous interval-arithmetic proof is far beyond 12 h |
| 8 | Kissing numbers / packings in dimensions 9–31 | OPEN, ENG | Linear-programming/SDP upper bounds; constructions | Crowded in 2026: autonomous systems keep improving bounds (arXiv 2609.35051, 2609.21591, *secondary*) |
| 9 | BB(6) | OPEN, probably beyond current mathematics | BB(5) was proven in 2024 (Coq). BB(6) contains Collatz-type "cryptids" | Needs open number-theory problems; not a compute question |
| 10 | Room-temperature ambient-pressure superconductor | ENG / OPEN | No theorem forbids it. Eliashberg-theory heuristics only | Not verifiable by computation alone, so it is excluded by the verification criterion |

**For contrast, proven impossibilities that were not candidates.** No-cloning
and no-signalling follow from the linearity/unitarity of QM plus the Born rule.
Lossless compression of all strings is ruled out by pigeonhole, unconditionally.
Beating Carnot or Landauer on average is ruled out by the second law; the
fluctuation theorems make "on average" the exact relaxable assumption.
Halting is undecidable (Turing). Attacking any of these means attacking the
stated assumption, and none can be tested in software tonight.

## Ranking (1 = worst, 5 = best)

| # | Magnitude | P(meaningful progress, 12 h) | Investigable by code / reasoning | Verifiability | Product |
| --- | --- | --- | --- | --- | --- |
| 5 R(3,10) | 4 | 3 | 5 | 5 | **300** |
| 2 3×3 matmul rank 22 | 5 | 1 | 5 | 5 | 125 |
| 8 Kissing numbers | 2 | 3 | 4 | 5 | 120 |
| 6 Hadwiger–Nelson | 5 | 1 | 4 | 5 | 100 |
| 4 R(5,5) | 4 | 1 | 4 | 5 | 80 |
| 7 Navier–Stokes | 5 | 1 | 3 | 3 | 45 |
| 1 P vs NP | 5 | 1 | 2 | 4 | 40 |
| 9 BB(6) | 3 | 1 | 3 | 4 | 36 |
| 10 RT superconductor | 5 | 1 | 1 | 1 | 5 |
| 3 Hadamard 668 | — | — | — | — | already solved |

"Meaningful progress" for R(3,10) does not mean settling it. It means a new,
checkable theorem about the hypothetical (3,10,40)-graph that narrows where it
can exist, with a nonzero chance that the search finds it.

## Selected target: R(3,10)

**The question.** Does a triangle-free graph on 40 vertices with no
independent set of size 10 exist? If it does, R(3,10) = 41, which would be the
first classical two-colour Ramsey number determined since R(4,5) = 25 (1995).
If it does not, R(3,10) = 40.

**Why "impossible".** This is not a theorem. Goedgebeur–Radziszowski (2013)
called it beyond reach because the gluing method needs every (3,9)-graph on 30–34
vertices. Angeltveit's ≤ 41 proof needed about 1.5 × 10¹¹ intermediate
(3,8)-graphs. The obstacle is search size (ENG), not mathematics.

**What is already known about a hypothetical (3,10,40)-graph G:**
- 4 ≤ δ(G) and Δ(G) ≤ 9, from R(3,9)=36 and independent neighbourhoods.
- No vertex-transitive G, including circulant and Cayley graphs (hraness/algal-lab, Sept 2026, an unrefereed
  AI-lab computation relying on the TransGrp classification).
- δ(G) ≥ 5 (algal-lab, LRAT-checked; relies on uniqueness of the (3,9,35)-graph).
- If G is maximal triangle-free, δ(G) ≥ 6 (Pandey–Ravi, Jan 2026).
- Extending the 43,146,537 known (3,10,39)-graphs by one vertex fails (Angeltveit §7).

**Gap I am attacking.** Nobody appears to have classified candidates with a
*non-transitive* automorphism of prime order. This is the classical method used
on the projective plane of order 10 and the Moore graph of degree 57. For each
prime p and cycle type (k p-cycles, f fixed points), the class gives one of two
outcomes:
- a witness, which would settle R(3,10) = 41 and is checkable in milliseconds, or
- an UNSAT proof, giving the new theorem "a (3,10,40)-graph has no automorphism
  of order p with f fixed points", checkable with DRAT/LRAT proofs.

Each completed case is new, verifiable mathematics. Together they would constrain
|Aut(G)|. The program also searches structured spaces that prior extension
searches never sampled.
