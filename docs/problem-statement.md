# IS-SCOPE — Problem Statement (SIH26108)

## Official statement

**SIH26108 — AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications.**

## Problem in practice

Procurement specifications in government and industry are often:

- **Incomplete** — operating temperature, pressure class, or test requirements left as "to be confirmed".
- **Ambiguous** — vendor phrases such as "food-grade finish" appear inside an otherwise industrial chemical-plant specification.
- **Technically complex** — a single valve procurement touches product scope, material, dimensions, flanges, testing, safety, and certification — each governed by different standards.

Finding *semantically similar* standards is not enough, because applicability depends on:

| Factor | Example |
|---|---|
| Scope conditions | rated PN16–PN40 vs PN40-only |
| Exclusions | potable-water-only record excludes process/chemical service |
| Lifecycle | superseded 2008 edition must not be recommended |
| Dependencies | primary valve record requires testing and references flanges |
| Requirement coverage | no single standard covers product + material + testing + safety alone |

A generic RAG chatbot retrieves documents that *look* relevant. It cannot answer:

- *Which standards actually apply to this specification?*
- *Do they collectively cover every requirement?*
- *What is missing, and what should we ask next?*
- *If a requirement changes, how does the answer change?*
- *Why was a similar-looking standard rejected — with evidence?*

## What a credible solution must demonstrate

1. Convert free-text procurement text into a structured, auditable requirement profile.
2. Separate **retrieval** (find candidates) from **applicability** (decide what applies).
3. Compile a **minimum sufficient set** — not a ranked list.
4. Ask for missing information in **impact order**, not chatbot order.
5. Recompute deterministically when requirements change (**counterfactual**).
6. Attach **evidence** to every include/reject decision.
7. Keep a **human** as the final authority and export a procurement-ready report.

That is the problem IS-SCOPE is built to solve.
