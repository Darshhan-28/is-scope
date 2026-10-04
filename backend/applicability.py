"""Applicability reasoning — the deterministic decision layer.

An LLM never decides applicability. Every decision is derived here from
standard metadata (conditions / exclusions / lifecycle) crossed with the
extracted requirement profile, and carries a human-readable evidence chain.
"""
from extraction import requirement_map

STATES = ("APPLICABLE", "CONDITIONAL", "REJECTED", "OUTDATED", "INSUFFICIENT_INFORMATION")


def evaluate_standard(standard: dict, requirements: list[dict]) -> dict:
    reqmap = requirement_map(requirements)
    chain: list[dict] = []
    blocking_missing: list[str] = []

    # 1. lifecycle gate
    if standard["status"] in ("SUPERSEDED", "WITHDRAWN"):
        target = standard.get("superseded_by") or "current edition"
        return _verdict(standard, "OUTDATED", 0.0,
                        f"Superseded/withdrawn ({standard['status']}); use {target}.",
                        chain + [{"step": "Lifecycle check",
                                  "detail": f"status={standard['status']}, revision {standard['revision_year']}; superseded by {target}"}],
                        blocking_missing)

    # 2. exclusions -> hard reject
    for rule in standard.get("exclusions", []):
        attr = rule["attr"]
        req = reqmap.get(attr)
        if req and req["value"] and req["value"] in [str(v).lower() for v in rule.get("forbidden", [])]:
            return _verdict(standard, "REJECTED", 0.0,
                            f"Excluded: {req['label']} = '{req['display_value']}' falls under this record's exclusion.",
                            chain + [{"step": "Exclusion check",
                                      "detail": f"{attr}='{req['value']}' is forbidden by {standard['standard_id']}"}],
                            blocking_missing)
        chain.append({"step": "Exclusion check",
                      "detail": f"{attr}: no forbidden value matched"})

    # 3. applicability conditions
    for rule in standard.get("applicability_conditions", []):
        attr = rule["attr"]
        allowed = [str(v).lower() for v in rule.get("allowed", [])]
        req = reqmap.get(attr)
        if req is None or req["value"] is None or req["status"] == "MISSING":
            blocking_missing.append(attr)
            chain.append({"step": f"Condition: {attr}",
                          "detail": f"cannot be determined — '{attr}' is missing from the specification"})
        elif req["value"] not in allowed:
            return _verdict(standard, "REJECTED", 0.0,
                            f"Condition not satisfied: {req['label']} = '{req['display_value']}' is outside the scope ({', '.join(allowed)}).",
                            chain + [{"step": f"Condition: {attr}",
                                      "detail": f"required one of {allowed}; found '{req['value']}'"}],
                            blocking_missing)
        else:
            chain.append({"step": f"Condition: {attr}",
                          "detail": f"'{req['value']}' satisfies scope ({', '.join(allowed)})"})

    if blocking_missing:
        uniq = sorted(set(blocking_missing))
        return _verdict(standard, "INSUFFICIENT_INFORMATION", 0.0,
                        f"Cannot determine applicability — missing: {', '.join(uniq)}.",
                        chain, uniq)

    chain.append({"step": "Decision", "detail": "all scope conditions satisfied; no exclusion triggered"})
    return _verdict(standard, "APPLICABLE", 1.0,
                    "All applicability conditions satisfied; no exclusions triggered.",
                    chain, [])


def _verdict(standard, state, score, reason, chain, blocking):
    return {
        "standard_id": standard["standard_id"],
        "title": standard["title"],
        "product_category": standard["product_category"],
        "scope_summary": standard["scope_summary"],
        "role": standard["role"],
        "status": standard["status"],
        "revision_year": standard["revision_year"],
        "superseded_by": standard.get("superseded_by"),
        "covers": standard.get("covers", []),
        "related": standard.get("related", []),
        "normative_references": standard.get("normative_references", []),
        "test_methods": standard.get("test_methods", []),
        "certification_flag": standard.get("certification_flag", False),
        "state": state,
        "score": score,
        "reason": reason,
        "evidence_chain": chain,
        "blocking_missing": blocking,
        "relevance": 0.0,
        "bm25": 0.0,
        "cosine": 0.0,
    }
