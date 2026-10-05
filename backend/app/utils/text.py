import os
import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in extracted text."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    filename = os.path.basename(filename)
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    return filename[:255]


def is_safe_path(path: str, base_dir: str) -> bool:
    """Ensure path is within base_dir."""
    real_path = os.path.realpath(path)
    real_base = os.path.realpath(base_dir)
    return real_path.startswith(real_base)
