export interface Requirement {
  key: string; label: string; value: string | null;
  display_value: string; status: 'CONFIRMED' | 'AMBIGUOUS' | 'MISSING';
  evidence: string; options: string[];
}

export interface Candidate {
  standard_id: string; title: string; product_category: string;
  scope_summary: string; role: string; status: string; revision_year: number;
  superseded_by: string | null; covers: string[]; related: { target: string; rel: string }[];
  state: 'APPLICABLE' | 'CONDITIONAL' | 'REJECTED' | 'OUTDATED' | 'INSUFFICIENT_INFORMATION';
  reason: string; relevance: number;
  evidence_chain: { step: string; detail: string }[];
  blocking_missing: string[];
}

export interface Funnel { candidates_found: number; relevant_count: number; applicable_count: number; sufficient_count: number; }

export interface CoverageData {
  matrix: { requirement_keys: string[]; matrix: Record<string, Record<string, boolean>> };
  minimum_sufficient_set: { standard_id: string; title: string; role: string; state: string; reason: string }[];
  covered: string[]; uncovered: string[]; coverage_pct: number;
  covered_by: Record<string, string[]>;
}

export interface MissingItem {
  attr: string; label: string; question: string; impact_count: number;
  impact_standards: string[]; current_status: string; options: string[];
}

export interface GraphData {
  nodes: { id: string; kind: string; label: string; title?: string; role?: string; state?: string; status?: string }[];
  edges: { from: string; to: string; etype: string }[];
}

const BASE = '';

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + url, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } });
  if (!r.ok) throw new Error((await r.text()) || `HTTP ${r.status}`);
  return r.json();
}

export const api = {
  sample: () => req<{ spec_text: string }>('/api/sample-spec'),
  analyze: (spec_text: string) =>
    req<{ session_id: string; requirements: Requirement[]; funnel: Funnel; missing: MissingItem[]; coverage_pct: number }>('/api/analyze', { method: 'POST', body: JSON.stringify({ spec_text }) }),
  candidates: (sid: string) => req<{ candidates: Candidate[]; funnel: Funnel }>(`/api/sessions/${sid}/candidates`),
  coverage: (sid: string) => req<CoverageData>(`/api/sessions/${sid}/coverage`),
  evidence: (sid: string, std: string) => req<Candidate>(`/api/sessions/${sid}/standards/${std}/evidence`),
  missing: (sid: string) => req<{ missing: MissingItem[] }>(`/api/sessions/${sid}/missing`),
  clarify: (sid: string, attr: string, value: string) =>
    req<{ requirements: Requirement[]; funnel: Funnel; missing: MissingItem[]; coverage_pct: number; minimum_sufficient_set: CoverageData['minimum_sufficient_set'] }>(
      `/api/sessions/${sid}/clarify`, { method: 'POST', body: JSON.stringify({ attr, value }) }),
  counterfactual: (sid: string, attr: string, new_value: string) =>
    req<{ attr: string; old_value: string; new_value: string; added: string[]; removed: string[]; unchanged: string[]; explanation: string; minimum_sufficient_set: CoverageData['minimum_sufficient_set']; coverage_pct: number }>(
      `/api/sessions/${sid}/counterfactual`, { method: 'POST', body: JSON.stringify({ attr, new_value }) }),
  graph: (sid: string) => req<GraphData>(`/api/sessions/${sid}/graph`),
  validate: (sid: string, standard_id: string, decision: string, note = '') =>
    req<{ validation: Record<string, { decision: string; note: string }> }>(`/api/sessions/${sid}/validate`, { method: 'POST', body: JSON.stringify({ standard_id, decision, note }) }),
  reportJsonUrl: (sid: string) => `/api/sessions/${sid}/report.json`,
  reportHtmlUrl: (sid: string) => `/api/sessions/${sid}/report.html`,
};
