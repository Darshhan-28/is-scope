# IS-SCOPE — Demo Script (2 minutes, evaluator path)

## Setup

```powershell
# Backend
cd D:\SIH108\backend
py -m pip install -r requirements.txt
py seed_data.py
py -m uvicorn main:app --port 8000
# Health check: http://localhost:8000/api/health should report 64 standards.

# Frontend (second terminal)
cd D:\SIH108\frontend
npm install
npm run dev
# Open http://localhost:5173 (dev server proxies /api to the backend).
```

No API key, no GPU, no Docker. The deterministic path is the default.

## The 12-beat hero demo

The sample specification (`Sample spec` button in the UI, also `sample_spec.txt`) is an industrial stainless-steel flanged gate valve for high-pressure process service, PN16, with testing + safety required, operating temperature deliberately missing, and an ambiguous "food-grade finish" phrase.

| # | Action | What to observe |
|---|---|---|
| 1 | Click **Load sample specification** → **Analyze** | session created |
| 2 | **Requirement Profile** | temperature `MISSING`, medium `AMBIGUOUS`, rest `CONFIRMED` |
| 3 | **Standard Discovery** funnel | `53 candidates → 23 relevant → 7 applicable` |
| 4 | Open `IS-DEM-VALVE-WTR-09` → **Why rejected?** | `REJECTED` via exclusion — lexical similarity ≠ applicability |
| 5 | Open `IS-DEM-VALVE-OLD-03` | `OUTDATED` — superseded by `IS-DEM-VALVE-01` |
| 6 | **Coverage matrix + Standards Set Compiler** | requirement × standard matrix; minimum sufficient set of 3 (`VALVE-01`, `DIM-12`, `TEST-20`); coverage **87.5%** — safety uncovered |
| 7 | **Missing Information** | temperature asked first (blocks 3 standards: `MAT-HT-13`, `SAFE-30`, `SAFE-31`); pick `150-250C process` → **Submit & recompute** |
| 8 | Recomputed set | coverage **100%**; `SAFE-30` now `APPLICABLE` |
| 9 | **Change Requirement**: `pressure_class` → `PN40` → **Recompute** | `REMOVED: IS-DEM-DIM-12`, `ADDED: IS-DEM-FLANGE-HP-14`, with reasons |
| 10 | **Standards Relationship Graph** | compact session subgraph (COVERS green, SUPERSEDES grey, …) |
| 11 | **Human Validation** | Approve items (INCLUDE / REJECT / REVIEW) — decision support, not auto-approval |
| 12 | **Final Report** | download HTML / JSON: spec, requirements, applicable set, rejected candidates, coverage, lifecycle, dependencies, missing info, evidence, validation state |

## Headless alternative (no browser)

```powershell
cd D:\SIH108\backend
py acceptance_check.py http://localhost:8000
# Expected: ACCEPTANCE: ALL 13 STEPS PASSED
```

## If something goes wrong

- Backend not reachable: confirm `http://localhost:8000/api/health` returns `{"status":"ok","standards":64,…}`.
- Empty DB: run `py seed_data.py` once, then restart uvicorn (lifespan also auto-seeds).
- Frontend proxy errors: start the backend first, then `npm run dev`.
