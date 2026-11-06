#!/usr/bin/env python3
"""Real-document evaluation for TermsGuard/ToS-risk-flagging (v2).

Runs official policy snapshots through the existing API, saves reproducible
artifacts, performs extraction/segmentation checks, and prepares blind human
review materials. Does NOT tune model, thresholds, segmentation, or artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
SNAP_DIR = EVAL_DIR / "snapshots"
CLEAN_DIR = EVAL_DIR / "cleaned"
API_DIR = EVAL_DIR / "api_outputs"
SHEET_DIR = EVAL_DIR / "review_sheets"
FIG_DIR = EVAL_DIR / "figures"
AGG_DIR = EVAL_DIR / "aggregate"
MANIFEST_PATH = ROOT / "data" / "review" / "real_document_sources_v2.csv"
FREEZE_PATH = EVAL_DIR / "candidate_freeze.json"
API_BASE = os.environ.get("TERMSGUARD_API_BASE", "http://127.0.0.1:8000/api/v1")
REPEAT_TIMING_N = 3

# 12 documents: 6 services × (ToS/User Agreement + Privacy Policy). Official sources.
# Overlap is recorded from evidence in data/raw/services.csv (ToSDR-derived registry).
DOCUMENTS = [
    # Discord - messaging
    {"document_id":"discord_tos","service_name":"Discord","category":"messaging","document_type":"Terms of Service",
     "source_url":"https://discord.com/terms","jurisdiction":"global/US (consumer terms page)","language":"en",
     "overlap_evidence":"discord present in data/raw/services.csv and points.csv; service_component anonymized in split manifest",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"discord_privacy","service_name":"Discord","category":"messaging","document_type":"Privacy Policy",
     "source_url":"https://discord.com/privacy","jurisdiction":"global/US","language":"en",
     "overlap_evidence":"discord present in data/raw/services.csv and points.csv; service_component anonymized in split manifest",
     "overlap_status":"known-registry/potential-overlap"},
    # Spotify - streaming (India EULA as specified)
    {"document_id":"spotify_tos_in","service_name":"Spotify","category":"streaming","document_type":"Terms of Service / End User Agreement",
     "source_url":"https://www.spotify.com/in-en/legal/end-user-agreement/","jurisdiction":"India (IN)","language":"en",
     "overlap_evidence":"spotify present in data/raw/services.csv and points.csv; India-specific EULA version recorded",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"spotify_privacy","service_name":"Spotify","category":"streaming","document_type":"Privacy Policy",
     "source_url":"https://www.spotify.com/in-en/legal/privacy-policy/","jurisdiction":"global/region-specific presentation","language":"en",
     "overlap_evidence":"spotify present in data/raw/services.csv and points.csv",
     "overlap_status":"known-registry/potential-overlap"},
    # Reddit - social media
    {"document_id":"reddit_user_agreement","service_name":"Reddit","category":"social media","document_type":"User Agreement",
     "source_url":"https://www.redditinc.com/policies/user-agreement","jurisdiction":"global/US","language":"en",
     "overlap_evidence":"reddit/redditmetis entries present in data/raw/services.csv and points.csv",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"reddit_privacy","service_name":"Reddit","category":"social media","document_type":"Privacy Policy",
     "source_url":"https://www.reddit.com/policies/privacy-policy","jurisdiction":"global/US","language":"en",
     "overlap_evidence":"reddit entries present in data/raw/services.csv and points.csv",
     "overlap_status":"known-registry/potential-overlap"},
    # GitHub - developer tools
    {"document_id":"github_tos","service_name":"GitHub","category":"developer tools","document_type":"Terms of Service",
     "source_url":"https://docs.github.com/en/site-policy/github-terms/github-terms-of-service","jurisdiction":"global/US","language":"en",
     "overlap_evidence":"github present in data/raw/services.csv; service_component anonymized in split manifest",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"github_privacy","service_name":"GitHub","category":"developer tools","document_type":"Privacy Statement",
     "source_url":"https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement","jurisdiction":"global","language":"en",
     "overlap_evidence":"github present in data/raw/services.csv",
     "overlap_status":"known-registry/potential-overlap"},
    # Notion - productivity
    {"document_id":"notion_tos","service_name":"Notion","category":"productivity","document_type":"Terms of Use / Master Subscription Agreement (consumer-facing terms page)",
     "source_url":"https://www.notion.so/terms","jurisdiction":"global/US","language":"en",
     "overlap_evidence":"notion present in data/raw/services.csv",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"notion_privacy","service_name":"Notion","category":"productivity","document_type":"Privacy Policy",
     "source_url":"https://www.notion.so/privacy","jurisdiction":"global","language":"en",
     "overlap_evidence":"notion present in data/raw/services.csv",
     "overlap_status":"known-registry/potential-overlap"},
    # Etsy - shopping/marketplace
    {"document_id":"etsy_tos","service_name":"Etsy","category":"shopping/marketplace","document_type":"Terms of Use",
     "source_url":"https://www.etsy.com/legal/terms-of-use","jurisdiction":"global/region-specific","language":"en",
     "overlap_evidence":"etsy present in data/raw/services.csv",
     "overlap_status":"known-registry/potential-overlap"},
    {"document_id":"etsy_privacy","service_name":"Etsy","category":"shopping/marketplace","document_type":"Privacy Policy",
     "source_url":"https://www.etsy.com/legal/privacy/","jurisdiction":"global/region-specific","language":"en",
     "overlap_evidence":"etsy present in data/raw/services.csv",
     "overlap_status":"known-registry/potential-overlap"},
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class VisibleText(HTMLParser):
    SKIP = {"script","style","noscript","svg","nav","header","footer","aside","form","button","input"}
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.depth += 1
        elif not self.depth and tag in {"p","li","h1","h2","h3","h4","h5","h6","br","tr","td","th","section","article","blockquote","pre","div"}:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth: self.depth -= 1
        elif not self.depth and tag in {"p","li","h1","h2","h3","h4","h5","h6","tr","section","article","blockquote","div"}:
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.depth:
            t = re.sub(r"\s+", " ", data)
            if t.strip(): self.parts.append(t)


def clean_html_to_text(raw: bytes) -> str:
    html = raw.decode("utf-8", errors="replace")
    p = VisibleText(); p.feed(html)
    text = "\n".join(p.parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # light removal of obvious cookie/banner remnants
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s: lines.append(""); continue
        low = s.lower()
        if len(s) < 220 and ("cookie" in low and ("accept" in low or "preferences" in low or "consent" in low)):
            continue
        lines.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def fetch_url(url: str) -> dict[str, Any]:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urlopen(req, timeout=90) as resp:
            raw = resp.read()
            return {"ok": True, "status": getattr(resp, "status", 200), "final_url": resp.geturl(),
                    "content_type": resp.headers.get_content_type(), "raw": raw}
    except HTTPError as e:
        return {"ok": False, "status": e.code, "error": f"HTTPError:{e.code}", "detail": str(e)}
    except (URLError, TimeoutError, Exception) as e:
        return {"ok": False, "status": None, "error": type(e).__name__, "detail": str(e)}


def ensure_dirs():
    for d in [SNAP_DIR,CLEAN_DIR,API_DIR,SHEET_DIR,FIG_DIR,AGG_DIR]: d.mkdir(parents=True, exist_ok=True)


def load_manifest_rows() -> list[dict[str,str]]:
    if not MANIFEST_PATH.exists(): return []
    with MANIFEST_PATH.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))


def write_manifest(rows: list[dict[str,Any]]):
    fields = ["document_id","service_name","category","document_type","source_url","requested_url","final_url",
              "jurisdiction","language","retrieved_at_utc","published_or_effective_date","retrieval_method",
              "snapshot_path","snapshot_sha256","content_type","cleaned_text_path","cleaned_text_sha256",
              "cleaned_text_chars","overlap_status","overlap_evidence","collection_status","failure_reason","notes"]
    tmp = MANIFEST_PATH.with_suffix('.csv.tmp')
    with tmp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    tmp.replace(MANIFEST_PATH)


def cmd_collect(args):
    ensure_dirs()
    rows_by_id = {r['document_id']: r for r in load_manifest_rows()}
    out_rows=[]
    for doc in DOCUMENTS:
        did=doc['document_id']
        existing=rows_by_id.get(did)
        if existing and existing.get('collection_status','').startswith('snapshot_frozen') and (ROOT/existing.get('snapshot_path','_')).exists():
            print(f"{did}: existing frozen snapshot preserved")
            out_rows.append(existing); continue
        res = fetch_url(doc['source_url'])
        now = datetime.now(timezone.utc).isoformat()
        row = {**doc, "requested_url":doc['source_url'], "final_url": res.get('final_url'),
               "retrieved_at_utc": now, "published_or_effective_date":"", "retrieval_method":"urllib GET (no bypass)",
               "snapshot_path":"","snapshot_sha256":"","content_type":res.get('content_type',''),
               "cleaned_text_path":"","cleaned_text_sha256":"","cleaned_text_chars":"",
               "collection_status":"","failure_reason":"","notes":""}
        if not res.get('ok'):
            row['collection_status']=f"fetch_failed:{res.get('status') or res.get('error')}"
            row['failure_reason']=res.get('detail','')[:500]
            print(f"{did}: FAILED {row['collection_status']} - {row['failure_reason'][:120]}")
            out_rows.append(row); continue
        raw=res['raw']
        ctype=(res.get('content_type') or '').lower()
        ext='pdf' if 'pdf' in ctype or raw[:4]==b'%PDF' else 'html'
        snap_path=SNAP_DIR/f"{did}.{ext}"; snap_path.write_bytes(raw)
        row['snapshot_path']=str(snap_path.relative_to(ROOT)).replace('\\','/')
        row['snapshot_sha256']=sha256_bytes(raw)
        row['content_type']=ctype or ext
        if ext=='pdf':
            # extract via existing app parser for fidelity
            try:
                sys.path.insert(0,str(ROOT/'backend'))
                from app.services.document_parser import PdfParser
                text=PdfParser().parse(str(snap_path))
                extraction='app.PdfParser(pypdf)'
            except Exception as e:
                text=f"[PDF extraction failed: {e}]"; extraction=f"error:{e}"
            row['notes']=f'pdf_extraction={extraction}'
        else:
            text=clean_html_to_text(raw)
            row['notes']='html_extraction=stdlib.VisibleText+heuristic cleanup; snapshot text separate from API-extracted text'
        if len(text.strip()) < 400:
            row['collection_status']='snapshot_frozen_extraction_thin'
            row['failure_reason']=f'extracted text short ({len(text.strip())} chars); may be blocked/JS-rendered; manual save may be needed'
            print(f"{did}: THIN extraction {len(text.strip())} chars")
        else:
            row['collection_status']='snapshot_frozen_review_pending'
            print(f"{did}: ok {len(raw)} bytes, {len(text)} chars, {ext}")
        clean_path=CLEAN_DIR/f"{did}.txt"; clean_path.write_text(text,encoding='utf-8')
        row['cleaned_text_path']=str(clean_path.relative_to(ROOT)).replace('\\','/')
        row['cleaned_text_sha256']=sha256_text(text)
        row['cleaned_text_chars']=str(len(text))
        out_rows.append(row)
    write_manifest(out_rows)
    print(f"Wrote manifest: {MANIFEST_PATH} ({len(out_rows)} rows)")


def curl_json(method, url, payload=None, form_file=None, timeout=180):
    cmd=['curl','-sS','--max-time',str(timeout),'-X',method,url]
    tmp_payload=None
    try:
        if form_file:
            cmd+=['-F',f'file=@{form_file}']
        if payload is not None:
            import tempfile
            fd,tmp_payload=tempfile.mkstemp(prefix='tg-eval-',suffix='.json')
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(payload,f,ensure_ascii=False)
            cmd+=['-H','Content-Type: application/json','--data-binary',f'@{tmp_payload}']
        t0=time.perf_counter()
        p=subprocess.run(cmd,capture_output=True,text=True)
        dt=time.perf_counter()-t0
        body=p.stdout
        try: data=json.loads(body) if body else None
        except Exception: data={"_raw":(body or '')[:2000],"_parse_error":True}
        return {"http_ok":p.returncode==0,"curl_rc":p.returncode,"duration_s":dt,"data":data,"stderr":(p.stderr or '')[:500]}
    finally:
        if tmp_payload and os.path.exists(tmp_payload):
            try: os.unlink(tmp_payload)
            except OSError: pass


def cmd_analyze(args):
    ensure_dirs()
    rows=load_manifest_rows()
    if not rows: print("No manifest; run collect first",file=sys.stderr); sys.exit(2)
    model_info = curl_json('GET', f'{API_BASE}/../v1/health') if False else curl_json('GET','http://127.0.0.1:8000/api/v1/health')
    summary=[]
    for row in rows:
        did=row['document_id']
        if not row.get('collection_status','').startswith('snapshot_frozen'):
            summary.append({"document_id":did,"api_status":"skipped","reason":row.get('collection_status')}); continue
        clean_path=ROOT/row['cleaned_text_path']
        if not clean_path.exists():
            summary.append({"document_id":did,"api_status":"skipped","reason":"missing cleaned text"}); continue
        text=clean_path.read_text(encoding='utf-8')
        payload={"text":text, "filename":f"{did}.txt"}
        # first request (cold-ish) + repeat timings
        first=curl_json('POST',f'{API_BASE}/documents/analyze-text',payload=payload,timeout=180)
        repeats=[]
        for _ in range(max(0,REPEAT_TIMING_N-1)):
            r=curl_json('POST',f'{API_BASE}/documents/analyze-text',payload=payload,timeout=180)
            repeats.append({"duration_s":r['duration_s'],"http_ok":r['http_ok'],"curl_rc":r['curl_rc']})
        out={"document_id":did,"service_name":row['service_name'],"document_type":row['document_type'],
             "region":row.get('jurisdiction'),"input":{"cleaned_text_path":row['cleaned_text_path'],
             "cleaned_text_sha256":row['cleaned_text_sha256'],"chars":len(text)},
             "timing":{"first_request_s":first['duration_s'],"repeat_requests":repeats,
                       "definition":"curl wall-clock including HTTP/JSON transfer; repeat requests after first; not a production capacity benchmark"},
             "api_first":first['data']}
        (API_DIR/f"{did}.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        # compact summary
        d=first['data'] if isinstance(first['data'],dict) else {}
        summary.append({"document_id":did,"service":row['service_name'],"type":row['document_type'],
                        "region":row.get('jurisdiction'),"overlap":row.get('overlap_status'),
                        "api_status":"ok" if d.get('totalClauses') else ("error:"+str(d.get('detail') or d.get('_parse_error') or first['stderr'])[:120]),
                        "totalClauses":d.get('totalClauses'),"risky":d.get('riskyCount'),
                        "neutral":d.get('neutralCount'),"safe":d.get('safeCount'),
                        "riskyPct":d.get('riskyPercentage'),"neutralPct":d.get('neutralPercentage'),"safePct":d.get('safePercentage'),
                        "modelVersion":d.get('modelVersion'),"warnings":d.get('warnings'),
                        "first_s":round(first['duration_s'],3)})
        print(f"{did}: status={summary[-1]['api_status']} clauses={d.get('totalClauses')} risky={d.get('riskyCount')} first={first['duration_s']:.2f}s")
    (AGG_DIR/'run_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    # CSV
    if summary:
        keys=sorted({k for r in summary for k in r.keys()})
        with (AGG_DIR/'run_summary.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(summary)
    print(f"Wrote {AGG_DIR/'run_summary.json'}")


def inspect_extraction():
    issues=[]
    for p in sorted(API_DIR.glob('*.json')):
        obj=json.loads(p.read_text(encoding='utf-8'))
        did=obj['document_id']; d=obj.get('api_first') or {}
        clauses=d.get('clauses') or []; et=d.get('extractedText') or ''
        doc_issues=[]
        if not clauses and d.get('detail'): doc_issues.append(f"API error: {d.get('detail')}")
        total=len(clauses)
        counts={"Risky":d.get('riskyCount'),"Neutral":d.get('neutralCount'),"Safe":d.get('safeCount')}
        actual={"Risky":sum(1 for c in clauses if c.get('label')=='Risky'),
                "Neutral":sum(1 for c in clauses if c.get('label')=='Neutral'),
                "Safe":sum(1 for c in clauses if c.get('label')=='Safe')}
        if total!=d.get('totalClauses'): doc_issues.append(f"total mismatch {total}!={d.get('totalClauses')}")
        if counts!=actual: doc_issues.append(f"count mismatch reported={counts} actual={actual}")
        bad_labels=[c.get('label') for c in clauses if c.get('label') not in ('Risky','Neutral','Safe')]
        if bad_labels: doc_issues.append(f"invalid labels: {set(bad_labels)}")
        offset_err=span_mismatch=0
        covered=set()
        for c in clauses:
            s,e=c.get('startOffset',-1),c.get('endOffset',-1)
            if s<0 or e>s is False or e>len(et): offset_err+=1; continue
            span=et[s:e]
            if span!=c.get('text',''): span_mismatch+=1
            for i in range(s,min(e,s+500000)): covered.add(i)
        if offset_err: doc_issues.append(f"offset errors: {offset_err}/{total}")
        if span_mismatch: doc_issues.append(f"span/text mismatches: {span_mismatch}/{total}")
        coverage=(len(covered)/len(et)*100) if et else 0
        short=sum(1 for c in clauses if len((c.get('text') or '').strip())<20)
        headings=sum(1 for c in clauses if re.match(r'^(\d+\.|#+|[A-Z][A-Z \-]{4,}$)',(c.get('text') or '').strip()) and len((c.get('text') or '').split())<=8)
        risky_cl=[c for c in clauses if c.get('label')=='Risky']
        missing_context=sum(1 for c in risky_cl if len(c.get('text',''))<40)
        issues.append({"document_id":did,"total_clauses":total,"char_coverage_pct":round(coverage,2),
                       "extracted_chars":len(et),"offset_errors":offset_err,"span_mismatches":span_mismatch,
                       "short_clauses_lt20":short,"heading_like_clauses":headings,
                       "risky_clauses_very_short_lt40":missing_context,"issues":doc_issues,
                       "note":"High character coverage does not prove accurate extraction or useful segmentation."})
    (AGG_DIR/'extraction_segmentation_inspection.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
    with (AGG_DIR/'extraction_segmentation_inspection.csv').open('w',newline='',encoding='utf-8') as f:
        if issues:
            keys=["document_id","total_clauses","extracted_chars","char_coverage_pct","offset_errors","span_mismatches","short_clauses_lt20","heading_like_clauses","risky_clauses_very_short_lt40","issues","note"]
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
            for r in issues: w.writerow({**r,"issues":" | ".join(r['issues'])})
    print(f"Wrote extraction inspection for {len(issues)} docs")
    return issues


SAMPLE_TARGET_MIN=150
SAMPLE_TARGET_MAX=250
SAMPLE_SEED=20261106

def build_review_sheets():
    ensure_dirs()
    all_clauses=[]
    for p in sorted(API_DIR.glob('*.json')):
        obj=json.loads(p.read_text(encoding='utf-8'))
        did=obj['document_id']; d=obj.get('api_first') or {}
        for c in (d.get('clauses') or []):
            all_clauses.append({"document_id":did,"service_name":obj.get('service_name'),
                                "document_type":obj.get('document_type'),"clause_id":c.get('id'),
                                "section":c.get('section'),"startOffset":c.get('startOffset'),
                                "endOffset":c.get('endOffset'),"clause_text":c.get('text'),
                                "model_prediction_DO_NOT_USE":c.get('label')})
    if not all_clauses:
        print("No clauses found for review sheets"); return
    # representative sample: stratify by document, no prediction use
    by_doc={}
    for c in all_clauses: by_doc.setdefault(c['document_id'],[]).append(c)
    rng=random.Random(SAMPLE_SEED)
    per=max(1, SAMPLE_TARGET_MIN // max(1,len(by_doc)))
    sample=[]; seen=set()
    for did,items in by_doc.items():
        k=min(per,len(items))
        pick=rng.sample(items,k)
        for x in pick:
            key=(x['document_id'],x['clause_id']); 
            if key not in seen: sample.append(x); seen.add(key)
    # fill up to target
    remaining=[c for c in all_clauses if (c['document_id'],c['clause_id']) not in seen]
    rng.shuffle(remaining)
    for x in remaining:
        if len(sample)>=SAMPLE_TARGET_MAX: break
        sample.append(x)
    # blind sheets (no prediction column)
    blind_fields=["sample_id","document_id","service_name","document_type","clause_id","section","startOffset","endOffset","clause_text","human_label","uncertain_or_context_insufficient","notes"]
    for reviewer in ['A','B']:
        path=SHEET_DIR/f"reviewer_{reviewer}_blind_representative_v2.csv"
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=blind_fields); w.writeheader()
            for i,c in enumerate(sample,1):
                w.writerow({"sample_id":f"rep_{i:04d}", **{k:c.get(k,'') for k in blind_fields if k in c or k not in ('sample_id','human_label','uncertain_or_context_insufficient','notes')},
                            "human_label":"","uncertain_or_context_insufficient":"","notes":""})
    # targeted challenge set (separate, clearly labeled; not for representative scoring)
    keywords={
        'arbitration':r'arbitration|class action|waiver of jury|dispute resolution',
        'liability':r'liabilit|indemnif|hold harmless|limitation of damages',
        'content_license':r'license to|royalty-free|perpetual|irrevocable|user content',
        'term_changes':r'change these terms|modify.*terms|update.*agreement|sole discretion',
        'termination':r'terminat|suspend.*account|disable.*access',
        'data_sharing':r'share.*data|third part|advertis|sell.*information|personal data',
        'protective':r'you may delete|opt[- ]out|withdraw consent|data portability|right to access',
    }
    targeted=[]
    for c in all_clauses:
        t=(c.get('clause_text') or '').lower()
        for cat,pat in keywords.items():
            if re.search(pat,t): targeted.append({**c,'challenge_category':cat}); break
    rng.shuffle(targeted); targeted=targeted[:120]
    tpath=SHEET_DIR/"targeted_challenge_set_v2_DO_NOT_MIX_WITH_REPRESENTATIVE.csv"
    with tpath.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=blind_fields+['challenge_category']); w.writeheader()
        for i,c in enumerate(targeted,1):
            w.writerow({"sample_id":f"chal_{i:04d}", **{k:c.get(k,'') for k in w.fieldnames}, "human_label":"","uncertain_or_context_insufficient":"","notes":""})
    meta={"seed":SAMPLE_SEED,"target_range":[SAMPLE_TARGET_MIN,SAMPLE_TARGET_MAX],"representative_count":len(sample),
          "targeted_count":len(targeted),"sampling":"stratified by document (equal-ish per doc) then random fill; model predictions NOT used for inclusion",
          "note":"Representative and targeted sheets are blind (no predictions/confidence). Targeted scores must not be mixed with representative sample."}
    (SHEET_DIR/'review_sampling_meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(f"Review sheets: representative={len(sample)} targeted={len(targeted)} in {SHEET_DIR}")


def try_figures():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"matplotlib unavailable, skipping figures: {e}"); return
    # fig 1: per-document composition
    summary=json.loads((AGG_DIR/'run_summary.json').read_text(encoding='utf-8'))
    ok=[r for r in summary if r.get('api_status')=='ok']
    if ok:
        labels=[r['document_id'] for r in ok]
        risky=[r.get('riskyPct') or 0 for r in ok]; neutral=[r.get('neutralPct') or 0 for r in ok]; safe=[r.get('safePct') or 0 for r in ok]
        x=range(len(labels))
        plt.figure(figsize=(max(8,len(labels)*0.7),5))
        plt.bar(x,safe,label='Safe (pred)'); plt.bar(x,neutral,bottom=safe,label='Neutral (pred)')
        bottom=[s+n for s,n in zip(safe,neutral)]; plt.bar(x,risky,bottom=bottom,label='Risky (pred)')
        plt.xticks(list(x),labels,rotation=45,ha='right',fontsize=7); plt.ylabel('% of clauses (predicted)')
        plt.title('Predicted label composition by document (no human labels)'); plt.legend(); plt.tight_layout()
        plt.savefig(FIG_DIR/'predicted_composition_by_document.png',dpi=150); plt.close()
    # fig 2: extraction issues
    insp=json.loads((AGG_DIR/'extraction_segmentation_inspection.json').read_text(encoding='utf-8'))
    if insp:
        labels=[r['document_id'] for r in insp]
        vals=[len(r.get('issues') or []) + (r.get('span_mismatches') or 0>0) + (r.get('offset_errors') or 0>0) for r in insp]
        plt.figure(figsize=(max(8,len(labels)*0.7),4))
        plt.bar(range(len(labels)),vals); plt.xticks(range(len(labels)),labels,rotation=45,ha='right',fontsize=7)
        plt.ylabel('issue indicators (count)'); plt.title('Extraction/segmentation issue indicators by document'); plt.tight_layout()
        plt.savefig(FIG_DIR/'extraction_issue_indicators.png',dpi=150); plt.close()
    # fig 3: timing
    if ok:
        labels=[r['document_id'] for r in ok]; vals=[r.get('first_s') or 0 for r in ok]
        plt.figure(figsize=(max(8,len(labels)*0.7),4))
        plt.bar(range(len(labels)),vals); plt.xticks(range(len(labels)),labels,rotation=45,ha='right',fontsize=7)
        plt.ylabel('seconds'); plt.title('First API request wall-clock time (curl; not production benchmark)'); plt.tight_layout()
        plt.savefig(FIG_DIR/'first_request_timing.png',dpi=150); plt.close()
    print(f"Figures written to {FIG_DIR}")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['collect','analyze','inspect','review-sheets','figures','all'])
    args=ap.parse_args()
    if args.stage in ('collect','all'): cmd_collect(args)
    if args.stage in ('analyze','all'): cmd_analyze(args)
    if args.stage in ('inspect','all'): inspect_extraction()
    if args.stage in ('review-sheets','all'): build_review_sheets()
    if args.stage in ('figures','all'): try_figures()

if __name__=='__main__': main()
