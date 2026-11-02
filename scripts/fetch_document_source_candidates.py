"""Fetch public official candidate policy snapshots for human annotation.

Snapshot files are kept locally under data/review/snapshots_v1 and are ignored
by Git because the source documents may be copyrighted.
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "review" / "document_sources_candidates_v1.csv"
OUT = ROOT / "data" / "review" / "snapshots_v1"
DOWNLOADS = {
    "anthropic_consumer_terms": ("https://assets.claude.com/43c13f51a6d9755341433f79cf63c966ed9200ea.pdf", "pdf"),
    "anthropic_privacy": ("https://assets.claude.com/693a25036936f7e7bf4dd0c299a2e654f14fac01.pdf", "pdf"),
    "mistral_consumer_terms_row": ("https://legal.mistral.ai/terms/row-consumer-terms/", "html"),
    "mistral_privacy": ("https://legal.mistral.ai/terms/privacy-policy/", "html"),
    "perplexity_consumer_terms": ("https://www.perplexity.ai/hub/legal/terms-of-service", "html"),
    "perplexity_privacy": ("https://www.perplexity.ai/hub/legal/privacy-policy", "html"),
    "you_com_terms": ("https://about.you.com/legal/terms", "html"),
    "you_com_privacy": ("https://you.com/privacy", "html"),
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def repair_common_mojibake(text: str) -> str:
    """Undo UTF-8 punctuation decoded once as Windows-1252 when it is evident."""
    markers = ("â€™", "â€œ", "â€", "Ã©", "Ã—", "Â ")
    if not any(marker in text for marker in markers):
        return text
    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired if sum(text.count(x) for x in markers) > sum(repaired.count(x) for x in markers) else text


class VisibleText(HTMLParser):
    """Extract visible body text while skipping navigation and executable content."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self.depth += 1
        elif not self.depth and tag in {"p", "li", "h1", "h2", "h3", "h4", "br", "tr", "td", "th", "section", "article"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        elif not self.depth and tag in {"p", "li", "h1", "h2", "h3", "h4", "tr", "section", "article"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.depth:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
        fields = list(rows[0])
    additions = ["snapshot_download_url", "snapshot_final_url", "content_type", "snapshot_path", "local_snapshot_path", "text_snapshot_path", "text_sha256", "snapshot_timestamp_utc", "pdf_page_count", "fetch_error"]
    for field in additions:
        if field not in fields:
            fields.append(field)
    seen = set()
    for row in rows:
        doc_id = row["document_id"]
        if doc_id not in DOWNLOADS:
            continue
        url, kind = DOWNLOADS[doc_id]
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read()
                final_url = response.geturl()
                content_type = response.headers.get_content_type()
        except (HTTPError, URLError, TimeoutError) as exc:
            row["review_status"] = f"snapshot_fetch_failed:{getattr(exc, 'code', type(exc).__name__)}"
            row["fetch_error"] = str(exc)
            print(f"{doc_id}: fetch failed: {exc}", file=sys.stderr)
            continue
        if not raw:
            raise RuntimeError(f"Empty response from {url}")
        suffix = "pdf" if kind == "pdf" else "html"
        raw_path = OUT / f"{doc_id}.{suffix}"
        raw_path.write_bytes(raw)
        if kind == "pdf":
            reader = PdfReader(str(raw_path), strict=False)
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
            text_path = OUT / f"{doc_id}.txt"
            text_path.write_text(text, encoding="utf-8")
            page_count = len(reader.pages)
        else:
            parser = VisibleText()
            parser.feed(raw.decode("utf-8", errors="replace"))
            text = repair_common_mojibake(re.sub(r"\n{3,}", "\n\n", "\n".join(parser.parts)).strip())
            text_path = OUT / f"{doc_id}.txt"
            text_path.write_text(text, encoding="utf-8")
            page_count = ""
        if len(text) < 1000:
            raise RuntimeError(f"Visible text extraction looks incomplete for {doc_id}: {len(text)} characters")
        rel_raw = str(raw_path.relative_to(ROOT)).replace("\\", "/")
        rel_text = str(text_path.relative_to(ROOT)).replace("\\", "/")
        row.update({
            "snapshot_sha256": sha256(raw), "review_status": "snapshot_frozen_review_pending",
            "snapshot_download_url": url, "snapshot_final_url": final_url, "content_type": content_type,
            "snapshot_path": rel_raw, "local_snapshot_path": rel_raw, "text_snapshot_path": rel_text,
            "text_sha256": sha256(text.encode("utf-8")), "snapshot_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "retrieved_date": datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat(), "pdf_page_count": page_count,
        })
        seen.add(doc_id)
        print(f"{doc_id}: {len(raw):,} bytes, {len(text):,} extracted characters, {page_count or 'HTML'} pages, sha256={row['snapshot_sha256']}")
    temporary_registry = REGISTRY.with_suffix(".csv.tmp")
    with temporary_registry.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary_registry.replace(REGISTRY)
    print(f"Fetched {len(seen)} of {len(DOWNLOADS)} candidates; missing snapshots: {sorted(set(DOWNLOADS) - seen)}")


if __name__ == "__main__":
    main()
