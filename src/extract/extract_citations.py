"""
Stage 2 — deterministic claim<->citation extraction from JATS XML.

For every in-text citation (<xref ref-type="bibr">) in each open-access article,
this resolves the cited reference (<ref>) to a DOI/PMID/PMCID and pairs it with
the sentence in which the citation appears. Output: one JSONL row per citation
instance.

Handles the real-world variation observed across publishers in the corpus:
- no XML namespace (root <article> directly)
- DOI/PMID encoded either as <pub-id pub-id-type="doi"> (BMC/Nature) OR as
  <ext-link ext-link-type="doi"> (ACS/Frontiers/JCI/Cell)
- in-text markers nested inside <sup>
"""

import glob
import json
import os
import re
import sys
from lxml import etree

XLINK = "http://www.w3.org/1999/xlink"


def text_of(el):
    """Full visible text of an element, whitespace-normalized."""
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def resolve_ref_ids(ref):
    """Extract doi / pmid / pmcid from a <ref>, covering both encodings."""
    ids = {"doi": None, "pmid": None, "pmcid": None}

    # Encoding A: <pub-id pub-id-type="...">
    for pid in ref.findall(".//pub-id"):
        t = pid.get("pub-id-type")
        if t in ids and ids[t] is None and pid.text:
            ids[t] = pid.text.strip()

    # Encoding B: <ext-link ext-link-type="..." xlink:href="...">
    for ext in ref.findall(".//ext-link"):
        t = ext.get("ext-link-type")
        href = ext.get("{%s}href" % XLINK)
        if t in ids and ids[t] is None and href:
            ids[t] = href.strip()

    return ids


def ref_citation_string(ref):
    """A human-readable citation string for the reference, for eyeballing."""
    nc = ref.find(".//named-content[@content-type='citation-string']")
    if nc is not None and text_of(nc):
        return text_of(nc)
    return text_of(ref)[:300]


def ancestor_sentence(xref, para_text):
    """
    Return the sentence within the ancestor paragraph that contains this xref.
    Splits the paragraph on sentence boundaries and picks the fragment holding
    the citation marker. Falls back to the whole paragraph if splitting fails.
    """
    marker = text_of(xref)
    # crude but effective sentence split
    sentences = re.split(r"(?<=[.!?])\s+", para_text)
    for s in sentences:
        if marker and marker in s:
            return s.strip()
    # fallback: return whole paragraph trimmed
    return para_text.strip()


def ancestor_paragraph_text(xref):
    p = xref
    while p is not None and p.tag != "p":
        p = p.getparent()
    if p is None:
        return ""
    return text_of(p)


def process_file(path):
    pmcid = os.path.splitext(os.path.basename(path))[0]
    tree = etree.parse(path)

    # build ref lookup: rid -> resolved ids + citation string
    ref_lookup = {}
    for ref in tree.findall(".//ref"):
        rid = ref.get("id")
        if not rid:
            continue
        ref_lookup[rid] = {
            "ids": resolve_ref_ids(ref),
            "citation_string": ref_citation_string(ref),
        }

    rows = []
    for xref in tree.findall('.//xref[@ref-type="bibr"]'):
        rid = xref.get("rid")
        if not rid:
            continue
        # a single xref may point to multiple refs (space-separated rids)
        for one_rid in rid.split():
            ref = ref_lookup.get(one_rid)
            para = ancestor_paragraph_text(xref)
            claim = ancestor_sentence(xref, para) if para else ""
            rows.append({
                "citing_pmcid": pmcid,
                "claim_sentence": claim,
                "cited_rid": one_rid,
                "cited_doi": ref["ids"]["doi"] if ref else None,
                "cited_pmid": ref["ids"]["pmid"] if ref else None,
                "cited_pmcid": ref["ids"]["pmcid"] if ref else None,
                "cited_citation_string": ref["citation_string"] if ref else None,
            })
    return rows


def main():
    xml_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out_path = sys.argv[2] if len(sys.argv) > 2 else "claim_citation_pairs.jsonl"

    files = sorted(glob.glob(os.path.join(xml_dir, "*.xml")))
    all_rows = []
    per_file = {}
    for f in files:
        rows = process_file(f)
        per_file[os.path.basename(f)] = len(rows)
        all_rows.extend(rows)

    with open(out_path, "w") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # summary
    resolved = sum(1 for r in all_rows if r["cited_doi"] or r["cited_pmid"])
    print(f"Files processed : {len(files)}")
    print(f"Citation pairs  : {len(all_rows)}")
    print(f"  with DOI/PMID  : {resolved} ({100*resolved/len(all_rows):.0f}%)")
    print(f"Output           : {out_path}")
    print("Per-file citation counts:")
    for k, v in per_file.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
