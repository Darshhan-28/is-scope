"""Final report generation (JSON + printable HTML)."""
import html
from datetime import datetime


def build_report_json(session: dict) -> dict:
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "Prototype dataset — not an official BIS database. AI-assisted recommendation — human validation required.",
        "specification": session["spec_text"],
        "requirements": session["requirements"],
        "funnel": session["funnel"],
        "coverage": session["coverage_result"],
        "minimum_sufficient_set": session["coverage_result"]["selected"],
        "candidates": session["candidates"],
        "missing": session["missing"],
        "graph": session["graph"],
        "validation": session["validation"],
        "counterfactuals": session.get("counterfactuals", []),
    }


def build_report_html(session: dict) -> str:
    rep = build_report_json(session)
    e = html.escape
    rows = "".join(
        f"<tr><td>{e(r['label'])}</td><td>{e(str(r['display_value']))}</td><td>{e(r['status'])}</td></tr>"
        for r in rep["requirements"])
    sel = "".join(
        f"<li><b>{e(s['standard_id'])}</b> [{e(s['role'])}] — {e(s['title'])}<br><span>{e(s['reason'])}</span></li>"
        for s in rep["minimum_sufficient_set"])
    rej = "".join(
        f"<li><b>{e(c['standard_id'])}</b> [{e(c['state'])}] — {e(c['reason'])}</li>"
        for c in rep["candidates"] if c["state"] in ("REJECTED", "OUTDATED"))
    val = "".join(
        f"<li><b>{e(k)}</b>: {e(v['decision'])}{' — ' + e(v.get('note') or '') if v.get('note') else ''}</li>"
        for k, v in rep["validation"].items()) or "<li>No human decisions recorded yet.</li>"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>IS-SCOPE Recommendation Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:32px auto;color:#1a2332}}
.banner{{background:#fff7e6;border:1px solid #e0a800;padding:10px 14px;border-radius:8px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cbd5e1;padding:6px 10px;text-align:left}}
h1{{font-size:22px}}h2{{font-size:16px;margin-top:28px;color:#0f3a5d}}</style></head><body>
<h1>IS-SCOPE — Procurement Standards Recommendation</h1>
<div class="banner"><b>Prototype dataset — not an official BIS database.</b> AI-assisted recommendation — human validation required.</div>
<h2>1. Procurement specification</h2><p>{e(rep['specification'])}</p>
<h2>2. Requirement profile</h2><table><tr><th>Requirement</th><th>Value</th><th>Status</th></tr>{rows}</table>
<h2>3. Funnel</h2><p>{rep['funnel']['candidates_found']} candidates → {rep['funnel']['relevant_count']} relevant → {rep['funnel']['applicable_count']} applicable → {len(rep['minimum_sufficient_set'])} sufficient. Coverage: {rep['coverage']['coverage_pct']}% of resolvable requirements.</p>
<h2>4. Minimum sufficient set</h2><ul>{sel}</ul>
<h2>5. Rejected / outdated candidates</h2><ul>{rej}</ul>
<h2>6. Human validation</h2><ul>{val}</ul>
<p><small>Generated {e(rep['generated_at'])}</small></p></body></html>"""
