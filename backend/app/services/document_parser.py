from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


class DocumentParsingError(ValueError):
    """The uploaded file could not be safely converted to reviewable text."""


class UnsupportedScannedPDFError(DocumentParsingError):
    """The PDF has no extractable text; OCR is not supported."""


class DocumentLimitError(DocumentParsingError):
    """A parsed document exceeds a configured resource limit."""


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Return extracted text, or raise a useful DocumentParsingError."""


class PdfParser(DocumentParser):
    def __init__(self, max_pages: int = 200, max_chars: int = 2_000_000):
        self.max_pages = max_pages
        self.max_chars = max_chars

    def parse(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path, strict=True)
            if reader.is_encrypted:
                try:
                    if reader.decrypt("") == 0:
                        raise DocumentParsingError("Encrypted PDFs are not supported.")
                except Exception as exc:
                    if isinstance(exc, DocumentParsingError):
                        raise
                    raise DocumentParsingError("Encrypted PDFs are not supported.") from exc
            if len(reader.pages) > self.max_pages:
                raise DocumentLimitError(f"PDF exceeds the {self.max_pages}-page limit.")
            text_parts = []
            char_count = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                char_count += len(page_text)
                if char_count > self.max_chars:
                    raise DocumentLimitError("Extracted text exceeds the 2,000,000-character limit.")
                if page_text:
                    text_parts.append(page_text)
        except DocumentParsingError:
            raise
        except Exception as exc:
            raise DocumentParsingError("This PDF is corrupt or could not be read.") from exc

        text = "\n\n".join(text_parts)
        if not text.strip():
            raise UnsupportedScannedPDFError(
                "No selectable text was found. Scanned or image-only PDFs are unsupported; OCR is not enabled."
            )
        return text


class DocxParser(DocumentParser):
    def __init__(self, max_chars: int = 2_000_000):
        self.max_chars = max_chars

    def parse(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)
        except Exception as exc:
            raise DocumentParsingError("This DOCX file is corrupt or could not be read.") from exc
        if len(text) > self.max_chars:
            raise DocumentLimitError("Extracted text exceeds the 2,000,000-character limit.")
        return text


class TxtParser(DocumentParser):
    def __init__(self, max_chars: int = 2_000_000):
        self.max_chars = max_chars

    def parse(self, file_path: str) -> str:
        path = Path(file_path)
        try:
            # Read one extra character so oversized files are rejected without
            # loading an unbounded text file into memory.
            with path.open("r", encoding="utf-8-sig", errors="strict", newline="") as stream:
                text = stream.read(self.max_chars + 1)
        except UnicodeDecodeError:
            try:
                with path.open("r", encoding="cp1252", errors="strict", newline="") as stream:
                    text = stream.read(self.max_chars + 1)
            except Exception as exc:
                raise DocumentParsingError("Text file encoding is unsupported; save it as UTF-8.") from exc
        except OSError as exc:
            raise DocumentParsingError("Text file could not be read.") from exc
        if len(text) > self.max_chars:
            raise DocumentLimitError("Extracted text exceeds the 2,000,000-character limit.")
        return text


def get_parser(file_extension: str) -> DocumentParser:
    parsers = {
        ".pdf": PdfParser(max_pages=settings.PDF_MAX_PAGES, max_chars=settings.MAX_EXTRACTED_CHARS),
        ".docx": DocxParser(max_chars=settings.MAX_EXTRACTED_CHARS),
        ".txt": TxtParser(max_chars=settings.MAX_EXTRACTED_CHARS),
    }
    parser = parsers.get(file_extension.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {file_extension}")
    return parser
