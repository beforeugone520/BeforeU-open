from pathlib import Path
from datetime import datetime
import json

import fitz

import open_book_exam
from open_book_exam import main


def _make_pdf(path: Path, title: str) -> None:
    doc = fitz.open()
    page = doc.new_page(width=200, height=120)
    page.insert_text((24, 48), title)
    doc.save(path)
    doc.close()


def test_cli_requires_grid_before_generating_outputs(tmp_path, capsys):
    source_dir = tmp_path / "海洋法"
    source_dir.mkdir()
    _make_pdf(source_dir / "1 海洋法.pdf", "绪论")

    exit_code = main([str(source_dir)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "请先指定合并规格" in captured.err
    assert "--grid 4x4" in captured.err
    assert "--grid 5x4" in captured.err
    assert "--grid 5x5" in captured.err
    assert list(source_dir.glob("开卷考输出-*")) == []


def test_cli_generates_core_outputs(tmp_path):
    source_dir = tmp_path / "海洋法"
    source_dir.mkdir()
    _make_pdf(source_dir / "1 海洋法.pdf", "绪论")
    merged = source_dir / "合并"
    merged.mkdir()
    _make_pdf(merged / "海洋法PDF合并.pdf", "previous output")
    exam_brief = "老师提示：重点考名词解释和比较题，只考第一到第三章。"

    exit_code = main([str(source_dir), "--grid", "4x4", "--exam-brief", exam_brief])

    assert exit_code == 0
    run_dirs = list(source_dir.glob("开卷考输出-*"))
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    support_dir = run_dir / "_support"
    assert (run_dir / "开卷考打印版.pdf").exists()
    assert (run_dir / "目录.pdf").exists()
    assert support_dir.exists()
    assert (support_dir / "AI分析输入.json").exists()
    analysis_input = json.loads((support_dir / "AI分析输入.json").read_text(encoding="utf-8"))
    assert analysis_input["考试要求"] == exam_brief
    assert (support_dir / "AI分析结果模板.json").exists()
    assert not (run_dir / "课程重点.pdf").exists()
    assert (support_dir / "页码映射.csv").exists()
    assert (support_dir / "运行报告.md").exists()
    assert (support_dir / "markdown" / "目录.md").exists()
    assert (support_dir / "typst" / "目录.typ").exists()
    assert not (run_dir / "AI分析输入.json").exists()
    assert not (run_dir / "AI分析结果模板.json").exists()
    assert not (run_dir / "页码映射.csv").exists()
    assert not (run_dir / "运行报告.md").exists()
    assert not (run_dir / "目录.md").exists()
    assert "合并" not in (support_dir / "页码映射.csv").read_text(encoding="utf-8-sig")
    assert not (run_dir / "print-pack.pdf").exists()
    assert not (run_dir / "lookup-index.csv").exists()


def test_cli_renders_key_points_pdf_from_ai_analysis_json(tmp_path):
    source_dir = tmp_path / "海洋法"
    source_dir.mkdir()
    _make_pdf(source_dir / "1 海洋法.pdf", "思考题：领海制度的核心是什么？")
    analysis_json = tmp_path / "AI分析结果.json"
    analysis_json.write_text(
        json.dumps(
            {
                "课程名称": "海洋法",
                "目录": [
                    {
                        "章节": "1 海洋法.pdf",
                        "小节": "领海制度核心",
                        "拼版页": 1,
                    }
                ],
                "重点": [
                    {
                        "章节": "1 海洋法.pdf",
                        "关键词或思考题": "领海制度的核心是什么？",
                        "解释或答案": "领海制度的核心是沿海国主权、无害通过权及其限制之间的平衡。",
                        "来源文件": "1 海洋法.pdf",
                        "源页": 1,
                        "拼版页": 1,
                        "备注": "AI根据课件思考题整理",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    exit_code = main([str(source_dir), "--grid", "4x4", "--analysis-json", str(analysis_json)])

    assert exit_code == 0
    run_dir = list(source_dir.glob("开卷考输出-*"))[0]
    assert (run_dir / "课程重点.pdf").exists()
    assert not (run_dir / "目录.pdf").exists()
    assert not (run_dir / "开卷速查.pdf").exists()
    assert (run_dir / "_support" / "运行报告.md").exists()
    assert (run_dir / "_support" / "AI分析结果.json").exists()
    assert (run_dir / "_support" / "typst" / "目录.typ").exists()
    assert (run_dir / "_support" / "typst" / "课程重点.typ").exists()
    assert not (run_dir / "_support" / "typst" / "开卷速查.typ").exists()
    with fitz.open(run_dir / "课程重点.pdf") as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    assert "领海制度的核心是什么" in text
    assert "沿海国主权" in text
    assert "章节：1 海洋法.pdf（第 1 页）" in text
    assert "目录" in text
    assert "领海制度核心：第 1 页" in text


def test_cli_reuses_latest_output_dir_when_rendering_ai_analysis(tmp_path, monkeypatch):
    source_dir = tmp_path / "海洋法"
    source_dir.mkdir()
    _make_pdf(source_dir / "1 海洋法.pdf", "思考题：领海制度的核心是什么？")

    class FakeDatetime:
        calls = 0

        @classmethod
        def now(cls):
            values = [
                datetime(2026, 6, 5, 22, 0, 0),
                datetime(2026, 6, 5, 22, 3, 0),
            ]
            value = values[min(cls.calls, len(values) - 1)]
            cls.calls += 1
            return value

    monkeypatch.setattr(open_book_exam, "datetime", FakeDatetime)

    first_exit_code = main([str(source_dir), "--grid", "4x4"])
    first_run_dirs = list(source_dir.glob("开卷考输出-*"))
    assert first_exit_code == 0
    assert len(first_run_dirs) == 1
    first_run_dir = first_run_dirs[0]

    analysis_json = tmp_path / "AI分析结果.json"
    analysis_json.write_text(
        json.dumps(
            {
                "课程名称": "海洋法",
                "重点": [
                    {
                        "章节": "1 海洋法.pdf",
                        "关键词或思考题": "【思考题】领海制度的核心是什么？",
                        "解释或答案": "答：领海制度的核心是沿海国主权、无害通过权及其限制之间的平衡。",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    second_exit_code = main([str(source_dir), "--grid", "4x4", "--analysis-json", str(analysis_json)])

    assert second_exit_code == 0
    run_dirs = list(source_dir.glob("开卷考输出-*"))
    assert run_dirs == [first_run_dir]
    assert (first_run_dir / "课程重点.pdf").exists()
    assert not (first_run_dir / "目录.pdf").exists()
    assert not (first_run_dir / "开卷速查.pdf").exists()
    assert (first_run_dir / "_support" / "AI分析结果.json").exists()


def test_cli_separate_catalog_mode_keeps_ai_curated_catalog_pdf(tmp_path):
    source_dir = tmp_path / "海洋法"
    source_dir.mkdir()
    _make_pdf(source_dir / "1 海洋法.pdf", "思考题：领海制度的核心是什么？")
    analysis_json = tmp_path / "AI分析结果.json"
    analysis_json.write_text(
        json.dumps(
            {
                "课程名称": "海洋法",
                "目录": [
                    {
                        "章节": "1 海洋法.pdf",
                        "小节": "领海制度核心",
                        "拼版页": 1,
                    }
                ],
                "重点": [
                    {
                        "章节": "1 海洋法.pdf",
                        "关键词或思考题": "【思考题】领海制度的核心是什么？",
                        "解释或答案": "答：领海制度的核心是沿海国主权、无害通过权及其限制之间的平衡。",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            str(source_dir),
            "--grid",
            "4x4",
            "--catalog-mode",
            "separate",
            "--analysis-json",
            str(analysis_json),
        ]
    )

    assert exit_code == 0
    run_dir = list(source_dir.glob("开卷考输出-*"))[0]
    assert (run_dir / "目录.pdf").exists()
    assert (run_dir / "课程重点.pdf").exists()
    with fitz.open(run_dir / "目录.pdf") as doc:
        catalog_text = "\n".join(page.get_text("text") for page in doc)
    assert "领海制度核心：第 1 页" in catalog_text
