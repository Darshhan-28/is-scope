# IS-SCOPE — Data Strategy

## Prototype data disclaimer

> Prototype data disclaimer: The current demonstration uses a synthetic/curated standards knowledge base and does not represent an official BIS database. Production deployment would require authorized access to relevant BIS/government data sources.

No full BIS standard text is reproduced anywhere in this repository. All records are metadata-style demonstration entries.

## What is in the prototype knowledge base

`backend/seed_data.py` generates the **Prototype Standards Knowledge Base — Demonstration Dataset**:

- **64 records** = 14 curated hero records + 50 broad-catalogue filler records.
- Each record carries only metadata: `standard_id, title, product_category, scope_summary, keywords, applicability_conditions, exclusions, status, revision_year, related_standards, normative_references, test_methods, certification_flag` — plus `role` and `is_synthetic_demo = True`.
- **~18 relationships** across `RELATED_TO / REFERENCES / TESTED_BY / SUPERSEDES` edges (see `graph_builder.py`).

### Curated hero records (the demo story)

| ID | Role | Purpose in demo |
|---|---|---|
| `IS-DEM-VALVE-01` | PRIMARY | correct process-valve record — must be APPLICABLE and selected |
| `IS-DEM-VALVE-02` | PRIMARY | PN40+ range — relevant but not selected at PN16 |
| `IS-DEM-VALVE-WTR-09` | ALLIED (decoy) | high lexical overlap, **must REJECT** via exclusion (potable-water-only vs process service) |
| `IS-DEM-VALVE-OLD-03` | PRIMARY (SUPERSEDED) | must surface as OUTDATED, superseded by VALVE-01 |
| `IS-DEM-MAT-10` | SUPPORTING | stainless material record |
| `IS-DEM-MAT-HT-13` | SUPPORTING | temperature-gated — INSUFFICIENT_INFORMATION until clarified |
| `IS-DEM-FLANGE-11` | SUPPORTING | PN16-bounded flange record |
| `IS-DEM-FLANGE-HP-14` | SUPPORTING | PN40 flange record — enters set only in the PN40 counterfactual |
| `IS-DEM-DIM-12` | SUPPORTING | PN16-bounded dimensions — leaves the set in the PN40 counterfactual |
| `IS-DEM-TEST-20/21` | TEST | testing records |
| `IS-DEM-SAFE-30/31` | SAFETY | temperature-gated — blocked until temperature is clarified |
| `IS-DEM-CERT-40` | CERTIFICATION | certification scheme record |

### Filler records

50 catalogue entries (`IS-DEM-PIPE-50` … `IS-DEM-AC-99`) scoped to their own product categories. Each is deterministically REJECTED for a valve procurement on applicability even when lexical overlap (steel / pressure / test) is high — this is what makes the retrieval funnel (53 candidates found) realistic and the "similarity ≠ applicability" point demonstrable.

## Copyright and sourcing limits

- All titles/summaries are original demonstration paraphrases (each marked "(Demo record)"). No copyrighted BIS text is included or needed.
- Standard IDs use the `IS-DEM-*` namespace so they can never be mistaken for real BIS numbers.

## Production ingestion path (future, out of scope for prototype)

1. Obtain **authorized access** to official BIS/government data sources (licensing required).
2. Ingest official metadata (number, title, scope, status, supersession) through a versioned ETL pipeline with provenance fields.
3. Encode scope conditions / exclusions as structured rules reviewed by domain experts — the applicability engine consumes rules, never raw LLM output.
4. Continuously track lifecycle (confirm/amend/revise/withdraw) so OUTDATED verdicts stay correct.
5. Keep the AI-vs-deterministic boundary: models may assist extraction and drafting; only versioned rules decide applicability.
