"""Standards relationship graph (NetworkX) + compact session subgraph."""
import networkx as nx

EDGE_TYPES = ("COVERS", "REQUIRES", "REFERENCES", "RELATED_TO", "SUPERSEDES", "TESTED_BY")


def build_full_graph(standards: list[dict]) -> nx.DiGraph:
    g = nx.DiGraph()
    for s in standards:
        g.add_node(s["standard_id"], kind="standard", role=s["role"], title=s["title"])
        for rel in s.get("related", []):
            g.add_edge(s["standard_id"], rel["target"], etype=rel.get("rel", "RELATED_TO"))
        for ref in s.get("normative_references", []):
            if not g.has_edge(s["standard_id"], ref):
                g.add_edge(s["standard_id"], ref, etype="REFERENCES")
        for t in s.get("test_methods", []):
            g.add_edge(s["standard_id"], t, etype="TESTED_BY")
        if s.get("superseded_by"):
            g.add_edge(s["standard_id"], s["superseded_by"], etype="SUPERSEDES")
    return g


def session_subgraph(requirements: list[dict], verdicts: list[dict],
                     selected_ids: list[str], standards: list[dict]) -> dict:
    by_id = {s["standard_id"]: s for s in standards}
    keep = set(selected_ids)
    # include rejected decoy + outdated + conditional neighbours for the story (cap 20 nodes)
    for v in verdicts:
        if v["state"] in ("REJECTED", "OUTDATED", "INSUFFICIENT_INFORMATION") and len(keep) < 20:
            keep.add(v["standard_id"])
    nodes, edges = [], []
    for r in requirements:
        if r["key"] == "size":
            continue
        nodes.append({"id": f"REQ:{r['key']}", "kind": "requirement", "label": r["label"],
                      "status": r["status"]})
    for sid in sorted(keep):
        s = by_id.get(sid)
        if not s:
            continue
        v = next((x for x in verdicts if x["standard_id"] == sid), {})
        nodes.append({"id": sid, "kind": "certification" if s["role"] == "CERTIFICATION"
                      else ("test" if s["role"] == "TEST" else "standard"),
                      "label": sid, "title": s["title"], "role": s["role"],
                      "state": v.get("state")})
        for cov in s.get("covers", []):
            if any(n["id"] == f"REQ:{cov}" for n in nodes):
                edges.append({"from": f"REQ:{cov}", "to": sid, "etype": "COVERS"})
        for rel in s.get("related", []):
            if rel["target"] in keep:
                edges.append({"from": sid, "to": rel["target"], "etype": rel.get("rel", "RELATED_TO")})
        for t in s.get("test_methods", []):
            if t in keep:
                edges.append({"from": sid, "to": t, "etype": "TESTED_BY"})
        if s.get("superseded_by") and s["superseded_by"] in keep:
            edges.append({"from": sid, "to": s["superseded_by"], "etype": "SUPERSEDES"})
    # dedupe edges
    seen, deduped = set(), []
    for e in edges:
        k = (e["from"], e["to"], e["etype"])
        if k not in seen:
            seen.add(k)
            deduped.append(e)
    return {"nodes": nodes, "edges": deduped,
            "legend": ["requirement", "standard", "test", "certification"],
            "edge_types": list(EDGE_TYPES)}
