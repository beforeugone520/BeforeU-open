from collections import defaultdict
from pathlib import Path
import json
from typing import Literal

from models import PageMapEntry
from typst_renderer import write_typst_pdf

LineKind = Literal["title", "chapter", "section", "body", "muted", "blank"]


def write_catalog_markdown(entries: list[PageMapEntry], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[PageMapEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.source_file].append(entry)

    lines = ["# 目录", ""]
    for source_file, group in grouped.items():
        lines.append(f"## {source_file}")
        for entry in group:
            title = entry.title or "未抽取标题"
            lines.append(
                f"- {title}：源页 {entry.source_page}，拼版页 {entry.imposed_page}，"
                f"格子 R{entry.grid_row}C{entry.grid_col}"
            )
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def write_catalog_pdf(entries: list[PageMapEntry], output: Path, typst_source: Path | None = None) -> None:
    lines = catalog_lines_from_entries(entries, include_title=True)
    write_typst_pdf(lines, output, typst_source)


def catalog_lines_from_entries(
    entries: list[PageMapEntry],
    include_title: bool = False,
) -> list[tuple[str, LineKind]]:
    lines: list[tuple[str, LineKind]] = [("目录", "title")] if include_title else []
    grouped: dict[str, list[PageMapEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.source_file].append(entry)
    for source_file, group in grouped.items():
        first_page = min(entry.imposed_page for entry in group)
        last_page = max(entry.imposed_page for entry in group)
        page_range = _format_page_range(first_page, last_page)
        lines.append((f"{source_file}（{page_range}）", "chapter"))
        seen_titles: set[str] = set()
        for entry in group:
            title = (entry.title or "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            lines.append((f"第 {entry.imposed_page} 页｜{title}", "body"))
            if len(seen_titles) >= 8:
                remaining = len([e for e in group if (e.title or "").strip() not in seen_titles])
                if remaining:
                    lines.append((f"另有 {remaining} 个页面标题，详见 _support/页码映射.csv", "muted"))
                break
        lines.append(("", "blank"))
    return lines


def catalog_entries_from_analysis(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_entries = payload.get("目录", [])
    if not isinstance(raw_entries, list):
        return []
    entries: list[dict[str, object]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue
        chapter = str(raw_entry.get("章节") or "").strip()
        subtitle = str(raw_entry.get("小节") or "").strip()
        page = _coerce_positive_int(raw_entry.get("拼版页"))
        if not chapter or not subtitle or page is None:
            continue
        entries.append({"章节": chapter, "小节": subtitle, "拼版页": page})
    return entries


def write_catalog_pdf_from_analysis(
    analysis_catalog: list[dict[str, object]],
    output: Path,
    typst_source: Path | None = None,
) -> None:
    lines = catalog_lines_from_analysis(analysis_catalog, include_title=True)
    write_typst_pdf(lines, output, typst_source)


def catalog_lines_from_analysis(
    analysis_catalog: list[dict[str, object]],
    include_title: bool = False,
) -> list[tuple[str, LineKind]]:
    lines: list[tuple[str, LineKind]] = [("目录", "title")] if include_title else []
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in analysis_catalog:
        grouped[str(entry["章节"])].append(entry)

    for chapter, group in grouped.items():
        pages = [int(entry["拼版页"]) for entry in group]
        lines.append((f"{chapter}（{_format_page_range(min(pages), max(pages))}）", "chapter"))
        seen: set[tuple[str, int]] = set()
        for entry in group:
            subtitle = str(entry["小节"])
            page = int(entry["拼版页"])
            key = (subtitle, page)
            if key in seen:
                continue
            seen.add(key)
            lines.append((f"{subtitle}：第 {page} 页", "body"))
        lines.append(("", "blank"))
    return lines


def chapter_ranges_from_analysis_catalog(analysis_catalog: list[dict[str, object]]) -> dict[str, str]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for entry in analysis_catalog:
        chapter = str(entry.get("章节") or "").strip()
        page = _coerce_positive_int(entry.get("拼版页"))
        if chapter and page is not None:
            grouped[chapter].append(page)
    return {
        chapter: _format_page_range(min(pages), max(pages))
        for chapter, pages in grouped.items()
        if pages
    }


def _coerce_positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        page = int(value.strip())
        return page if page > 0 else None
    return None


def _format_page_range(first_page: int, last_page: int) -> str:
    if first_page == last_page:
        return f"第 {first_page} 页"
    return f"第 {first_page}-{last_page} 页"


def write_analysis_input_json(
    entries: list[PageMapEntry],
    output: Path,
    page_texts: dict[tuple[str, int], str] | None = None,
    exam_brief: str | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    page_texts = page_texts or {}
    payload = {
        "说明": "这是给AI分析用的结构化输入。AI应按SKILL.md约束生成AI分析结果.json，再由脚本渲染课程重点.pdf。",
        "考试要求": (exam_brief or "").strip(),
        "页面": [
            {
                "来源文件": entry.source_file,
                "源页": entry.source_page,
                "拼版页": entry.imposed_page,
                "格子位置": f"R{entry.grid_row}C{entry.grid_col}",
                "页面标题候选": entry.title,
                "页面文本": page_texts.get((entry.source_file, entry.source_page), ""),
            }
            for entry in entries
        ],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_analysis_template_json(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "课程名称": "",
        "目录": [
            {
                "章节": "第一章 章节名",
                "小节": "AI整理后的目录小标题",
                "拼版页": 1,
            }
        ],
        "重点": [
            {
                "章节": "",
                "关键词或思考题": "",
                "解释或答案": "",
                "来源文件": "",
                "源页": 1,
                "拼版页": 1,
                "备注": "AI根据课件内容、思考题、反复出现概念或考纲提示整理",
            }
        ],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_analysis_items(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("重点", [])
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("AI分析结果必须是对象或列表")
    if not isinstance(items, list):
        raise ValueError("AI分析结果中的“重点”必须是列表")
    return [item for item in items if isinstance(item, dict)]


def load_analysis_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"重点": payload}
    raise ValueError("AI分析结果必须是对象或列表")


def write_key_points_pdf_from_analysis(
    items: list[dict[str, object]],
    output: Path,
    title: str = "课程重点",
    chapter_ranges: dict[str, str] | None = None,
    typst_source: Path | None = None,
) -> None:
    lines = key_points_lines_from_analysis(items, title, chapter_ranges, include_title=True)
    write_typst_pdf(lines, output, typst_source)


def key_points_lines_from_analysis(
    items: list[dict[str, object]],
    title: str = "课程重点",
    chapter_ranges: dict[str, str] | None = None,
    include_title: bool = False,
) -> list[tuple[str, LineKind]]:
    lines: list[tuple[str, LineKind]] = [(title, "title")] if include_title else []
    chapter_ranges = chapter_ranges or {}
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in items:
        chapter = str(item.get("章节") or "未标注章节")
        grouped[chapter].append(item)

    index_lines = _key_point_index_lines(grouped, chapter_ranges)
    if index_lines:
        lines.append(("关键词索引", "section"))
        lines.extend((line, "body") for line in index_lines)
        lines.append(("", "blank"))

    for chapter, group in grouped.items():
        terms: list[tuple[str, str]] = []
        questions: list[tuple[str, str]] = []
        others: list[tuple[str, str]] = []
        for item in group:
            raw_keyword = str(item.get("关键词或思考题") or "未标注关键词/思考题")
            answer = str(item.get("解释或答案") or "未填写解释/答案")
            category, keyword = _classify_key_point(raw_keyword, answer)
            if category == "term":
                terms.append((keyword, answer))
            elif category == "question":
                questions.append((keyword, answer))
            else:
                others.append((keyword, answer))

        range_text = chapter_ranges.get(chapter, "")
        chapter_heading = f"章节：{chapter}"
        if range_text:
            chapter_heading += f"（{range_text}）"
        lines.append((chapter_heading, "chapter"))
        if terms:
            lines.append(("重点名词解释", "section"))
            for keyword, answer in terms:
                lines.append((f"- {keyword}：{answer}", "body"))
        if questions:
            lines.append(("思考题", "section"))
            for index, (keyword, answer) in enumerate(questions, start=1):
                lines.append((f"{index}. {keyword}", "body"))
                lines.append((answer if answer.startswith("答：") else f"答：{answer}", "muted"))
        if others:
            lines.append(("其他重点", "section"))
            for keyword, answer in others:
                lines.append((f"- {keyword}：{answer}", "body"))
        lines.append(("", "blank"))
    return lines


def write_combined_catalog_and_key_points_pdf(
    catalog_lines: list[tuple[str, LineKind]],
    items: list[dict[str, object]],
    output: Path,
    title: str = "课程重点",
    chapter_ranges: dict[str, str] | None = None,
    typst_source: Path | None = None,
) -> None:
    lines: list[tuple[str, LineKind]] = [(title, "title")]
    if catalog_lines:
        lines.append(("目录", "section"))
        lines.extend(catalog_lines)
    key_point_lines = key_points_lines_from_analysis(items, chapter_ranges=chapter_ranges)
    if catalog_lines and key_point_lines:
        lines.append(("课程重点", "section"))
    lines.extend(key_point_lines)
    write_typst_pdf(lines, output, typst_source)


def _key_point_index_lines(
    grouped: dict[str, list[dict[str, object]]],
    chapter_ranges: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for chapter, group in grouped.items():
        range_text = chapter_ranges.get(chapter, "")
        location = f"{chapter}（{range_text}）" if range_text else chapter
        for item in group:
            raw_keyword = str(item.get("关键词或思考题") or "").strip()
            if not raw_keyword:
                continue
            _, keyword = _classify_key_point(raw_keyword, str(item.get("解释或答案") or ""))
            keyword = keyword.strip()
            if not keyword:
                continue
            key = (keyword, location)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- {keyword}：{location}")
    return lines


def _classify_key_point(keyword: str, answer: str) -> tuple[str, str]:
    keyword = keyword.strip()
    term_prefixes = ["【重点名词解释】", "重点名词解释：", "名词解释："]
    question_prefixes = ["【思考题】", "思考题：", "问题："]
    for prefix in term_prefixes:
        if keyword.startswith(prefix):
            return "term", keyword[len(prefix) :].strip()
    for prefix in question_prefixes:
        if keyword.startswith(prefix):
            return "question", keyword[len(prefix) :].strip()
    if keyword.endswith(("？", "?")) or answer.startswith("答："):
        return "question", keyword
    return "term", keyword
