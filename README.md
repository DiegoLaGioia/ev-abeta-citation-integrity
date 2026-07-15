# ev-abeta-citation-integrity

A citation integrity tool for the EV-Aβ axis: it checks claim-to-source correspondence at the **full-text** level (not just abstracts), producing verdicts that are auditable and traceable back to the exact source sentence.

This is not a mapping of the debate (Claude Science already does that at the abstract level). This tool's scope is:
1. verify whether a paper cites a source for a claim that the source, read in the text, actually supports;
2. identify positions that persist in the citing literature without support, propagated by citation inertia;
3. stay auditable and reproducible: every verdict traces back to the exact sentence in the source.

Full spec: [`blueprint_EV-Abeta_citation-integrity.md`](./blueprint_EV-Abeta_citation-integrity.md).

## MVP

One node verified end to end: homeostatic microglia (clearance) vs. MGnD/neurodegenerative microglia (propagation) on the EV-Aβ axis, across roughly 15-20 open-access anchor papers with JATS XML.

## Pipeline (6 stages)

```
[1] Corpus + full-text      → OA acquisition with JATS XML
[2] Claim↔citation extraction → deterministic parsing, xref → reference
[3] Cited source retrieval   → full-text/abstract of the cited paper
[4] Support verification    → Claude: verdict + rationale + evidence span
[5] Integrity aggregation   → contradictions + unsupported positions that persist
[6] Auditable output        → map of claim→cit→source→verdict→provenance
```

**Current status:** Stage 2 is working. On a corpus of 12 open-access papers (EV biogenesis → Aβ/tau axis), the pipeline extracts 1065 claim-citation pairs from full-text JATS, with 100% DOI/PMID resolution across heterogeneous publisher formats. First result: the field's dominant anchor (Asai 2015, a tau study) is cited by 11/11 citing papers, even for claims about Aβ, while the anchors for the opposing position (Yuyama, Dinkins) survive on 2 citations each, largely through self-citation. Stages 1 and 3-6 are still in development.

## Structure

```
src/
├── europepmc/   # stage 1: Europe PMC API client + local cache
└── extract/     # stage 2: JATS parsing, claim↔citation pairing
data/
├── anchors.csv     # anchor papers for the microglia node (PMCID/DOI), not versioned
└── outputs/        # generated reports (JSONL, CSV, HTML), not versioned
```

`data/` and `cache/` are in `.gitignore`: they hold raw/derived data (PDFs, XML, API cache), not code, and should not be committed.

## Setup

```bash
pip install -e .
```
