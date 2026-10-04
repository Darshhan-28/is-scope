import React, { useMemo, useState } from 'react';
import { api } from './api';
import type { Candidate, CoverageData, Funnel, GraphData, MissingItem, Requirement } from './api';

type Phase = 'input' | 'working' | 'results';

const STEPS = ['Procurement Input', 'Requirements', 'Discovery', 'Set Compiler', 'Clarify & What-if', 'Validate', 'Report'];

function stateChip(state: string) {
  const map: Record<string, string> = {
    APPLICABLE: 'c-ok', CONDITIONAL: 'c-warn', REJECTED: 'c-bad',
    OUTDATED: 'c-neutral', INSUFFICIENT_INFORMATION: 'c-info',
    CONFIRMED: 'c-ok', AMBIGUOUS: 'c-warn', MISSING: 'c-bad',
  };
  const icon = state === 'CONFIRMED' || state === 'APPLICABLE' ? '✓ ' : state === 'MISSING' ? '⚠ ' : state === 'AMBIGUOUS' ? '? ' : '';
  return <span className={`chip ${map[state] || 'c-neutral'}`}>{icon}{state.replace(/_/g, ' ')}</span>;
}

function GraphView({ graph }: { graph: GraphData }) {
  const W = 920, H = 380;
  const reqs = graph.nodes.filter(n => n.kind === 'requirement');
  const stds = graph.nodes.filter(n => n.kind !== 'requirement');
  const pos: Record<string, { x: number; y: number }> = {};
  reqs.forEach((n, i) => { pos[n.id] = { x: 110, y: 40 + i * ((H - 60) / Math.max(1, reqs.length - 1 || 1)) }; });
  const cols = 3;
  stds.forEach((n, i) => {
    const c = i % cols, r = Math.floor(i / cols);
    pos[n.id] = { x: 360 + c * 250, y: 60 + r * 90 };
  });
  const color = (n: { kind: string; state?: string }) =>
    n.kind === 'requirement' ? '#0e6aa8' : n.state === 'REJECTED' ? '#b3362b' : n.state === 'OUTDATED' ? '#8a94a6' : n.state === 'INSUFFICIENT_INFORMATION' ? '#b7791f' : '#1a7f4b';
  return (
    <div className="graph-box">
      <svg width={W} height={Math.max(H, 120 + stds.length * 30)} style={{ maxWidth: '100%' }}>
        {graph.edges.map((e, i) => {
          const a = pos[e.from], b = pos[e.to];
          if (!a || !b) return null;
          return (
            <g key={i}>
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={e.etype === 'COVERS' ? '#1a7f4b' : e.etype === 'SUPERSEDES' ? '#8a94a6' : '#0e6aa8'} strokeWidth={e.etype === 'COVERS' ? 2 : 1.2} strokeDasharray={e.etype === 'RELATED_TO' ? '5 4' : ''} opacity={0.75} />
            </g>
          );
        })}
        {graph.nodes.map(n => {
          const p = pos[n.id];
          if (!p) return null;
          return (
            <g key={n.id}>
              <rect x={p.x - 92} y={p.y - 16} width={184} height={34} rx={8} fill="#fff" stroke={color(n)} strokeWidth={2} />
              <text x={p.x} y={p.y - 1} textAnchor="middle" fontSize={10.5} fontWeight={700} fill={color(n)}>{n.label.length > 26 ? n.label.slice(0, 25) + '…' : n.label}</text>
              <text x={p.x} y={p.y + 12} textAnchor="middle" fontSize={9} fill="#5b6b82">{n.kind}{n.state ? ` · ${n.state}` : n.status ? ` · ${n.status}` : ''}</text>
              <title>{n.title || n.label}</title>
            </g>
          );
        })}
      </svg>
      <div className="progress">Edges: COVERS (green solid) · REQUIRES/REFERENCES/TESTED_BY (blue) · RELATED_TO (dashed) · SUPERSEDES (grey). Hover a node for its full title.</div>
    </div>
  );
}

export default function App() {
  const [phase, setPhase] = useState<Phase>('input');
  const [spec, setSpec] = useState('');
  const [progress, setProgress] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [sid, setSid] = useState('');
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [funnel, setFunnel] = useState<Funnel | null>(null);
  const [coveragePct, setCoveragePct] = useState(0);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [missing, setMissing] = useState<MissingItem[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [drawer, setDrawer] = useState<Candidate | null>(null);
  const [validation, setValidation] = useState<Record<string, { decision: string; note: string }>>({});
  const [diff, setDiff] = useState<any>(null);
  const [cfAttr, setCfAttr] = useState('pressure_class');
  const [cfVal, setCfVal] = useState('PN40');
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const stepIdx = phase === 'input' ? 0 : drawer ? 3 : 3;

  async function analyze() {
    setError('');
    if (spec.trim().length < 20) { setError('Paste a fuller procurement specification (at least a few lines).'); return; }
    setPhase('working');
    setProgress(['Understanding specification…']);
    try {
      const tick = (m: string) => setProgress(p => [...p, m]);
      const r = await api.analyze(spec);
      tick('Extracting requirements…'); tick('Searching standards…');
      setSid(r.session_id); setRequirements(r.requirements); setFunnel(r.funnel);
      setMissing(r.missing); setCoveragePct(r.coverage_pct);
      tick('Checking applicability…');
      const [c, cov, g] = await Promise.all([api.candidates(r.session_id), api.coverage(r.session_id), api.graph(r.session_id)]);
      setCandidates(c.candidates); setCoverage(cov); setGraph(g);
      tick('Building coverage…');
      setPhase('results');
    } catch (e: any) {
      setError(e.message || 'Analysis failed. Is the backend running on :8000?');
      setPhase('input');
    }
  }

  async function refreshSession() {
    const [c, cov, g, m] = await Promise.all([api.candidates(sid), api.coverage(sid), api.graph(sid), api.missing(sid)]);
    setCandidates(c.candidates); setFunnel(c.funnel); setCoverage(cov); setGraph(g); setMissing(m.missing);
    setCoveragePct(cov.coverage_pct);
  }

  async function answerMissing(attr: string) {
    const val = answers[attr];
    if (!val) return;
    const r = await api.clarify(sid, attr, val);
    setRequirements(r.requirements); setFunnel(r.funnel); setMissing(r.missing); setCoveragePct(r.coverage_pct);
    await refreshSession();
  }

  async function runCounterfactual() {
    const d = await api.counterfactual(sid, cfAttr, cfVal);
    setDiff(d);
  }

  async function decide(std: string, decision: string) {
    const r = await api.validate(sid, std, decision);
    setValidation(r.validation);
  }

  const kpis = useMemo(() => funnel ? [
    { n: String(funnel.applicable_count), l: 'APPLICABLE STANDARDS' },
    { n: String(funnel.relevant_count), l: 'CANDIDATES VALIDATED' },
    { n: String(missing.filter(m => m.impact_count > 0).length), l: 'CLARIFICATIONS REQUIRED' },
    { n: `${coveragePct}%`, l: 'RESOLVABLE REQUIREMENT COVERAGE' },
  ] : [], [funnel, missing, coveragePct]);

  return (
    <>
      <div className="topbar">
        <h1>IS-SCOPE</h1>
        <span className="tag">From Procurement Specification → Applicable Standards Set · SIH 2026 · PS SIH26108</span>
      </div>
      <div className="disclaimer"><b>Prototype Standards Knowledge Base — Demonstration Dataset.</b> Prototype dataset — not an official BIS database. Metadata-style demo records only. AI-assisted recommendation — human validation required.</div>
      <div className="layout">
        <div className="stepper">{STEPS.map((s, i) => (
          <span key={s} className={`step ${phase === 'results' && i <= stepIdx + 3 ? 'done' : phase !== 'input' && i === 0 ? 'done' : ''}`}>{i + 1}. {s}</span>
        ))}</div>
        {error && <div className="err">{error}</div>}

        {phase === 'input' && (
          <div className="card">
            <h2>Procurement Specification</h2>
            <div className="sub">Paste the procurement text (material, pressure class, connections, testing, safety). Demo dataset: synthetic / curated.</div>
            <textarea className="spec" value={spec} onChange={e => setSpec(e.target.value)} placeholder="e.g. Procurement of stainless steel gate valves for high-pressure process service…" />
            <div className="row" style={{ marginTop: 10 }}>
              <button className="ghost" onClick={async () => { const s = await api.sample(); setSpec(s.spec_text); }}>Load sample specification</button>
              <label className="ghost" style={{ border: '1px solid var(--navy)', borderRadius: 7, padding: '8px 14px', fontSize: 14, color: 'var(--navy)', cursor: 'pointer' }}>
                Upload .txt <input type="file" accept=".txt" hidden onChange={async e => { const f = e.target.files?.[0]; if (f) setSpec(await f.text()); }} />
              </label>
              <button onClick={analyze}>Analyze →</button>
            </div>
          </div>
        )}

        {phase === 'working' && (
          <div className="card"><h2>Analyzing…</h2><div className="progress">{progress.map((p, i) => <div key={i}>▸ {p}</div>)}</div></div>
        )}

        {phase === 'results' && (
          <>
            <div className="kpi">{kpis.map(k => <div className="box" key={k.l}><div className="n">{k.n}</div><div className="l">{k.l}</div></div>)}</div>

            <div className="card">
              <h2>Requirement Profile</h2>
              <div className="sub">Structured extraction — the system states what is missing instead of guessing.</div>
              <div className="grid3">{requirements.filter(r => r.key !== 'size').map(r => (
                <div className="std-card" key={r.key}><div className="head"><b>{r.label}</b>{stateChip(r.status)}</div>
                  <div style={{ marginTop: 6, fontSize: 14 }}>{r.display_value}</div>
                  <div className="progress">{r.evidence}</div></div>
              ))}</div>
            </div>

            <div className="card">
              <h2>Standard Discovery</h2>
              <div className="funnel"><b>{funnel?.candidates_found} candidates found</b><span className="arrow">↓ lexical + semantic retrieval</span><b>{funnel?.relevant_count} potentially relevant</b><span className="arrow">↓ applicability analysis</span><b>{funnel?.applicable_count} applicable candidates</b></div>
              <div className="sub">Semantic similarity alone is not enough — each card carries an applicability verdict with a reason.</div>
              {candidates.map(c => (
                <div className="std-card" key={c.standard_id}>
                  <div className="head"><span className="id">{c.standard_id}</span>{stateChip(c.state)}</div>
                  <div style={{ fontSize: 14, margin: '4px 0' }}>{c.title}</div>
                  <div className="progress">relevance {c.relevance.toFixed(3)} · {c.role} · {c.status} ({c.revision_year}) · {c.reason}</div>
                  <div className="row" style={{ marginTop: 6 }}>
                    <button className="small ghost" onClick={() => setDrawer(c)}>{c.state === 'REJECTED' || c.state === 'OUTDATED' ? 'Why rejected?' : 'Why included?'}</button>
                  </div>
                </div>
              ))}
            </div>

            {coverage && (
              <div className="card">
                <h2>Standards Set Compiler</h2>
                <div className="sub">Requirement-to-standard coverage matrix, then the minimum sufficient set (greedy set cover over applicable standards).</div>
                <table className="matrix">
                  <thead><tr><th>Requirement</th>{coverage.minimum_sufficient_set.map(s => <th key={s.standard_id}>{s.standard_id.replace('IS-DEM-', '')}<br /><small>{s.role}</small></th>)}</tr></thead>
                  <tbody>{coverage.matrix.requirement_keys.map(k => (
                    <tr key={k}><td>{k}</td>{coverage.minimum_sufficient_set.map(s => (
                      <td key={s.standard_id} className={coverage.matrix.matrix[s.standard_id]?.[k] ? 'yes' : 'no'}>{coverage.matrix.matrix[s.standard_id]?.[k] ? '✓' : '–'}</td>
                    ))}</tr>
                  ))}</tbody>
                </table>
                <div className="funnel" style={{ marginTop: 12 }}><span>{funnel?.candidates_found} candidates</span><span className="arrow">↓</span><span>{funnel?.relevant_count} relevant</span><span className="arrow">↓</span><span>{funnel?.applicable_count} applicable</span><span className="arrow">↓</span><b>{funnel?.sufficient_count} sufficient</b></div>
                <h3>Minimum sufficient set — coverage {coverage.coverage_pct}% of currently resolvable requirements</h3>
                {coverage.minimum_sufficient_set.map(s => (
                  <div className="std-card" key={s.standard_id}><div className="head"><span className="id">{s.standard_id} [{s.role}]</span>{stateChip(s.state)}</div>
                    <div style={{ fontSize: 14 }}>{s.title}</div><div className="progress">{s.reason}</div></div>
                ))}
                {coverage.uncovered.length > 0 && <div className="progress">Uncovered (needs clarification): {coverage.uncovered.join(', ')}</div>}
              </div>
            )}

            <div className="grid2">
              <div className="card">
                <h2>Missing Information</h2>
                <div className="sub">The engine asks the highest-impact clarification first — and recomputation is real.</div>
                {missing.length === 0 && <div className="progress">No missing information. All conditions resolvable.</div>}
                {missing.map(m => (
                  <div className="std-card" key={m.attr}>
                    <div className="head"><b>⚠ {m.label}</b><span className="chip c-info">{m.impact_count} standards depend on this</span></div>
                    <div style={{ fontSize: 14, margin: '4px 0' }}>{m.question}</div>
                    {m.impact_standards.length > 0 && <div className="progress">Impact: {m.impact_standards.join(', ')}</div>}
                    <div className="row" style={{ marginTop: 6 }}>
                      {m.options.length > 0 ? (
                        <select value={answers[m.attr] || ''} onChange={e => setAnswers({ ...answers, [m.attr]: e.target.value })}>
                          <option value="">— choose —</option>{m.options.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                      ) : (
                        <input className="txt" placeholder="Type value…" value={answers[m.attr] || ''} onChange={e => setAnswers({ ...answers, [m.attr]: e.target.value })} />
                      )}
                      <button className="small" onClick={() => answerMissing(m.attr)}>Submit & recompute</button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="card">
                <h2>Change Requirement (counterfactual)</h2>
                <div className="sub">Modify one attribute and recompute — proves constraint reasoning, not cached RAG.</div>
                <div className="row">
                  <select value={cfAttr} onChange={e => setCfAttr(e.target.value)}>
                    <option value="pressure_class">Pressure Class</option>
                    <option value="material">Material</option>
                    <option value="connection">Connection</option>
                    <option value="temperature">Temperature</option>
                  </select>
                  <input className="txt" value={cfVal} onChange={e => setCfVal(e.target.value)} style={{ width: 160 }} />
                  <button className="small" onClick={runCounterfactual}>Recompute standards</button>
                </div>
                {diff && (
                  <div style={{ marginTop: 10, fontSize: 14 }}>
                    <b>Standards set changed</b> ({diff.attr}: {String(diff.old_value)} → {diff.new_value})
                    <div>REMOVED: {diff.removed.join(', ') || '—'}</div>
                    <div>ADDED: {diff.added.join(', ') || '—'}</div>
                    <div>UNCHANGED: {diff.unchanged.join(', ') || '—'}</div>
                    <div className="progress">{diff.explanation}</div>
                  </div>
                )}
              </div>
            </div>

            {graph && (
              <div className="card">
                <h2>Standards Relationship Graph</h2>
                <div className="sub">Why are these standards connected? Compact subgraph of the decision.</div>
                <GraphView graph={graph} />
              </div>
            )}

            <div className="card">
              <h2>Human Validation — Proposed Standards Set</h2>
              <div className="sub">AI-assisted recommendation — human validation required. No regulatory approval is claimed.</div>
              {(coverage?.minimum_sufficient_set || []).map(s => (
                <div className="std-card" key={s.standard_id}>
                  <div className="head"><span className="id">{s.standard_id}</span><span className="chip c-neutral">{validation[s.standard_id]?.decision || 'PENDING'}</span></div>
                  <div className="row" style={{ marginTop: 6 }}>
                    <button className="small" onClick={() => decide(s.standard_id, 'INCLUDE')}>Include</button>
                    <button className="small ghost" onClick={() => decide(s.standard_id, 'REJECT')}>Reject</button>
                    <button className="small ghost" onClick={() => decide(s.standard_id, 'REVIEW')}>Review</button>
                    <button className="small ghost" onClick={async () => setDrawer(await api.evidence(sid, s.standard_id))}>Why?</button>
                  </div>
                </div>
              ))}
              {Object.keys(validation).length > 0 && <div className="progress">Final validated set: {Object.entries(validation).filter(([, v]) => v.decision === 'INCLUDE').map(([k]) => k).join(', ') || '—'}</div>}
            </div>

            <div className="grid2">
              <div className="card">
                <h2>Final Report</h2>
                <div className="sub">Specification, requirement profile, applicable set, rejected candidates, coverage, evidence, lifecycle, validation status.</div>
                <div className="row">
                  <a href={api.reportHtmlUrl(sid)} target="_blank" rel="noreferrer"><button className="ghost">Download HTML report</button></a>
                  <a href={api.reportJsonUrl(sid)} target="_blank" rel="noreferrer"><button className="ghost">Download JSON</button></a>
                  <button className="ghost" onClick={() => { setPhase('input'); setSpec(''); setDiff(null); setDrawer(null); }}>↺ New analysis</button>
                </div>
              </div>
              <div className="card">
                <h2>Traditional RAG vs IS-SCOPE</h2>
                <div className="compare">
                  <div className="col"><b>Traditional RAG</b><br />Retrieve → Rank → Explain</div>
                  <div className="col"><b>IS-SCOPE</b><br />Understand → Discover → Validate → Cover → Optimize → Explain → Validate</div>
                </div>
                <div className="footer-note">Other systems retrieve standards. IS-SCOPE determines which standards actually apply, what they collectively cover, what is missing, and how the set changes when requirements change.</div>
              </div>
            </div>
          </>
        )}
      </div>

      {drawer && (
        <>
          <div className="overlay" onClick={() => setDrawer(null)} />
          <div className="drawer">
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <h2 style={{ margin: 0 }}>Why {drawer.standard_id}?</h2>
              <button className="small ghost" onClick={() => setDrawer(null)}>Close</button>
            </div>
            <p style={{ fontSize: 14 }}>{drawer.title}</p>
            <p>{stateChip(drawer.state)} <span className="chip c-neutral">{drawer.status} · {drawer.revision_year}</span></p>
            <p style={{ fontSize: 14 }}><b>Decision reason:</b> {drawer.reason}</p>
            <div className="evidence">{drawer.evidence_chain.map((s, i) => (
              <div className="estep" key={i}><b>{i + 1}. {s.step}</b><br /><span className="progress">{s.detail}</span></div>
            ))}</div>
            {drawer.blocking_missing.length > 0 && <p style={{ fontSize: 13 }}>⛔ Blocked by missing: {drawer.blocking_missing.join(', ')}</p>}
            <p className="progress">Evidence source: prototype dataset record {drawer.standard_id} (synthetic demo metadata, not official BIS text). Relevance: lexical+semantic blend {drawer.relevance.toFixed(3)} — shown for transparency, never the decision basis.</p>
            {drawer.state === 'REJECTED' && <p style={{ fontSize: 14 }}><b>Semantic similarity is not enough:</b> high lexical overlap did not satisfy the applicability constraint, so this candidate is excluded from the final set.</p>}
          </div>
        </>
      )}
    </>
  );
}
