"""Coverage matrix + minimum sufficient set (greedy weighted set cover)."""
from extraction import resolvable_keys

ROLE_WEIGHT = {"PRIMARY": 0, "SUPPORTING": 1, "SAFETY": 2, "TEST": 3, "CERTIFICATION": 4, "ALLIED": 5}


def build_matrix(requirements: list[dict], verdicts: list[dict]) -> dict:
    keys = resolvable_keys(requirements)
    usable = [v for v in verdicts if v["state"] in ("APPLICABLE", "CONDITIONAL")]
    matrix = {vid: {k: (k in (v.get("covers") or [])) for k in keys} for v in usable for vid in [v["standard_id"]]}
    return {"requirement_keys": keys, "matrix": matrix}


def greedy_minimum_set(requirements: list[dict], verdicts: list[dict]) -> dict:
    keys = resolvable_keys(requirements)
    uncovered = set(keys)
    usable = sorted([v for v in verdicts if v["state"] in ("APPLICABLE", "CONDITIONAL")],
                    key=lambda v: (ROLE_WEIGHT.get(v["role"], 9), v["standard_id"]))
    chosen: list[dict] = []
    covered_by: dict[str, list[str]] = {}
    while uncovered:
        best, best_gain = None, 0
        for v in usable:
            if v in chosen:
                continue
            gain = len(set(v.get("covers", [])) & uncovered)
            if gain > best_gain:
                best, best_gain = v, gain
        if best is None or best_gain == 0:
            break
        chosen.append(best)
        for k in set(best.get("covers", [])) & uncovered:
            covered_by.setdefault(k, []).append(best["standard_id"])
        uncovered -= set(best.get("covers", []))
    covered = set(keys) - uncovered
    pct = round(100.0 * len(covered) / len(keys), 1) if keys else 0.0
    return {
        "selected": [{"standard_id": v["standard_id"], "title": v["title"], "role": v["role"],
                      "state": v["state"], "reason": v["reason"]} for v in chosen],
        "covered_requirements": sorted(covered),
        "uncovered_requirements": sorted(uncovered),
        "coverage_pct": pct,
        "covered_by": covered_by,
    }
