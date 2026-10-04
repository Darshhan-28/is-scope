"""IS-SCOPE FastAPI backend — deterministic standards decision engine."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uuid

import applicability
import coverage as cov
import database
import extraction
import graph_builder
import missing as missing_mod
import report as report_mod
import retrieval
from ai_layer import normalize_with_llm

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    if database.count_standards() == 0:
        from seed_data import seed
        seed()
    yield


app = FastAPI(title="IS-SCOPE API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SESSIONS: dict[str, dict] = {}
RELEVANCE_THRESHOLD = 0.12
MAX_SPEC_LENGTH = 20000

SAMPLE_SPEC = (
    "Procurement of stainless steel gate valves for high-pressure process service in our chemical plant. "
    "Body material shall be stainless steel. Pressure rating PN16 with flanged ends. "
    "Valves are required in the process fluid line (vendor mentions food-grade finish) and must undergo "
    "hydrostatic pressure testing with full inspection. Fire-safe performance and fugitive emission control "
    "are required for safety compliance. Operating temperature range will be confirmed by the process team."
)


class AnalyzeIn(BaseModel):
    spec_text: str


class ClarifyIn(BaseModel):
    attr: str
    value: str


class CounterfactualIn(BaseModel):
    attr: str
    new_value: str


class ValidateIn(BaseModel):
    standard_id: str
    decision: str  # INCLUDE | REJECT | REVIEW
    note: str = ""


def _pipeline(spec_text: str) -> dict:
    standards = database.fetch_all_standards()
    hints = normalize_with_llm(spec_text)
    requirements = extraction.extract_requirements(spec_text, llm_hints=hints)
    query = retrieval.expand_query(spec_text, requirements)
    index = retrieval.Index(standards)
    ranked = index.search(query)
    score_by_id = {standards[i]["standard_id"]: (blend, b, c) for i, blend, b, c in ranked}
    # funnel: candidates_found = everything with a whisper of signal
    candidates_found = [s for s in standards if score_by_id[s["standard_id"]][0] > 0.02]
    relevant = [s for s in standards if score_by_id[s["standard_id"]][0] >= RELEVANCE_THRESHOLD]
    # applicability over relevant + any curated hero records (so decoy/outdated story always visible)
    hero_ids = {"IS-DEM-VALVE-01", "IS-DEM-VALVE-02", "IS-DEM-VALVE-WTR-09",
                "IS-DEM-VALVE-OLD-03", "IS-DEM-MAT-10", "IS-DEM-MAT-HT-13",
                "IS-DEM-FLANGE-11", "IS-DEM-FLANGE-HP-14", "IS-DEM-DIM-12",
                "IS-DEM-TEST-20", "IS-DEM-TEST-21", "IS-DEM-SAFE-30",
                "IS-DEM-SAFE-31", "IS-DEM-CERT-40"}
    eval_set = {s["standard_id"]: s for s in relevant}
    for s in standards:
        if s["standard_id"] in hero_ids:
            eval_set[s["standard_id"]] = s
    verdicts = []
    for s in eval_set.values():
        v = applicability.evaluate_standard(s, requirements)
        blend, b, c = score_by_id[s["standard_id"]]
        v["relevance"] = blend
        v["bm25"] = b
        v["cosine"] = c
        verdicts.append(v)
    verdicts.sort(key=lambda v: ({"APPLICABLE": 0, "CONDITIONAL": 1, "INSUFFICIENT_INFORMATION": 2,
                                  "REJECTED": 3, "OUTDATED": 4}.get(v["state"], 5), -v["relevance"]))
    matrix = cov.build_matrix(requirements, verdicts)
    result = cov.greedy_minimum_set(requirements, verdicts)
    miss = missing_mod.find_missing(requirements, verdicts)
    graph = graph_builder.session_subgraph(
        requirements, verdicts, [s["standard_id"] for s in result["selected"]], standards)
    applicable = sum(1 for v in verdicts if v["state"] in ("APPLICABLE", "CONDITIONAL"))
    return {
        "requirements": requirements, "candidates": verdicts,
        "funnel": {"candidates_found": len(candidates_found),
                   "relevant_count": len(verdicts),
                   "applicable_count": applicable,
                   "sufficient_count": len(result["selected"])},
        "matrix": matrix, "coverage_result": result, "missing": miss, "graph": graph,
    }


def _get_session(sid: str) -> dict:
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404, "unknown session")
    return s


@app.get("/api/health")
def health():
    return {"status": "ok", "standards": database.count_standards(),
            "disclaimer": "Prototype dataset — not an official BIS database."}


@app.get("/api/sample-spec")
def sample_spec():
    return {"spec_text": SAMPLE_SPEC}


@app.post("/api/analyze")
def analyze(body: AnalyzeIn):
    if not body.spec_text or len(body.spec_text.strip()) < 20:
        raise HTTPException(400, "spec_text too short — paste a fuller procurement specification")
    if len(body.spec_text) > MAX_SPEC_LENGTH:
        raise HTTPException(400, f"spec_text too long — limit is {MAX_SPEC_LENGTH} characters")
    sid = uuid.uuid4().hex[:12]
    pipe = _pipeline(body.spec_text.strip())
    SESSIONS[sid] = {"session_id": sid, "spec_text": body.spec_text.strip(),
                     "validation": {}, "counterfactuals": [], **pipe}
    s = SESSIONS[sid]
    return {"session_id": sid, "requirements": s["requirements"], "funnel": s["funnel"],
            "missing": s["missing"], "coverage_pct": s["coverage_result"]["coverage_pct"]}


@app.get("/api/sessions/{sid}/candidates")
def candidates(sid: str):
    s = _get_session(sid)
    return {"candidates": s["candidates"], "funnel": s["funnel"]}


@app.get("/api/sessions/{sid}/coverage")
def coverage(sid: str):
    s = _get_session(sid)
    return {"matrix": s["matrix"], "minimum_sufficient_set": s["coverage_result"]["selected"],
            "covered": s["coverage_result"]["covered_requirements"],
            "uncovered": s["coverage_result"]["uncovered_requirements"],
            "coverage_pct": s["coverage_result"]["coverage_pct"],
            "covered_by": s["coverage_result"]["covered_by"]}


@app.get("/api/sessions/{sid}/standards/{std_id}/evidence")
def evidence(sid: str, std_id: str):
    s = _get_session(sid)
    v = next((c for c in s["candidates"] if c["standard_id"] == std_id), None)
    if not v:
        raise HTTPException(404, "standard not in candidate set")
    return v


@app.get("/api/sessions/{sid}/missing")
def get_missing(sid: str):
    return {"missing": _get_session(sid)["missing"]}


@app.post("/api/sessions/{sid}/clarify")
def clarify(sid: str, body: ClarifyIn):
    s = _get_session(sid)
    # patch requirement value deterministically
    updated = False
    for r in s["requirements"]:
        if r["key"] == body.attr:
            from extraction import _canon
            r["value"] = _canon(body.attr, body.value)
            r["display_value"] = body.value
            r["status"] = "CONFIRMED"
            r["evidence"] = "provided via clarification question"
            updated = True
    if not updated:
        raise HTTPException(400, f"unknown requirement attr '{body.attr}'")
    pipe = _pipeline_with_requirements(s["spec_text"], s["requirements"])
    s.update(pipe)
    return {"requirements": s["requirements"], "funnel": s["funnel"],
            "missing": s["missing"], "coverage_pct": s["coverage_result"]["coverage_pct"],
            "minimum_sufficient_set": s["coverage_result"]["selected"]}


def _pipeline_with_requirements(spec_text: str, requirements: list[dict]) -> dict:
    """Re-run discovery→applicability→coverage with a patched requirement profile."""
    standards = database.fetch_all_standards()
    query = retrieval.expand_query(spec_text, requirements)
    index = retrieval.Index(standards)
    ranked = index.search(query)
    score_by_id = {standards[i]["standard_id"]: (blend, b, c) for i, blend, b, c in ranked}
    candidates_found = [x for x in standards if score_by_id[x["standard_id"]][0] > 0.02]
    relevant = [x for x in standards if score_by_id[x["standard_id"]][0] >= RELEVANCE_THRESHOLD]
    hero_ids = {"IS-DEM-VALVE-01", "IS-DEM-VALVE-02", "IS-DEM-VALVE-WTR-09",
                "IS-DEM-VALVE-OLD-03", "IS-DEM-MAT-10", "IS-DEM-MAT-HT-13",
                "IS-DEM-FLANGE-11", "IS-DEM-FLANGE-HP-14", "IS-DEM-DIM-12",
                "IS-DEM-TEST-20", "IS-DEM-TEST-21", "IS-DEM-SAFE-30",
                "IS-DEM-SAFE-31", "IS-DEM-CERT-40"}
    eval_set = {x["standard_id"]: x for x in relevant}
    for x in standards:
        if x["standard_id"] in hero_ids:
            eval_set[x["standard_id"]] = x
    verdicts = []
    for x in eval_set.values():
        v = applicability.evaluate_standard(x, requirements)
        blend, b, c = score_by_id[x["standard_id"]]
        v["relevance"] = blend
        v["bm25"] = b
        v["cosine"] = c
        verdicts.append(v)
    verdicts.sort(key=lambda v: ({"APPLICABLE": 0, "CONDITIONAL": 1, "INSUFFICIENT_INFORMATION": 2,
                                  "REJECTED": 3, "OUTDATED": 4}.get(v["state"], 5), -v["relevance"]))
    result = cov.greedy_minimum_set(requirements, verdicts)
    graph = graph_builder.session_subgraph(
        requirements, verdicts, [t["standard_id"] for t in result["selected"]], standards)
    applicable = sum(1 for v in verdicts if v["state"] in ("APPLICABLE", "CONDITIONAL"))
    return {"candidates": verdicts,
            "funnel": {"candidates_found": len(candidates_found), "relevant_count": len(verdicts),
                       "applicable_count": applicable, "sufficient_count": len(result["selected"])},
            "matrix": cov.build_matrix(requirements, verdicts),
            "coverage_result": result,
            "missing": missing_mod.find_missing(requirements, verdicts), "graph": graph}


@app.post("/api/sessions/{sid}/counterfactual")
def counterfactual(sid: str, body: CounterfactualIn):
    s = _get_session(sid)
    import copy
    patched = copy.deepcopy(s["requirements"])
    old = next((r["display_value"] for r in patched if r["key"] == body.attr), None)
    for r in patched:
        if r["key"] == body.attr:
            from extraction import _canon
            r["value"] = _canon(body.attr, body.new_value)
            r["display_value"] = body.new_value
            r["status"] = "CONFIRMED"
            r["evidence"] = "modified via counterfactual (Change Requirement)"
    before_ids = {t["standard_id"] for t in s["coverage_result"]["selected"]}
    pipe = _pipeline_with_requirements(s["spec_text"], patched)
    after_ids = {t["standard_id"] for t in pipe["coverage_result"]["selected"]}
    changed_std = next((c for c in pipe["candidates"]
                        if c["standard_id"] in (after_ids ^ before_ids)), None)
    diff = {"attr": body.attr, "old_value": old, "new_value": body.new_value,
            "added": sorted(after_ids - before_ids), "removed": sorted(before_ids - after_ids),
            "unchanged": sorted(before_ids & after_ids),
            "explanation": ("Applicability changed because the modified "
                            f"{body.attr} condition affected standards' applicability rules."
                            + (f" e.g. {changed_std['standard_id']}: {changed_std['reason']}"
                               if changed_std else ""))}
    s["counterfactuals"].append(diff)
    return {**diff, "minimum_sufficient_set": pipe["coverage_result"]["selected"],
            "coverage_pct": pipe["coverage_result"]["coverage_pct"]}


@app.get("/api/sessions/{sid}/graph")
def graph(sid: str):
    return _get_session(sid)["graph"]


@app.post("/api/sessions/{sid}/validate")
def validate(sid: str, body: ValidateIn):
    s = _get_session(sid)
    if body.decision not in ("INCLUDE", "REJECT", "REVIEW"):
        raise HTTPException(400, "decision must be INCLUDE | REJECT | REVIEW")
    if not any(c["standard_id"] == body.standard_id for c in s["candidates"]):
        raise HTTPException(404, "unknown standard id — invented IDs are rejected")
    s["validation"][body.standard_id] = {"decision": body.decision, "note": body.note}
    return {"validation": s["validation"]}


@app.get("/api/sessions/{sid}/report.json")
def report_json(sid: str):
    return JSONResponse(report_mod.build_report_json(_get_session(sid)))


@app.get("/api/sessions/{sid}/report.html")
def report_html(sid: str):
    return HTMLResponse(report_mod.build_report_html(_get_session(sid)))
