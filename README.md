# breakthrough-baby

An overnight research attempt on an open problem. The target is **R(3,10) ∈ {40, 41}**.
The question is whether a triangle-free graph on 40 vertices with no independent
10-set exists.

- `docs/01-problem-survey.md` ranks ten "impossible" problems and explains the target choice.
- `docs/02-symmetry-program.md` gives the lemmas, method and results ledger.
- `r310/` contains the code:
  - `symenc.py` / `search.py`: lazy SAT search over σ-invariant graphs.
  - `audit.py`: independent re-encoding plus DRAT/LRAT proof checking.
  - `test_*.py`: soundness tests.

Statuses used throughout: **conjectured**, **implemented**, **tested**,
**independently verified**.
