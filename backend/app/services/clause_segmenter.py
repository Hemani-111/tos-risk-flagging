import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Clause:
    clause_id: str
    text: str
    section: Optional[str]
    start_offset: int
    end_offset: int


class ClauseSegmenter:
    """Split extracted document text into clauses while retaining source offsets."""

    _numbered = re.compile(r"^\s*(?:\d+\.)+\s+")
    _bullet = re.compile(r"^\s*[-*•▪]\s+")
    _sentence_end = re.compile(r"(?<=[.!?])(?:[\"'’”\)\]]*)\s+(?=[\"'“‘(\[]*[A-Z0-9])")

    def segment(self, text: str, min_clause_length: int = 20) -> List[Clause]:
        if not text or not text.strip():
            return []

        clauses: List[Clause] = []
        section: Optional[str] = None
        run_start: Optional[int] = None
        run_end = 0
        offset = 0

        def flush() -> None:
            nonlocal run_start, run_end
            if run_start is None:
                return
            content = text[run_start:run_end]
            starts = [0]
            starts.extend(match.end() for match in self._sentence_end.finditer(content))
            starts.append(len(content))
            spans: list[tuple[int, int]] = []
            for left, right in zip(starts, starts[1:]):
                a, b = left, right
                while a < b and content[a].isspace():
                    a += 1
                while b > a and content[b - 1].isspace():
                    b -= 1
                if a < b:
                    spans.append((a, b))

            merged: list[tuple[int, int]] = []
            for a, b in spans:
                if merged and b - a < min_clause_length:
                    merged[-1] = (merged[-1][0], b)
                else:
                    merged.append((a, b))
            for a, b in merged:
                clause_text = content[a:b]
                if len(clause_text.strip()) >= min_clause_length:
                    clauses.append(Clause(
                        clause_id=f"clause_{len(clauses) + 1}",
                        text=clause_text,
                        section=section,
                        start_offset=run_start + a,
                        end_offset=run_start + b,
                    ))
            run_start = None

        for line in text.splitlines(keepends=True):
            raw = line.rstrip("\r\n")
            stripped = raw.strip()
            line_start = offset
            offset += len(line)

            if not stripped:
                flush()
                continue

            if self._is_heading(stripped):
                flush()
                section = stripped
                continue

            content_start = line_start + len(raw) - len(raw.lstrip())
            marker = self._numbered.match(text[content_start:line_start + len(raw)])
            if marker is None:
                marker = self._bullet.match(text[content_start:line_start + len(raw)])
            if marker:
                flush()
                content_start += marker.end()

            if run_start is None:
                run_start = content_start
            run_end = line_start + len(raw.rstrip())

        flush()
        return clauses

    def _is_heading(self, line: str) -> bool:
        if line.startswith("#"):
            return True
        numbered_heading = self._numbered.match(line)
        if numbered_heading:
            title = line[numbered_heading.end():]
            if not re.search(r"[.!?]", title) and len(title) < 80 and len(title.split()) <= 7:
                return True
        # Uppercase sentences are content. Only treat short, punctuation-free
        # all-caps lines as headings.
        return (
            line.isupper()
            and len(line) < 120
            and len(line.split()) <= 12
            and not re.search(r"[.!?;:]", line)
        )

    def to_json(self, clauses: List[Clause]) -> List[Dict]:
        return [{
            "clause_id": c.clause_id,
            "text": c.text,
            "section": c.section,
            "start_offset": c.start_offset,
            "end_offset": c.end_offset,
        } for c in clauses]
