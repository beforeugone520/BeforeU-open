from pathlib import Path

import fitz

from build_index import (
    catalog_entries_from_analysis,
    chapter_ranges_from_analysis_catalog,
    write_analysis_input_json,
    write_catalog_markdown,
    write_catalog_pdf,
    write_catalog_pdf_from_analysis,
    write_key_points_pdf_from_analysis,
)
from extract_outline import infer_chapter_label_from_filename
from models import PageMapEntry


def test_infer_chapter_label_from_filename_handles_ranges():
    assert infer_chapter_label_from_filename(Path("21-22章战时海洋法 2024(1).pdf")) == "21-22章 战时海洋法"
    assert infer_chapter_label_from_filename(Path("13 海洋法 海洋环境保护.pdf")) == "13章 海洋法 海洋环境保护"


def test_write_catalog_markdown_groups_by_source_file(tmp_path):
    entries = [
        PageMapEntry("1 海洋法.pdf", 1, 1, 1, 1, "绪论"),
        PageMapEntry("1 海洋法.pdf", 2, 1, 1, 2, "海洋法概念"),
    ]
    output = tmp_path / "catalog.md"

    write_catalog_markdown(entries, output)

    text = output.read_text(encoding="utf-8")
    assert "# 目录" in text
    assert "## 1 海洋法.pdf" in text
    assert "源页 1" in text
    assert "拼版页 1" in text


def test_write_catalog_pdf_writes_printable_chinese_pdf(tmp_path):
    entries = [PageMapEntry("1 海洋法.pdf", 1, 1, 1, 1, "海洋法概念")]
    output = tmp_path / "目录.pdf"

    write_catalog_pdf(entries, output)

    with fitz.open(output) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    assert "目录" in text
    assert "海洋法概念" in text
    assert "第 1 页" in text
    assert "合并PDF" not in text
    assert "源页" not in text
    assert "格子" not in text
    typst_source = output.with_suffix(".typ")
    assert typst_source.exists()
    assert "海洋法概念" in typst_source.read_text(encoding="utf-8")


def test_write_key_points_pdf_uses_ai_analysis_result_structure(tmp_path):
    analysis_items = [
        {
            "章节": "1 海洋法.pdf",
            "关键词或思考题": "【重点名词解释】领海",
            "解释或答案": "领海是沿海国基线以外一定宽度的海域，沿海国享有主权，但外国船舶享有无害通过权。",
            "来源文件": "1 海洋法.pdf",
            "源页": 1,
            "拼版页": 1,
            "备注": "AI根据课件思考题整理",
        },
        {
            "章节": "1 海洋法.pdf",
            "关键词或思考题": "【思考题】领海制度的核心是什么？",
            "解释或答案": "答：领海制度的核心是沿海国主权、无害通过权及其限制之间的平衡。",
            "来源文件": "1 海洋法.pdf",
            "源页": 1,
            "拼版页": 1,
            "备注": "AI根据课件思考题整理",
        },
    ]
    output = tmp_path / "课程重点.pdf"

    write_key_points_pdf_from_analysis(analysis_items, output)

    with fitz.open(output) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    assert "课程重点" in text
    assert "章节" in text
    assert "重点名词解释" in text
    assert "思考题" in text
    assert "关键词索引" in text
    assert "领海：1 海洋法.pdf" in text
    assert "领海制度的核心是什么" in text
    assert "沿海国主权" in text
    assert "出处" not in text
    assert "源页" not in text
    typst_source = output.with_suffix(".typ")
    assert typst_source.exists()
    source_text = typst_source.read_text(encoding="utf-8")
    assert "重点名词解释" in source_text
    assert "领海制度的核心是什么" in source_text


def test_write_key_points_pdf_renders_latex_style_math(tmp_path):
    analysis_items = [
        {
            "章节": "公式章",
            "关键词或思考题": "【重点名词解释】质能方程",
            "解释或答案": "质能关系可写为 $E = mc^2$，积分形式可写为 $$\\int_a^b f(x) dx$$。",
        }
    ]
    output = tmp_path / "课程重点.pdf"

    write_key_points_pdf_from_analysis(analysis_items, output)

    assert output.exists()
    typst_source = output.with_suffix(".typ")
    source_text = typst_source.read_text(encoding="utf-8")
    assert "$E = m c^2$" in source_text
    assert "$integral_a^b f(x) dif x$" in source_text
    assert '"$E = mc^2$' not in source_text


def test_write_catalog_pdf_from_analysis_uses_ai_curated_subtitles(tmp_path):
    analysis_catalog = [
        {"章节": "第五章 基线、内水、领海与毗连区", "小节": "基线制度", "拼版页": 7},
        {"章节": "第五章 基线、内水、领海与毗连区", "小节": "内水、领海与毗连区", "拼版页": 8},
        {"章节": "第六章 公海", "小节": "公海自由及其限制", "拼版页": 22},
    ]
    output = tmp_path / "目录.pdf"

    write_catalog_pdf_from_analysis(analysis_catalog, output)

    with fitz.open(output) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    assert "第五章 基线、内水、领海与毗连区（第 7-8 页）" in text
    assert "基线制度：第 7 页" in text
    assert "内水、领海与毗连区：第 8 页" in text
    assert "另有" not in text
    assert "详见 _support" not in text


def test_chapter_ranges_from_analysis_catalog_are_exact():
    analysis_catalog = [
        {"章节": "第四章 海洋法的基本原则", "小节": "原则概览", "拼版页": 6},
        {"章节": "第四章 海洋法的基本原则", "小节": "公平利用", "拼版页": 7},
        {"章节": "第二十一章 战时海洋法概述", "小节": "战争法与海战法", "拼版页": 47},
        {"章节": "第二十一章 战时海洋法概述", "小节": "海战法渊源", "拼版页": 48},
    ]

    ranges = chapter_ranges_from_analysis_catalog(analysis_catalog)

    assert ranges == {
        "第四章 海洋法的基本原则": "第 6-7 页",
        "第二十一章 战时海洋法概述": "第 47-48 页",
    }


def test_catalog_entries_from_analysis_ignores_incomplete_rows():
    entries = catalog_entries_from_analysis(
        {
            "目录": [
                {"章节": "第一章", "小节": "海洋法概述", "拼版页": 1},
                {"章节": "第一章", "小节": "", "拼版页": 2},
                {"章节": "", "小节": "无章节", "拼版页": 3},
            ]
        }
    )

    assert entries == [{"章节": "第一章", "小节": "海洋法概述", "拼版页": 1}]


def test_write_analysis_input_json_includes_exam_brief(tmp_path):
    entries = [PageMapEntry("1 海洋法.pdf", 1, 1, 1, 1, "绪论")]
    output = tmp_path / "AI分析输入.json"

    write_analysis_input_json(
        entries,
        output,
        exam_brief="老师提示：重点考名词解释和比较题，只考第一到第三章。",
    )

    text = output.read_text(encoding="utf-8")
    assert "老师提示：重点考名词解释和比较题，只考第一到第三章。" in text
    assert "考试要求" in text
