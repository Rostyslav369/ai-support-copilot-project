from pathlib import Path
from pypdf import PdfReader


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n".join(pages).strip()


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return read_text_file(path)

    if suffix == ".pdf":
        return read_pdf_file(path)

    raise ValueError("Unsupported file type. Only .txt, .md, and .pdf are allowed.")


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks = []
    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(end - overlap, 0)

    return chunks