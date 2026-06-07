from pathlib import Path
import re

from models import SourceFile

SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".ppt": "ppt", ".pptx": "pptx"}


def natural_sort_key(value: str) -> list[object]:
    parts = re.split(r"(\d+)", value)
    return [int(part) if part.isdigit() else part.casefold() for part in parts]


def _iter_candidates(input_path: Path, include_subdirs: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if include_subdirs:
        return [p for p in input_path.rglob("*") if p.is_file()]
    return [p for p in input_path.iterdir() if p.is_file()]


def discover_sources(input_path: Path | str, include_subdirs: bool = False) -> list[SourceFile]:
    root = Path(input_path)
    if not root.exists():
        raise FileNotFoundError(f"Input path does not exist: {root}")

    sources: list[SourceFile] = []
    for path in _iter_candidates(root, include_subdirs):
        source_type = SUPPORTED_EXTENSIONS.get(path.suffix.lower())
        if source_type:
            sources.append(SourceFile(path=path, source_type=source_type))

    sources.sort(key=lambda item: natural_sort_key(item.path.name))
    return sources
