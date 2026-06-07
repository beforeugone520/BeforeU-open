from pathlib import Path

import fitz

from impose_pdf import impose_pdfs
from models import LayoutConfig


def _make_pdf(path: Path, pages: int) -> None:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page(width=200, height=120)
        page.insert_text((24, 48), f"page {index + 1}")
    doc.save(path)
    doc.close()


def test_impose_pdfs_creates_expected_page_map(tmp_path):
    source = tmp_path / "1 海洋法.pdf"
    _make_pdf(source, 3)
    output_pdf = tmp_path / "print-pack.pdf"
    page_map_csv = tmp_path / "page-map.csv"

    entries = impose_pdfs([source], output_pdf, page_map_csv, LayoutConfig(grid="2x2"))

    assert output_pdf.exists()
    assert page_map_csv.exists()
    assert len(entries) == 3
    assert entries[0].imposed_page == 1
    assert entries[0].grid_row == 1
    assert entries[0].grid_col == 1
    assert entries[2].grid_row == 2
    assert entries[2].grid_col == 1
    with fitz.open(output_pdf) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    assert "第 1 页" in text
    assert "合并PDF" not in text
