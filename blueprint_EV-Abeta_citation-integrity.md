# Blueprint — Tool di citation-integrity sull'asse EV–Aβ

**Autore:** Diego La Gioia
**Deadline operativa:** 15 luglio (grant Claude Science AI for Science)
**Finestra di build:** 7–14 luglio
**Stato di partenza:** pilot Claude Science già eseguito (1.633 record Europe PMC, 135 classificati, 6 contraddizioni mappate a livello abstract)

---

## 0. La tesi — perché questo tool non è ridondante rispetto a Claude Science

Questo è il paletto che decide se il progetto vale. Va tenuto fisso in ogni scelta successiva.

Il pilot di ieri ha dimostrato che Claude Science, in una sera, mappa il *dibattito* a livello di abstract: classifica posizioni, conta, aggrega. Se il tuo tool si ferma lì, sei ridondante e il grant non ha motivo di finanziarti.

Lo spazio difendibile è la parte che il pilot **non** ha fatto e che il workbench generalista non fa:

1. **Verifica claim↔fonte sul full-text.** Non "questi due abstract sembrano in disaccordo", ma "questo paper cita quella fonte per un'affermazione che la fonte, letta nel testo, non sostiene". Questa è citation integrity vera; il resto è mappatura di dibattito.
2. **Tracciamento del citation lag.** Non contare le posizioni, ma misurare se una posizione contestata/superata continua a propagarsi per inerzia. Il tuo segnale forte dal pilot — la clearance protettiva scesa a 5/135 — non va letto come "contraddizione risolta" ma come *posizione che svanisce per spostamento sociologico del campo*, da interrogare.
3. **Auditabilità e riproducibilità.** Ogni verdetto tracciabile alla frase-fonte esatta, rieseguibile da terzi. Il pilot è one-shot e non riproducibile.

> **Formulazione per il grant:** non compete con Claude Science, ci si costruisce sopra come *skill verticale* di dominio — verifica claim↔fonte full-text con output auditabile, su un campo dove la correttezza citazionale ha conseguenze cliniche. È esattamente ciò che l'hackathon Builder e il grant AI for Science cercano: estendere l'ecosistema, non rifare il core.

---

## 1. Architettura della pipeline

Sei stadi. I primi due sono il cuore differenziante; non saltarli per tornare alla classificazione abstract del pilot.

```
[1] Corpus + full-text      → acquisizione OA con JATS XML
[2] Estrazione claim↔cit.    → parsing deterministico xref → reference
[3] Retrieval fonte citata   → full-text/abstract del paper citato
[4] Verifica del supporto    → Claude: verdict + rationale + evidence span
[5] Aggregazione integrità   → contraddizioni + citation lag
[6] Output auditabile        → mappa claim→cit→fonte→verdict→provenance
```

### Stadio 1 — Corpus e full-text
- Fonte: **Europe PMC REST API** (già la usi).
  - Search: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`
  - Full-text OA: `.../rest/{source}/{id}/fullTextXML` (es. sorgente `PMC`)
- **Scelta architetturale decisiva:** limita il corpus della verifica agli articoli **open-access con JATS XML disponibile**. Sacrifichi copertura, guadagni rigore e ti togli dai piedi il parsing dei PDF, che è il punto dove i progetti come questo affogano.

### Stadio 2 — Estrazione claim↔citazione (il pezzo che vale)
- Il JATS XML degli articoli OA ha i marker di citazione in-text come `<xref ref-type="bibr" rid="...">` collegati alle voci `<ref>` della reference list. **Questo rende il pairing claim↔citazione deterministico, non affidato a un LLM fragile.** È la differenza tra "il modello ha estratto le citazioni" e "le citazioni sono estratte per costruzione dalla struttura del documento".
- Per ogni citazione: isola la **frase-claim** che la contiene (la sentence in cui compare l'`<xref>`), risolvi la `<ref>` a DOI/PMID.
- *Solo dove manca lo XML* e serve un paper specifico: GROBID come fallback per estrarre riferimenti strutturati dal PDF. Ma per l'MVP tienilo fuori — è complessità che non ti serve questa settimana.

### Stadio 3 — Retrieval della fonte citata
- Per ogni DOI/PMID citato, recupera abstract e, se OA, full-text via Europe PMC.
- Onestà del metodo: se la fonte citata **non** è OA, hai solo l'abstract → il verdetto va marcato come "verifica limitata all'abstract", non spacciato per full-text. La trasparenza sul livello di verifica è essa stessa un feature di integrità.

### Stadio 4 — Verifica del supporto (Claude)
- Input al modello: la frase-claim del paper citante + il passo rilevante della fonte citata.
- Output strutturato (JSON), per ogni coppia:
  - `verdict`: `supports` | `partial` | `fails` | `unverifiable`
  - `rationale`: motivazione in linguaggio naturale
  - `evidence_span`: la stringa esatta della fonte su cui poggia il verdetto
  - `verification_level`: `full_text` | `abstract_only`
- Questo è dove il pilot si è fermato all'abstract e tu vai al full-text. Il `rationale` + `evidence_span` sono ciò che rende il verdetto *auditabile* invece che un'etichetta opaca.

### Stadio 5 — Aggregazione: contraddizioni + citation lag
- **Contraddizioni:** stessa fonte citata da paper diversi per conclusioni opposte → flag. (Il pilot lo faceva sugli abstract; ora poggia su verdetti full-text.)
- **Citation lag:** per le fonti che il campo ha "abbandonato" (es. la clearance protettiva a 5/135), traccia se vengono ancora citate correttamente, citate male, o ignorate. È qui che il tool diventa più di un aggregatore: misura la *dinamica* della correttezza citazionale nel tempo, non solo la distribuzione istantanea.

### Stadio 6 — Output auditabile
- Un report navigabile: `claim → citazione → fonte → verdict → evidence_span → provenance (DOI, verification_level)`.
- Riusa il pattern HTML+CSV che hai già prodotto nel pilot. Aggiungi il campo `evidence_span` e `verification_level`, che sono la novità.

---

## 2. Stack tecnico (deciso, con rationale)

| Componente | Scelta | Perché |
|---|---|---|
| Linguaggio | Python | Già nel tuo flusso; tutto qui è API + parsing, niente GPU |
| Corpus/full-text | Europe PMC REST | Già validato nel pilot; ha il full-text JATS OA |
| Parsing citazioni | `lxml` su JATS XML | Deterministico via `<xref>`/`<ref>`; niente ML fragile |
| Verifica | Claude API (structured output) | Il ragionamento claim↔fonte è il core |
| Fallback PDF | GROBID | *Solo se serve*, fuori dall'MVP |
| Output | HTML + CSV + JSON | Riuso del pattern pilot; JSON per riproducibilità |
| Build environment | Claude Code su WSL2 | Il blueprint È la spec che gli dai |

**Nota hardware:** nulla qui richiede la tua RTX 3050. Il carico pesante sono chiamate API a Claude, non modelli locali. Il tuo X13 su WSL2 basta e avanza. Questo elimina la scusa "non ho la macchina giusta".

---

## 3. MVP della settimana — lo scope stretto

Non ricreare il pilot su 135 paper. L'MVP è **un nodo, verificato full-text, end-to-end**:

> **Asse microgliale EV–Aβ: microglia omeostatica (clearance) vs. MGnD/neurodegenerativa (propagazione).**
> ~15–20 anchor paper OA con JATS XML, verifica claim↔citazione full-text, output auditabile con almeno una contraddizione tracciata alla frase-fonte + una traccia di citation lag sulla clearance protettiva.

Criterio di selezione degli anchor: **massimizza densità di conflitto verificabile su un nodo che padroneggi**, non copertura. Parti dalle 1-2 review recenti che esplicitano la controversia clearance-vs-spreading e segui le loro citazioni ai due poli.

**Test di "abbastanza piccolo":** se non gira end-to-end su questo nodo in 3 giorni densi, taglia ancora (es. solo EV microgliali → neurone, non tutto il nodo).

---

## 4. Piano di esecuzione — front-loaded verso il 15

La cornice esterna dell'hackathon non c'è più. La ricrei tu: la deadline vera è il **15**, e lo stake sociale lo agganci a Origlia (vedi §6). Il calendario resta front-loaded — il grosso nei primi giorni, così la settimana d'esame che segue non ti trova con un progetto aperto.

**7–8 lug — Fondamenta (sprint duro)**
- Repo pubblico, README con tesi + architettura (§0–1). `.gitignore` sensato, niente PDF di paper nel repo.
- Stadi 1–2: acquisizione OA + estrazione deterministica claim↔citazione sul nodo microgliale. Questo è il pezzo tecnico critico; se funziona, il resto è in discesa.

**9–10 lug — Il cuore**
- Stadi 3–4: retrieval fonti + verifica Claude con output strutturato (`verdict`/`rationale`/`evidence_span`/`verification_level`).
- Prima passata sui 15–20 anchor. Guarda gli output, correggi i falsi positivi peggiori a mano — è qui che il tuo giudizio di dominio è insostituibile.

**11–12 lug — Aggregazione + rigore**
- Stadio 5: contraddizioni su base full-text + traccia citation lag sulla clearance protettiva.
- Stadio 6: report auditabile. Verifica full-text di almeno 2-3 anchor "parola per parola" per validare che il tool non stia allucinando supporti/contraddizioni.

**13 lug — Packaging + release**
- Release Zenodo del repo → **DOI citabile** (asset pubblico reale, vale a prescindere dal grant).
- README finale con output d'esempio.
- **Consegna entro sera ora italiana**, non nella notte.

**14–15 lug — Application del grant**
- Scrivi la proposal *attorno al demo funzionante*: tier-1 = questo tool (proof-of-concept già costruito, ecco il DOI), tier-2 = visione (vedi §5).
- Submit entro il 15, verificando l'orario esatto di cutoff.

---

## 5. Aggancio al grant — tier-1 / tier-2

**Tier-1 (il deliverable di questa settimana):** il tool di citation-integrity full-text sul nodo microgliale EV–Aβ. Non "vi propongo di costruire X" ma "ho costruito il proof-of-concept di X, ecco il DOI, con i crediti lo scalo".

**Tier-2 (la visione, computazionale — NON tocca questa settimana):** dalle contraddizioni e future directions che il tier-1 fa emergere, validazione *in silico* delle ipotesi proteiche/di interazione. Ancoralo al livello **structure/interaction prediction** (AlphaFold3/Boltz-2 sui candidati che il tool identifica come sotto-esplorati) — credibile e finanziabile con compute credits. La molecular dynamics vera resta orizzonte a cui il tool apre, non cosa che esegui tu. La proteomica di rete (angolo Krogan/Verderio) vive qui come direzione, non come secondo progetto.

Coerenza dell'arco: **sintesi rigorosa → generazione ipotesi → validazione computazionale.** Il tier-1 fonda retoricamente il tier-2.

---

## 6. Rischi e note watchdog

- **Il rischio non è tecnico, è motivazionale.** Senza la cornice dell'hackathon, il progetto può scivolare nel "lo faccio con calma" = mai, con l'esame addosso. **Contromisura obbligatoria:** aggancia uno stake esterno oggi. Messaggio a Origlia: "sto costruendo un tool di citation-integrity sull'asse EV-microglia-Aβ, posso mostrartelo la settimana prossima?". Uno che si aspetta di vedere qualcosa vale più di 500 sconosciuti su Discord.
- **Non fidarti del tuo stesso output automatico.** I verdetti Claude sono ipotesi di (non-)supporto, non fatti. La verifica full-text a mano di alcuni anchor non è opzionale — è la cosa che distingue il tuo tool da ciò che critica. Se salti quella, fai l'errore epistemico che il tool esiste per combattere.
- **Non pivotare per il no dell'hackathon.** L'esclusione da una lotteria su decine di migliaia non è informazione sul progetto. "Ho sbagliato progetto" è un'inferenza da rumore che ti porterebbe ad aprire un fronte nuovo. Il progetto era buono ieri quando Claude Science l'ha validato, è buono oggi.
- **Scope creep.** La tentazione sarà "già che ci sono, estendo a tutto l'asse EV-Aβ / aggiungo origine e funzione". No. Un nodo che gira end-to-end batte un asse coperto al 70%. Completo è nemico di consegnato.
- **Compute.** Non hai il Max 20x. Non è il collo di bottiglia verso il 15: il fattore limitante è il tuo tempo e il tuo rigore, non i token. Hai l'accesso a Claude Science e a Claude Code — basta per l'MVP.

---

## 7. Prima azione concreta (oggi)

Non rinfrescare caselle né rimuginare sul no. Due cose:
1. Apri il corpus del pilot e **seleziona i 15–20 anchor** del nodo microgliale (clearance vs propagazione).
2. Manda **il messaggio a Origlia** — lo stake che sostituisce la cornice dell'hackathon.

Il resto è esecuzione, e l'esecuzione parte da qui.
