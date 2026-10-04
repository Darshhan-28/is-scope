# IS-SCOPE — Solution

## Positioning

> RAG retrieves what looks relevant. IS-SCOPE determines what is applicable, sufficient, and defensible.

IS-SCOPE converts a procurement specification into an **evidence-backed, applicability-checked, coverage-complete set of Indian Standards**, with a human validator as the final authority.

## Core pipeline

```text
Procurement Specification
↓
Requirement Understanding        (regex/rules extraction → CONFIRMED / AMBIGUOUS / MISSING)
↓
Candidate Discovery              (hand-rolled BM25 + TF-IDF cosine blend — retrieval only)
↓
Standards Relationship Graph     (NetworkX: COVERS / REQUIRES / REFERENCES / RELATED_TO / SUPERSEDES / TESTED_BY)
↓
Applicability Engine             (conditions / exclusions / lifecycle → APPLICABLE / CONDITIONAL /
                                  REJECTED / OUTDATED / INSUFFICIENT_INFORMATION + evidence chain)
↓
Coverage Analysis                (requirement × standard matrix)
↓
Standards Set Compiler           (greedy minimum set cover over applicable standards)
↓
Clarification / Counterfactual   (impact-ranked questions; deterministic recomputation on change)
↓
Evidence + Human Validation      (INCLUDE / REJECT / REVIEW per standard)
↓
Procurement-Ready Report         (HTML + JSON)
```

## The three innovations

### 1. Standards Set Compiler

Instead of ranking similar documents, IS-SCOPE compiles a **minimum sufficient applicable set** that covers the procurement requirements while respecting applicability constraints, dependencies, and exclusions.

- Only `APPLICABLE` / `CONDITIONAL` verdicts are eligible — `REJECTED`, `OUTDATED`, and `INSUFFICIENT_INFORMATION` records can never enter the set.
- A greedy weighted set-cover selects the smallest combination that covers all resolvable requirements (role-weighted: PRIMARY → SUPPORTING → SAFETY → TEST → CERTIFICATION).
- The coverage matrix (requirement × standard) and the coverage percentage make sufficiency visible; uncovered requirements are named explicitly instead of hidden.

### 2. Constraint-Driven Clarification

When the specification lacks a decision-critical attribute, IS-SCOPE identifies the missing information with the **highest impact on the standards decision** and asks for that first.

- Every `INSUFFICIENT_INFORMATION` verdict records its `blocking_missing` attributes.
- Missing attributes are ranked by how many standards they block (e.g. unknown temperature blocks 3 safety/material records).
- Answering the question triggers a **real deterministic recomputation** — coverage, verdicts, and the compiled set all update. This is not a chatbot prompt; it is a constraint-resolution step.

### 3. Counterfactual Standards Analysis

When a procurement requirement changes, IS-SCOPE **recomputes the standards set from the deterministic engine** and explains the delta:

- `REMOVED` — standards that no longer satisfy the changed condition, with reasons.
- `ADDED` — standards that newly satisfy it, with reasons.
- `UNCHANGED` — standards unaffected by the change.

Example from the verified demo: `pressure_class PN16 → PN40` removes `IS-DEM-DIM-12` (PN16-bounded) and adds `IS-DEM-FLANGE-HP-14` (PN40-rated), with per-standard reasons drawn from the applicability rules.

## AI vs deterministic boundary

| AI/LLM may assist with | Deterministic logic must control |
|---|---|
| natural-language interpretation | applicability decisions |
| terminology normalization | exclusions |
| synonym expansion | lifecycle / supersession |
| requirement extraction hints | dependency propagation |
| semantic candidate discovery | coverage computation |
| explanation drafting | set compilation |
| | contradiction checks |
| | confidence policy |
| | evidence / provenance |

The LLM must **never** be treated as the regulatory authority. In this prototype the LLM layer (`backend/ai_layer.py`) is an optional terminology-hint stub that returns `None` offline; the deployed demo path is fully deterministic and reproducible.

## Decision-support, not decision-maker

**AI proposes → deterministic reasoning verifies → evidence explains → human validates.**

Every major decision carries an evidence chain (`requirement → rule/condition → standard metadata/relationship → decision`), and the final report records human INCLUDE / REJECT / REVIEW decisions. IS-SCOPE claims no legal or regulatory authority.
