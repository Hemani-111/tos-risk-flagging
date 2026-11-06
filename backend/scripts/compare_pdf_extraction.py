#!/usr/bin/env python3
"""Compare a PDF extraction with TXT and optional DOCX baselines.
Run from backend/: python scripts/compare_pdf_extraction.py policy.pdf policy.txt [--docx policy.docx] [--model-labels].
"""
from __future__ import annotations
from collections import defaultdict
from difflib import SequenceMatcher
import argparse, json, re, sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.services.document_parser import DocxParser, PdfParser, TxtParser
from app.services.clause_segmenter import ClauseSegmenter


def normalize_for_comparison(text: str) -> str:
    """Diagnostic-only normalization; never use this string for source offsets."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[\t\f\v ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def diff_summary(a: str, b: str, limit: int = 8) -> dict:
    matcher = SequenceMatcher(a=a, b=b, autojunk=False)
    counts = {"insertions": 0, "deletions": 0, "substitutions": 0}
    whitespace = 0
    samples = []
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert": counts["insertions"] += b2 - b1
        elif tag == "delete": counts["deletions"] += a2 - a1
        elif tag == "replace": counts["substitutions"] += max(a2-a1, b2-b1)
        if (not a[a1:a2].strip()) or (not b[b1:b2].strip()):
            whitespace += max(a2-a1, b2-b1)
        if len(samples) < limit:
            samples.append({"kind": tag, "pdf_excerpt": a[max(0,a1-100):min(len(a),a2+100)],
                            "baseline_excerpt": b[max(0,b1-100):min(len(b),b2+100)],
                            "pdf_span": [a1,a2], "baseline_span": [b1,b2]})
    return {**counts, "whitespace_difference_characters": whitespace,
            "similarity_ratio": round(matcher.ratio(), 6), "excerpts": samples}


def clause_alignment(pdf_clauses, base_clauses, threshold: float = .92) -> dict:
    """Exact normalized matches first; fuzzy matches only when high-confidence and unique."""
    key = lambda c: re.sub(r"\s+", " ", c.text).strip().casefold()
    pg, bg = defaultdict(list), defaultdict(list)
    for i,c in enumerate(pdf_clauses): pg[key(c)].append(i)
    for i,c in enumerate(base_clauses): bg[key(c)].append(i)
    matches, used_p, used_b, duplicates = [], set(), set(), []
    for content, pis in pg.items():
        bis = bg.get(content, [])
        if not bis: continue
        for pi,bi in zip(pis,bis):
            matches.append({"pdf_index":pi,"baseline_index":bi,"method":"exact"})
            used_p.add(pi); used_b.add(bi)
        if len(pis)>1 or len(bis)>1:
            duplicates.append({"text":content[:160],"pdf_occurrences":len(pis),"baseline_occurrences":len(bis),
                               "resolution":"nth occurrence paired with nth occurrence; semantic identity uncertain"})
    pleft=[i for i in range(len(pdf_clauses)) if i not in used_p]
    bleft=[i for i in range(len(base_clauses)) if i not in used_b]
    proposals=[]
    for pi in pleft:
        scores=sorted(((SequenceMatcher(None,key(pdf_clauses[pi]),key(base_clauses[bi])).ratio(),bi) for bi in bleft),reverse=True)
        if scores and scores[0][0]>=threshold and (len(scores)==1 or scores[0][0]-scores[1][0]>=.03):
            proposals.append((scores[0][0],pi,scores[0][1]))
    best_for_base={}
    for score,pi,bi in proposals:
        if bi not in best_for_base or score>best_for_base[bi][0]: best_for_base[bi]=(score,pi)
    for score,pi,bi in sorted(proposals,reverse=True):
        if best_for_base.get(bi)==(score,pi) and pi not in used_p and bi not in used_b:
            matches.append({"pdf_index":pi,"baseline_index":bi,"method":"fuzzy","similarity":round(score,4)})
            used_p.add(pi); used_b.add(bi)
    matches.sort(key=lambda m:m["pdf_index"])
    unmatched_p=[i for i in range(len(pdf_clauses)) if i not in used_p]
    unmatched_b=[i for i in range(len(base_clauses)) if i not in used_b]
    # Detect likely segmentation splits/merges by exact concatenation of adjacent
    # unmatched clauses. These are suggestions, not asserted equivalences.
    compact=lambda value: re.sub(r"\s+", " ", value).strip().casefold()
    split_merge=[]
    for bi in unmatched_b:
        target=compact(base_clauses[bi].text)
        for width in (2,3,4):
            for pos in range(max(0,len(unmatched_p)-width+1)):
                group=unmatched_p[pos:pos+width]
                if group != list(range(group[0],group[0]+width)):
                    continue
                joined=compact(" ".join(pdf_clauses[i].text for i in group))
                if joined==target:
                    split_merge.append({"kind":"baseline_clause_may_be_split_in_pdf","pdf_indices":group,"baseline_index":bi})
    for pi in unmatched_p:
        target=compact(pdf_clauses[pi].text)
        for width in (2,3,4):
            for pos in range(max(0,len(unmatched_b)-width+1)):
                group=unmatched_b[pos:pos+width]
                if group != list(range(group[0],group[0]+width)):
                    continue
                joined=compact(" ".join(base_clauses[i].text for i in group))
                if joined==target:
                    split_merge.append({"kind":"pdf_clause_may_be_split_in_baseline","pdf_index":pi,"baseline_indices":group})
    return {"matches":matches,"unmatched_pdf":unmatched_p,
            "unmatched_baseline":unmatched_b,"duplicate_notes":duplicates,"possible_splits_or_merges":split_merge,
            "pdf_clause_count":len(pdf_clauses),"baseline_clause_count":len(base_clauses),
            "note":"Clause-count differences can be segmentation splits/merges, not proof of text loss."}


def compare_model_labels(pdf_clauses, base_clauses, alignment):
    from app.ml.model_loader import model_loader
    model, vectorizer = model_loader.load()
    pairs=alignment["matches"]
    ptxt=[pdf_clauses[x["pdf_index"]].text for x in pairs]
    btxt=[base_clauses[x["baseline_index"]].text for x in pairs]
    pl=model.predict(vectorizer.transform(ptxt)) if ptxt else []
    bl=model.predict(vectorizer.transform(btxt)) if btxt else []
    rows=[{**m,"pdf_label":str(a),"baseline_label":str(b),"same_label":str(a)==str(b)} for m,a,b in zip(pairs,pl,bl)]
    return {"comparisons":rows,"different_labels":sum(not x["same_label"] for x in rows),
            "note":"Labels are compared only for aligned content. Fuzzy alignments are less certain."}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf",type=Path); ap.add_argument("txt",type=Path)
    ap.add_argument("--docx",type=Path); ap.add_argument("--model-labels",action="store_true")
    ap.add_argument("--output-dir",type=Path,default=Path("pdf-comparison"))
    args=ap.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    pdf=PdfParser().parse_with_details(str(args.pdf)); ptxt=pdf.text; ttxt=TxtParser().parse(str(args.txt))
    def save(name,content): (args.output_dir/name).write_text(content,encoding="utf-8",newline="")
    save("pdf.raw.txt",ptxt); save("pdf.normalized.txt",normalize_for_comparison(ptxt))
    save("txt.raw.txt",ttxt); save("txt.normalized.txt",normalize_for_comparison(ttxt))
    seg=ClauseSegmenter(); pc=seg.segment(ptxt); tc=seg.segment(ttxt); align=clause_alignment(pc,tc)
    report={"files":{"pdf":str(args.pdf),"txt":str(args.txt),"docx":str(args.docx) if args.docx else None},
      "pdf_warnings":pdf.warnings,"pdf_page_ranges":[{"page":p,"start":s,"end":e} for p,s,e in pdf.page_ranges],
      "counts":{"pdf_characters":len(ptxt),"txt_characters":len(ttxt),"character_delta_pdf_minus_txt":len(ptxt)-len(ttxt),
        "pdf_words":word_count(ptxt),"txt_words":word_count(ttxt),"pdf_clauses":len(pc),"txt_clauses":len(tc)},
      "raw_diff":diff_summary(ptxt,ttxt),
      "normalized_diff":diff_summary(normalize_for_comparison(ptxt),normalize_for_comparison(ttxt)),"clause_alignment":align}
    if args.docx:
        dtxt=DocxParser().parse(str(args.docx)); save("docx.raw.txt",dtxt); save("docx.normalized.txt",normalize_for_comparison(dtxt))
        dc=seg.segment(dtxt); report["docx"]={"characters":len(dtxt),"words":word_count(dtxt),"clauses":len(dc),
          "raw_diff_vs_pdf":diff_summary(ptxt,dtxt),"normalized_diff_vs_pdf":diff_summary(normalize_for_comparison(ptxt),normalize_for_comparison(dtxt)),
          "clause_alignment_vs_pdf":clause_alignment(pc,dc)}
    if args.model_labels: report["model_labels"]=compare_model_labels(pc,tc,align)
    out=args.output_dir/"report.json"; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["counts"],indent=2)); print("\nPDF warnings:")
    for w in pdf.warnings: print("-",w)
    print(f"\nRaw similarity: {report['raw_diff']['similarity_ratio']}; normalized similarity: {report['normalized_diff']['similarity_ratio']}")
    print(f"Aligned clauses: {len(align['matches'])}; PDF-only: {len(align['unmatched_pdf'])}; baseline-only: {len(align['unmatched_baseline'])}")
    print("Report:",out.resolve())

if __name__=="__main__": main()
