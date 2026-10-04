# IS-SCOPE — Limitations (read before judging)

1. **Prototype dataset, not a BIS corpus.** 64 synthetic/curated demo records (`IS-DEM-*`) stand in for structure, not substance. Nothing here is an official BIS database and no compliance determination is made.
2. **Applicability rules are hand-encoded for the demo.** Real scope/exclusion/lifecycle rules for actual BIS standards require authorized sources plus domain-expert review.
3. **Extraction is regex/rules-based.** It is deterministic and laptop-friendly, but it will miss phrasing outside its patterns. The optional LLM layer only offers terminology hints and is a stub offline.
4. **Greedy set cover is approximate.** It yields a small sufficient set, not a provably optimal one — acceptable for decision support, stated openly.
5. **Sessions are in-memory.** Restarting the backend clears sessions. Multi-user persistence, auth, and audit logging are out of scope for the prototype.
6. **Human validation is mandatory.** IS-SCOPE is decision support. It does not grant regulatory approval, certify compliance, or replace a standards engineer.
7. **No legal advice.** Reports are labelled "AI-assisted recommendation — human validation required."
8. **Single-domain demo depth.** The hero story is industrial valves; other product families have only catalogue-level filler coverage.
