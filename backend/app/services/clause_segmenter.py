import re
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Clause:
    clause_id: str
    text: str
    section: Optional[str]
    start_offset: int
    end_offset: int


class ClauseSegmenter:
    """Split document text into meaningful clauses/sections."""
    
    def __init__(self):
        # Heading patterns
        self.heading_pattern = re.compile(
            r"^(#{1,6}\s+.+|(?:[A-Z][A-Z\s]+)$|(?:^\d+\.\s+[A-Z])|(?:^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*$))",
            re.MULTILINE
        )
        self.numbered_section = re.compile(r"^(\d+\.)+\s+", re.MULTILINE)
        self.bullet_point = re.compile(r"^[\-\*•]\s+", re.MULTILINE)
        self.empty_line = re.compile(r"^\s*$", re.MULTILINE)
    
    def segment(self, text: str, min_clause_length: int = 20) -> List[Clause]:
        """
        Segment document text into clauses.
        
        Strategy:
        1. Detect headings and numbered sections
        2. Detect paragraph boundaries
        3. Detect bullet points
        4. Merge very short fragments
        5. Preserve section hierarchy
        """
        if not text or not text.strip():
            return []
        
        lines = text.split("\n")
        clauses = []
        current_section = None
        current_text_parts = []
        current_start = 0
        clause_index = 0
        
        def flush_clause(text_parts, section, start_offset, end_offset):
            text = " ".join(text_parts).strip()
            if not text or len(text) < min_clause_length:
                return None
            return Clause(
                clause_id=f"clause_{clause_index}",
                text=text,
                section=section,
                start_offset=start_offset,
                end_offset=end_offset,
            )
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect headings
            if self._is_heading(stripped):
                # Flush previous clause
                if current_text_parts:
                    end = sum(len(p) for p in current_text_parts) + len(current_text_parts) - 1
                    clause = flush_clause(current_text_parts, current_section, current_start, current_start + end)
                    if clause:
                        clauses.append(clause)
                        clause_index += 1
                    current_text_parts = []
                
                current_section = stripped
                continue
            
            # Skip empty lines but flush if we have content
            if not stripped:
                if current_text_parts:
                    end = sum(len(p) for p in current_text_parts) + len(current_text_parts) - 1
                    clause = flush_clause(current_text_parts, current_section, current_start, current_start + end)
                    if clause:
                        clauses.append(clause)
                        clause_index += 1
                    current_text_parts = []
                continue
            
            # Add to current clause
            if not current_text_parts:
                current_start = i
            current_text_parts.append(stripped)
        
        # Flush remaining
        if current_text_parts:
            end = sum(len(p) for p in current_text_parts) + len(current_text_parts) - 1
            clause = flush_clause(current_text_parts, current_section, current_start, current_start + end)
            if clause:
                clauses.append(clause)
        
        return clauses
    
    def _is_heading(self, line: str) -> bool:
        """Determine if a line is a section heading."""
        if not line:
            return False
        # All caps
        if line.isupper() and len(line) > 3:
            return True
        # Numbered section like "1. Introduction"
        if re.match(r"^\d+\.\s+[A-Z]", line):
            return True
        # Markdown heading
        if line.startswith("#"):
            return True
        return False
    
    def to_json(self, clauses: List[Clause]) -> List[Dict]:
        """Convert clauses to JSON-serializable format."""
        return [
            {
                "clause_id": c.clause_id,
                "text": c.text,
                "section": c.section,
                "start_offset": c.start_offset,
                "end_offset": c.end_offset,
            }
            for c in clauses
        ]
