from pathlib import Path

from models import LayoutConfig, SourceFile


def test_layout_config_defaults_to_a4_landscape_5x4():
    config = LayoutConfig()

    assert config.paper == "a4"
    assert config.orientation == "landscape"
    assert config.grid == "5x4"
    assert config.rows == 4
    assert config.cols == 5
    assert config.cells_per_page == 20


def test_source_file_detects_pdf_and_presentation():
    pdf = SourceFile(path=Path("1 海洋法.pdf"), source_type="pdf")
    pptx = SourceFile(path=Path("2 海洋法.pptx"), source_type="pptx")

    assert pdf.is_pdf
    assert not pdf.needs_conversion
    assert pptx.needs_conversion
