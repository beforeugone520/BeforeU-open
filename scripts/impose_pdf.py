from pathlib import Path
import csv

import fitz

from models import LayoutConfig, PageMapEntry

A4_PORTRAIT = (595, 842)
A4_LANDSCAPE = (842, 595)


def _page_size(config: LayoutConfig) -> tuple[float, float]:
    if config.orientation == "portrait":
        return A4_PORTRAIT
    return A4_LANDSCAPE


def impose_pdfs(
    pdf_paths: list[Path],
    output_pdf: Path,
    page_map_csv: Path,
    config: LayoutConfig,
    titles_by_pdf: dict[Path, list[str]] | None = None,
) -> list[PageMapEntry]:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    page_map_csv.parent.mkdir(parents=True, exist_ok=True)
    titles_by_pdf = titles_by_pdf or {}

    out = fitz.open()
    width, height = _page_size(config)
    margin = 18
    gutter = 6
    cell_width = (width - 2 * margin - (config.cols - 1) * gutter) / config.cols
    cell_height = (height - 2 * margin - (config.rows - 1) * gutter) / config.rows
    entries: list[PageMapEntry] = []
    cell_index = 0
    current_page = None

    for pdf_path in pdf_paths:
        with fitz.open(pdf_path) as src:
            titles = titles_by_pdf.get(pdf_path, [])
            for source_page_index in range(src.page_count):
                if cell_index % config.cells_per_page == 0:
                    current_page = out.new_page(width=width, height=height)
                imposed_page = len(out)
                position = cell_index % config.cells_per_page
                row = position // config.cols
                col = position % config.cols
                x0 = margin + col * (cell_width + gutter)
                y0 = margin + row * (cell_height + gutter)
                rect = fitz.Rect(x0, y0, x0 + cell_width, y0 + cell_height)
                current_page.show_pdf_page(rect, src, source_page_index)
                title = titles[source_page_index] if source_page_index < len(titles) else ""
                entries.append(
                    PageMapEntry(
                        source_file=pdf_path.name,
                        source_page=source_page_index + 1,
                        imposed_page=imposed_page,
                        grid_row=row + 1,
                        grid_col=col + 1,
                        title=title,
                    )
                )
                cell_index += 1

    _stamp_page_numbers(out)
    out.save(output_pdf)
    out.close()
    _write_page_map(entries, page_map_csv)
    return entries


def _stamp_page_numbers(doc: fitz.Document) -> None:
    for index, page in enumerate(doc, start=1):
        rect = page.rect
        page.insert_textbox(
            fitz.Rect(rect.width - 150, rect.height - 20, rect.width - 18, rect.height - 5),
            f"第 {index} 页",
            fontname="china-s",
            fontsize=8,
            color=(0.05, 0.05, 0.05),
            align=2,
        )


def _write_page_map(entries: list[PageMapEntry], output: Path) -> None:
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_file", "source_page", "imposed_page", "grid_row", "grid_col", "title"])
        for entry in entries:
            writer.writerow(
                [
                    entry.source_file,
                    entry.source_page,
                    entry.imposed_page,
                    entry.grid_row,
                    entry.grid_col,
                    entry.title,
                ]
            )
