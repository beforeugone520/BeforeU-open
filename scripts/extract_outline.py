from pathlib import Path
import re


def infer_chapter_label_from_filename(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"[（(]\d+[）)]$", "", stem).strip()
    stem = re.sub(r"\s+20\d{2}$", "", stem).strip()
    match = re.match(r"^(\d+(?:-\d+)?)\s*章?\s*(.*)$", stem)
    if not match:
        return stem
    chapter, rest = match.groups()
    rest = rest.strip()
    if rest:
        return f"{chapter}章 {rest}"
    return f"{chapter}章"


def extract_pdf_page_titles(pdf_path: Path) -> list[str]:
    try:
        import fitz
    except ImportError:
        return []
    titles: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text").strip()
            first_line = text.splitlines()[0].strip() if text.splitlines() else ""
            titles.append(first_line[:80])
    return titles


def extract_pdf_page_texts(pdf_path: Path, max_chars: int = 3000) -> list[str]:
    try:
        import fitz
    except ImportError:
        return []
    texts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text").strip()
            texts.append(text[:max_chars])
    return texts
