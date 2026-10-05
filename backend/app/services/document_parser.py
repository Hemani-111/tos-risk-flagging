from abc import ABC, abstractmethod
from typing import Optional
import os


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse document and return extracted text."""
        pass


class PdfParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF parsing. Install it with: pip install PyPDF2")
        
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)


class DocxParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for DOCX parsing. Install it with: pip install python-docx")
        
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)


class TxtParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(f"Could not decode file with any of: {encodings}")


def get_parser(file_extension: str) -> DocumentParser:
    """Return appropriate parser for file extension."""
    parsers = {
        ".pdf": PdfParser(),
        ".docx": DocxParser(),
        ".txt": TxtParser(),
    }
    parser = parsers.get(file_extension.lower())
    if not parser:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    return parser
