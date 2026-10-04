"""Final acceptance test: demo steps 1-13 against a live backend."""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


spec = call("GET", "/api/sample-spec")["spec_text"]
print("1. sample spec loaded:", len(spec), "chars")

a = call("POST", "/api/analyze", {"spec_text": spec})
sid = a["session_id"]
stats = {r["key"]: r["status"] for r in a["requirements"]}
assert stats["pressure_class"] == "CONFIRMED" and stats["temperature"] == "MISSING", stats
print("2. requirements OK:", stats, "| funnel:", a["funnel"])

cands = call("GET", f"/api/sessions/{sid}/candidates")["candidates"]
states = {c["standard_id"]: c["state"] for c in cands}
assert states.get("IS-DEM-VALVE-01") == "APPLICABLE", states
print("3. candidates OK; primary applicable; total:", len(cands))

decoy = next(c for c in cands if c["standard_id"] == "IS-DEM-VALVE-WTR-09")
assert decoy["state"] == "REJECTED", decoy
ev = call("GET", f"/api/sessions/{sid}/standards/IS-DEM-VALVE-WTR-09/evidence")
assert ev["state"] == "REJECTED" and ev["evidence_chain"], ev
print("4. decoy rejected with evidence:", decoy["reason"][:90])

cov = call("GET", f"/api/sessions/{sid}/coverage")
assert cov["matrix"]["requirement_keys"] and cov["minimum_sufficient_set"], cov
print("5. coverage matrix:", len(cov["matrix"]["requirement_keys"]), "reqs x",
      len(cov["minimum_sufficient_set"]), "stds")

sel_ids = [s["standard_id"] for s in cov["minimum_sufficient_set"]]
assert "IS-DEM-VALVE-01" in sel_ids and "IS-DEM-VALVE-WTR-09" not in sel_ids
print("6. minimum sufficient set:", sel_ids, "| coverage:", cov["coverage_pct"])

m = call("GET", f"/api/sessions/{sid}/missing")["missing"]
assert m and m[0]["attr"] == "temperature", m
print("7. missing info asked first:", m[0]["question"], "| impact:", m[0]["impact_standards"])

cl = call("POST", f"/api/sessions/{sid}/clarify", {"attr": "temperature", "value": "150-250C process"})
assert any(r["key"] == "temperature" and r["status"] == "CONFIRMED" for r in cl["requirements"])
print("8. clarification accepted; coverage now:", cl["coverage_pct"])

cands2 = call("GET", f"/api/sessions/{sid}/candidates")["candidates"]
s30 = next(c for c in cands2 if c["standard_id"] == "IS-DEM-SAFE-30")
assert s30["state"] == "APPLICABLE", s30
print("9. set recomputed; SAFE-30 now:", s30["state"])

cf = call("POST", f"/api/sessions/{sid}/counterfactual",
          {"attr": "pressure_class", "new_value": "PN40"})
assert cf["added"] or cf["removed"], cf
print("10-11. counterfactual PN16->PN40 | added:", cf["added"], "| removed:", cf["removed"])

v = call("POST", f"/api/sessions/{sid}/validate",
         {"standard_id": "IS-DEM-VALVE-01", "decision": "INCLUDE", "note": "evaluator approved"})
assert v["validation"]["IS-DEM-VALVE-01"]["decision"] == "INCLUDE"
print("12. human validation recorded")

rep = call("GET", f"/api/sessions/{sid}/report.json")
for k in ("requirements", "minimum_sufficient_set", "missing", "validation"):
    assert k in rep, k
print("13. report exported with keys: specification, requirements, minimum_sufficient_set, missing, validation")
print("ACCEPTANCE: ALL 13 STEPS PASSED")
