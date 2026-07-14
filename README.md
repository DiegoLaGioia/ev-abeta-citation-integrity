# ev-abeta-citation-integrity

Tool di citation-integrity sull'asse EV–Aβ: verifica claim↔fonte a livello di **full-text** (non solo abstract), con verdetti auditabili e tracciabili alla frase-fonte esatta.

Non è una mappatura del dibattito (quello lo fa già Claude Science a livello di abstract). Lo spazio proprio di questo tool è:
1. verificare se un paper cita una fonte per un'affermazione che la fonte, letta nel testo, sostiene davvero;
2. tracciare il *citation lag*: se una posizione superata continua a propagarsi per inerzia citazionale;
3. essere auditabile e riproducibile — ogni verdetto risale alla frase esatta della fonte.

Spec completa: [`blueprint_EV-Abeta_citation-integrity.md`](./blueprint_EV-Abeta_citation-integrity.md).

## MVP

Un nodo verificato end-to-end: **microglia omeostatica (clearance) vs. MGnD/neurodegenerativa (propagazione)** nell'asse EV–Aβ, su ~15–20 anchor paper open-access con JATS XML.

## Pipeline (6 stadi)

```
[1] Corpus + full-text      → acquisizione OA con JATS XML
[2] Estrazione claim↔cit.    → parsing deterministico xref → reference
[3] Retrieval fonte citata   → full-text/abstract del paper citato
[4] Verifica del supporto    → Claude: verdict + rationale + evidence span
[5] Aggregazione integrità   → contraddizioni + citation lag
[6] Output auditabile        → mappa claim→cit→fonte→verdict→provenance
```

**Stato attuale:** Stadio 2 funzionante. Su un corpus di 12 paper open-access (asse biogenesi EV → Aβ/tau), la pipeline estrae 1065 coppie claim-citazione dal full-text JATS, con risoluzione a DOI/PMID del 100% su formati di editori eterogenei. Primo risultato: l'anchor dominante del campo (Asai 2015, uno studio su *tau*) è citato da 11/11 paper citanti — anche per claim su *Aβ* — mentre gli anchor della posizione opposta (Yuyama, Dinkins) sopravvivono a 2 citazioni ciascuno, in gran parte per autocitazione. Stadi 1 e 3–6 in sviluppo.

## Struttura

```
src/
├── europepmc/   # stadio 1: client API Europe PMC + cache locale
└── extract/     # stadio 2: parsing JATS, pairing claim↔citazione
data/
├── anchors.csv     # anchor paper del nodo microgliale (PMCID/DOI) — non versionato
└── outputs/        # report generati (JSONL, CSV, HTML) — non versionato
```

`data/` e `cache/` sono in `.gitignore`: contengono dati grezzi/derivati (PDF, XML, cache API), non codice, e non vanno committati.

## Setup

```bash
pip install -e .
```
