from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LayoutConfig:
    paper: str = "a4"
    orientation: str = "landscape"
    grid: str = "5x4"

    @property
    def cols(self) -> int:
        return int(self.grid.split("x", 1)[0])

    @property
    def rows(self) -> int:
        return int(self.grid.split("x", 1)[1])

    @property
    def cells_per_page(self) -> int:
        return self.cols * self.rows


@dataclass(frozen=True)
class SourceFile:
    path: Path
    source_type: str

    @property
    def is_pdf(self) -> bool:
        return self.source_type == "pdf"

    @property
    def needs_conversion(self) -> bool:
        return self.source_type in {"ppt", "pptx"}


@dataclass(frozen=True)
class PdfPageRef:
    source_file: Path
    normalized_pdf: Path
    source_page: int
    title: str = ""


@dataclass(frozen=True)
class PageMapEntry:
    source_file: str
    source_page: int
    imposed_page: int
    grid_row: int
    grid_col: int
    title: str = ""


@dataclass
class RunReport:
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    dependency_lines: list[str] = field(default_factory=list)
