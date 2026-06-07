import convert_to_pdf
from models import SourceFile


def test_pdf_source_is_returned_without_conversion(tmp_path):
    pdf = tmp_path / "1 海洋法.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    result = convert_to_pdf.normalize_sources_to_pdf([SourceFile(pdf, "pdf")], tmp_path / "work")

    assert result == [pdf]


def test_pptx_conversion_uses_libreoffice(monkeypatch, tmp_path):
    pptx = tmp_path / "2 海洋法.pptx"
    pptx.write_bytes(b"pptx")
    output_pdf = tmp_path / "work" / "2 海洋法.pdf"

    monkeypatch.setattr(
        convert_to_pdf.shutil,
        "which",
        lambda name: "/usr/bin/soffice" if name == "soffice" else None,
    )

    def fake_run(args, check, stdout, stderr):
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        output_pdf.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(convert_to_pdf.subprocess, "run", fake_run)

    result = convert_to_pdf.normalize_sources_to_pdf([SourceFile(pptx, "pptx")], tmp_path / "work")

    assert result == [output_pdf]


def test_pptx_conversion_requires_libreoffice(monkeypatch, tmp_path):
    pptx = tmp_path / "2 海洋法.pptx"
    pptx.write_bytes(b"pptx")
    monkeypatch.setattr(convert_to_pdf.shutil, "which", lambda name: None)

    try:
        convert_to_pdf.normalize_sources_to_pdf([SourceFile(pptx, "pptx")], tmp_path / "work")
    except RuntimeError as exc:
        assert "LibreOffice is required" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
