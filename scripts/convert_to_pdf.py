from pathlib import Path
import shutil
import subprocess

from models import SourceFile


def _libreoffice_binary() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def convert_presentation_to_pdf(source: Path, work_dir: Path) -> Path:
    binary = _libreoffice_binary()
    if not binary:
        raise RuntimeError("LibreOffice is required to convert PPT/PPTX files to PDF")
    work_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [binary, "--headless", "--convert-to", "pdf", "--outdir", str(work_dir), str(source)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = work_dir / f"{source.stem}.pdf"
    if not output.exists():
        raise RuntimeError(f"LibreOffice did not create expected PDF: {output}")
    return output


def normalize_sources_to_pdf(sources: list[SourceFile], work_dir: Path | str) -> list[Path]:
    output_dir = Path(work_dir)
    pdfs: list[Path] = []
    for source in sources:
        if source.is_pdf:
            pdfs.append(source.path)
        elif source.needs_conversion:
            pdfs.append(convert_presentation_to_pdf(source.path, output_dir))
        else:
            raise ValueError(f"Unsupported source type: {source.source_type}")
    return pdfs
