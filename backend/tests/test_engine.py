"""Deterministic engine tests — no network, no LLM."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import applicability
import coverage as cov
import database
import extraction
import graph_builder
import missing as missing_mod
import retrieval
from seed_data import seed

SPEC = ("Procurement of stainless steel gate valves for high-pressure process service. "
        "Body material stainless steel. Pressure rating PN16 with flanged ends. "
        "Process fluid line, hydrostatic testing with inspection required. "
        "Fire-safe performance and fugitive emission control required.")


def setup_module():
    seed()


def reqs():
    return extraction.extract_requirements(SPEC)


def standards():
    return database.fetch_all_standards()


def test_extraction_statuses():
    r = {x["key"]: x for x in reqs()}
    assert r["product"]["status"] == "CONFIRMED"
    assert r["pressure_class"]["value"] == "pn16"
    assert r["temperature"]["status"] == "MISSING"


def test_retrieval_finds_valve_primary():
    idx = retrieval.Index(standards())
    ranked = idx.search(retrieval.expand_query(SPEC, reqs()))
    top_ids = [standards()[i]["standard_id"] for i, _, _, _ in ranked[:5]]
    assert "IS-DEM-VALVE-01" in top_ids


def test_applicability_accepts_primary():
    v = applicability.evaluate_standard(
        database.fetch_standard("IS-DEM-VALVE-01"), reqs())
    assert v["state"] == "APPLICABLE", v


def test_applicability_rejects_water_valve_decoy():
    v = applicability.evaluate_standard(
        database.fetch_standard("IS-DEM-VALVE-WTR-09"), reqs())
    assert v["state"] == "REJECTED"
    assert "Exclud" in v["reason"] or "Condition" in v["reason"]


def test_lifecycle_outdated():
    v = applicability.evaluate_standard(
        database.fetch_standard("IS-DEM-VALVE-OLD-03"), reqs())
    assert v["state"] == "OUTDATED"
    assert v["superseded_by"] == "IS-DEM-VALVE-01"


def test_missing_temperature_blocks_safety_standard():
    v = applicability.evaluate_standard(
        database.fetch_standard("IS-DEM-SAFE-30"), reqs())
    assert v["state"] == "INSUFFICIENT_INFORMATION"
    assert "temperature" in v["blocking_missing"]


def test_missing_engine_ranks_temperature_first():
    r = reqs()
    verdicts = [applicability.evaluate_standard(s, r) for s in standards()
                if s["standard_id"] in ("IS-DEM-SAFE-30", "IS-DEM-SAFE-31", "IS-DEM-MAT-HT-13")]
    m = missing_mod.find_missing(r, verdicts)
    assert m and m[0]["attr"] == "temperature" and m[0]["impact_count"] == 3


def test_coverage_and_minimum_set():
    r = reqs()
    verdicts = [applicability.evaluate_standard(s, r) for s in standards()]
    result = cov.greedy_minimum_set(r, verdicts)
    ids = {s["standard_id"] for s in result["selected"]}
    assert "IS-DEM-VALVE-01" in ids
    assert "IS-DEM-VALVE-WTR-09" not in ids
    assert result["coverage_pct"] > 80


def test_graph_traversal_edges():
    stds = standards()
    g = graph_builder.build_full_graph(stds)
    assert g.has_edge("IS-DEM-VALVE-01", "IS-DEM-TEST-20")
    assert g.has_edge("IS-DEM-VALVE-OLD-03", "IS-DEM-VALVE-01")


def test_counterfactual_pn16_to_pn40_changes_set():
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    sid = c.post("/api/analyze", json={"spec_text": SPEC}).json()["session_id"]
    before = {s["standard_id"] for s in
              c.get(f"/api/sessions/{sid}/coverage").json()["minimum_sufficient_set"]}
    diff = c.post(f"/api/sessions/{sid}/counterfactual",
                  json={"attr": "pressure_class", "new_value": "PN40"}).json()
    after = {s["standard_id"] for s in diff["minimum_sufficient_set"]}
    assert before != after, (before, after)
    assert diff["added"] or diff["removed"]
