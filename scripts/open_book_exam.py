from datetime import datetime
from pathlib import Path
import argparse
import shutil
import sys

from build_index import (
    catalog_lines_from_analysis,
    catalog_lines_from_entries,
    catalog_entries_from_analysis,
    chapter_ranges_from_analysis_catalog,
    load_analysis_payload,
    load_analysis_items,
    write_analysis_input_json,
    write_analysis_template_json,
    write_catalog_markdown,
    write_catalog_pdf,
    write_catalog_pdf_from_analysis,
    write_combined_catalog_and_key_points_pdf,
    write_key_points_pdf_from_analysis,
)
from convert_to_pdf import normalize_sources_to_pdf
from dependency_utils import install_missing
from extract_outline import extract_pdf_page_texts, extract_pdf_page_titles
from file_order import discover_sources
from impose_pdf import impose_pdfs
from models import LayoutConfig


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build A4 open-book exam print materials.")
    parser.add_argument("input_path")
    parser.add_argument("--output-dir")
    parser.add_argument("--paper", default="a4", choices=["a4"])
    parser.add_argument("--orientation", default="landscape", choices=["landscape", "portrait"])
    parser.add_argument("--grid", choices=["5x5", "5x4", "4x4"])
    parser.add_argument("--catalog-mode", default="combined-lookup", choices=["embedded", "separate", "combined-lookup"])
    parser.add_argument("--install-missing", action="store_true")
    parser.add_argument("--include-subdirs", action="store_true")
    parser.add_argument("--exam-brief")
    parser.add_argument("--analysis-json")
    return parser.parse_args(argv)


def _output_parent(input_path: Path, output_parent: Path | None) -> Path:
    return output_parent if output_parent is not None else (input_path.parent if input_path.is_file() else input_path)


def _run_dir(input_path: Path, output_parent: Path | None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parent = _output_parent(input_path, output_parent)
    return parent / f"开卷考输出-{stamp}"


def _latest_reusable_run_dir(input_path: Path, output_parent: Path | None) -> Path | None:
    parent = _output_parent(input_path, output_parent)
    if not parent.exists():
        return None
    candidates = [
        path
        for path in parent.glob("开卷考输出-*")
        if path.is_dir() and (path / "_support" / "AI分析输入.json").exists()
    ]
    return max(candidates, key=lambda path: path.name) if candidates else None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.grid is None:
        print("请先指定合并规格：--grid 4x4、--grid 5x4 或 --grid 5x5。", file=sys.stderr)
        return 2
    input_path = Path(args.input_path)
    output_parent = Path(args.output_dir) if args.output_dir else None
    reused_run_dir = bool(args.analysis_json and not args.output_dir)
    run_dir = _latest_reusable_run_dir(input_path, output_parent) if reused_run_dir else None
    if run_dir is None:
        reused_run_dir = False
        run_dir = _run_dir(input_path, output_parent)
    run_dir.mkdir(parents=True, exist_ok=reused_run_dir)
    support_dir = run_dir / "_support"
    markdown_dir = support_dir / "markdown"
    typst_dir = support_dir / "typst"
    support_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    typst_dir.mkdir(parents=True, exist_ok=True)
    report_lines: list[str] = []
    if reused_run_dir:
        report_lines.append(f"Reused output directory: {run_dir}")

    if args.install_missing:
        report_lines.extend(install_missing(auto_install=True))

    sources = discover_sources(input_path, include_subdirs=args.include_subdirs)
    if not sources:
        raise RuntimeError(f"No supported PDF/PPT/PPTX files found in {input_path}")

    report_lines.append("Input order:")
    report_lines.extend(f"- {source.path}" for source in sources)

    work_dir = support_dir / "converted-pdf"
    pdfs = normalize_sources_to_pdf(sources, work_dir)
    titles_by_pdf = {pdf: extract_pdf_page_titles(pdf) for pdf in pdfs}
    texts_by_pdf = {pdf: extract_pdf_page_texts(pdf) for pdf in pdfs}
    config = LayoutConfig(paper=args.paper, orientation=args.orientation, grid=args.grid)
    entries = impose_pdfs(pdfs, run_dir / "开卷考打印版.pdf", support_dir / "页码映射.csv", config, titles_by_pdf)
    write_catalog_markdown(entries, markdown_dir / "目录.md")
    write_catalog_pdf(entries, run_dir / "目录.pdf", typst_dir / "目录.typ")
    page_texts = {}
    for pdf in pdfs:
        for index, text in enumerate(texts_by_pdf.get(pdf, []), start=1):
            page_texts[(pdf.name, index)] = text
    write_analysis_input_json(entries, support_dir / "AI分析输入.json", page_texts, exam_brief=args.exam_brief)
    write_analysis_template_json(support_dir / "AI分析结果模板.json")
    if args.analysis_json:
        analysis_json_path = Path(args.analysis_json)
        analysis_payload = load_analysis_payload(analysis_json_path)
        analysis_items = load_analysis_items(analysis_json_path)
        analysis_copy_path = support_dir / "AI分析结果.json"
        if analysis_json_path.resolve() != analysis_copy_path.resolve():
            shutil.copyfile(analysis_json_path, analysis_copy_path)
        analysis_catalog = catalog_entries_from_analysis(analysis_payload)
        if analysis_catalog:
            catalog_pdf_path = run_dir / "目录.pdf" if args.catalog_mode == "separate" else support_dir / "目录.pdf"
            write_catalog_pdf_from_analysis(analysis_catalog, catalog_pdf_path, typst_dir / "目录.typ")
            chapter_ranges = chapter_ranges_from_analysis_catalog(analysis_catalog)
            catalog_lines = catalog_lines_from_analysis(analysis_catalog)
        else:
            chapter_ranges = {}
            catalog_lines = catalog_lines_from_entries(entries)
        if args.catalog_mode == "separate":
            write_key_points_pdf_from_analysis(
                analysis_items,
                run_dir / "课程重点.pdf",
                chapter_ranges=chapter_ranges,
                typst_source=typst_dir / "课程重点.typ",
            )
        else:
            write_combined_catalog_and_key_points_pdf(
                catalog_lines,
                analysis_items,
                run_dir / "课程重点.pdf",
                chapter_ranges=chapter_ranges,
                typst_source=typst_dir / "课程重点.typ",
            )
            _remove_default_separate_catalog(run_dir)
        _remove_legacy_lookup_outputs(run_dir, typst_dir)
        report_lines.append(f"AI analysis result: {args.analysis_json}")
    else:
        report_lines.append("课程重点.pdf 未生成：需要AI先根据 AI分析输入.json 产出 AI分析结果.json，再用 --analysis-json 渲染。")
    report_lines.append(f"Layout: {args.paper} {args.orientation} {args.grid}")
    report_lines.append(f"Catalog mode: {args.catalog_mode}")
    if args.exam_brief:
        report_lines.append(f"Exam brief: {args.exam_brief}")
    (support_dir / "运行报告.md").write_text("# 运行报告\n\n" + "\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Output written to: {run_dir}")
    return 0


def _remove_legacy_lookup_outputs(run_dir: Path, typst_dir: Path) -> None:
    for path in (run_dir / "开卷速查.pdf", typst_dir / "开卷速查.typ"):
        if path.exists():
            path.unlink()


def _remove_default_separate_catalog(run_dir: Path) -> None:
    path = run_dir / "目录.pdf"
    if path.exists():
        path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
