"""Missing-information engine: rank unresolved attributes by impact."""
from extraction import LABELS, requirement_map

QUESTION_TEXT = {
    "temperature": "What is the expected operating temperature range?",
    "pressure_class": "What pressure class is required?",
    "material": "What body material is required?",
    "connection": "What end connection is required?",
    "application": "What is the service application?",
    "medium": "What process medium will the valve handle?",
    "testing": "Is pressure testing / inspection required?",
    "safety": "Are fire-safe / emission safety requirements applicable?",
    "product": "What product is being procured?",
    "size": "What valve size is required?",
}


def find_missing(requirements: list[dict], verdicts: list[dict]) -> list[dict]:
    reqmap = requirement_map(requirements)
    impact: dict[str, set] = {}
    for v in verdicts:
        if v["state"] == "INSUFFICIENT_INFORMATION":
            for attr in v.get("blocking_missing", []):
                impact.setdefault(attr, set()).add(v["standard_id"])
    out = []
    for attr, stds in sorted(impact.items(), key=lambda kv: -len(kv[1])):
        req = reqmap.get(attr, {})
        out.append({
            "attr": attr,
            "label": LABELS.get(attr, attr),
            "question": QUESTION_TEXT.get(attr, f"Please provide {attr}."),
            "impact_count": len(stds),
            "impact_standards": sorted(stds),
            "current_status": req.get("status", "MISSING"),
            "options": req.get("options", []) or [],
        })
    # also surface AMBIGUOUS requirements as review items (zero hard blockers but need human eye)
    for r in requirements:
        if r["status"] == "AMBIGUOUS":
            out.append({
                "attr": r["key"], "label": r["label"],
                "question": f"Please confirm: {r['display_value']}",
                "impact_count": 0, "impact_standards": [],
                "current_status": "AMBIGUOUS", "options": r.get("options", []) or [],
            })
    return out
