# IS-SCOPE — Evaluation

## Methodology

IS-SCOPE is evaluated at three levels. No benchmark numbers are invented — every figure below is produced by running the commands in this file against the prototype.

### 1. Deterministic engine tests (no network, no LLM)

```powershell
cd backend
py -m pytest tests/test_engine.py -q
```

Covers: extraction statuses, retrieval recall of the primary record, applicability accept, decoy rejection, lifecycle outdated, temperature blocking, missing-impact ranking, coverage/minimum-set sanity, graph edges, and an end-to-end PN16→PN40 counterfactual via the API test client.

**Actual result (verified 2026-10-04): `10 passed`.**

### 2. Live acceptance check (13-step hero demo verification)

```powershell
cd backend
py seed_data.py
py -m uvicorn main:app --port 8000
# in a second terminal:
py acceptance_check.py http://localhost:8000
```

Verifies against a running backend: sample spec loads → requirement statuses → primary applicable → decoy rejected with evidence → coverage matrix → minimum set contains VALVE-01 and excludes the decoy → temperature asked first → clarification recomputes → SAFE-30 becomes applicable → counterfactual changes the set → validation recorded → report exports.

**Actual result (verified 2026-10-04): `ACCEPTANCE: ALL 13 STEPS PASSED`**, with the funnel:

```text
53 candidates → 23 relevant → 7 applicable → 3 sufficient
coverage 87.5% → 100% after answering the temperature clarification
counterfactual PN16 → PN40: removed IS-DEM-DIM-12, added IS-DEM-FLANGE-HP-14
```

### 3. Frontend checks

```powershell
cd frontend
npm install
npm run build   # runs tsc --noEmit && vite build
npm run dev     # serves on http://localhost:5173, proxies /api to :8000
```

**Actual result (verified 2026-10-04): production build clean** (`tsc --noEmit` with zero errors; `vite build` succeeded, ~160 KB JS).

## What the metrics mean — and what they do not

| Metric | Meaning | Not a claim of |
|---|---|---|
| funnel 53 → 23 → 7 → 3 | retrieval finds candidates; applicability filters; compiler minimizes | real-world BIS recall/precision |
| coverage 87.5% → 100% | resolvable-requirement coverage before/after clarification in the hero spec | compliance completeness |
| decoy rejected | exclusion logic beats lexical similarity on the curated case | adversarial robustness generally |
| counterfactual delta | deterministic recomputation on requirement change | causal correctness beyond encoded rules |

All figures describe **prototype behavior on synthetic/curated demonstration data**. They demonstrate that the reasoning machinery works end-to-end — not that the system knows real BIS standards.

## Recommended next evaluation (production track)

- Build a labelled set of real procurement specs × expert-judged applicable standards (with BIS authorization).
- Measure: requirement-extraction accuracy, applicability precision/recall, set-cover minimality vs expert sets, clarification impact ranking quality, counterfactual delta correctness.
- Track lifecycle accuracy (superseded/withdrawn detection) as a separate reliability metric.
