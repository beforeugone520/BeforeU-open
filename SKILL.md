---
name: beforeu-open
description: 将大学开卷考试资料整理成可打印资料包。用于从课程 PDF、PPT、PPTX 生成带可见页码的打印版、章节目录、关键词索引、名词解释、思考题答案、结合老师提示的重点整理，以及支持 LaTeX 风格公式的课程重点 PDF。
---

# BeforeU-open

Create printable open-book exam packs from course materials. Optimize for fast exam lookup, not textbook-style notes.

## Hard Rules

- Root output contains final PDFs only; all support files go under `_support/`.
- Before running the generation command, ask the user to choose the merge grid: `4x4`, `5x4`, or `5x5`.
- `开卷考打印版.pdf` is the page authority and must show visible `第 X 页` labels.
- First stage generates a standalone `目录.pdf`; after `AI分析结果.json` is supplied, the default final root output merges the directory into `课程重点.pdf`.
- Directory content uses print-PDF chapter page ranges, not source pages or grid cells.
- After `AI分析结果.json` is supplied, directory content inside `课程重点.pdf` must prefer the AI-curated `目录` array, not raw page titles.
- `课程重点.pdf` starts with the merged `目录` section, then a compact `关键词索引`, then groups chapter content into `重点名词解释` and `思考题`.
- Do not generate `开卷速查.pdf`; its content duplicates `课程重点.pdf`.
- Student-facing PDFs must use compact print layout: narrow margins, small readable Chinese text, dense rows or two columns.
- Student-facing PDFs must not foreground `来源文件`, `源页`, `拼版页`, `格子位置`, `备注`, or `出处`.
- Answers to thinking questions start with `答：`.
- Formula content in `解释或答案` may use LaTeX-style `$...$` or `$$...$$`; the renderer converts supported formulas to Typst math.
- If source text extraction is weak, report the limitation instead of inventing coverage.

## Output Contract

```text
开卷考输出-<timestamp>/
  开卷考打印版.pdf
  目录.pdf            # first stage only; removed from root by default after AI分析结果.json
  课程重点.pdf        # only when AI分析结果.json is supplied; includes 目录 by default
  _support/
    AI分析输入.json
    AI分析结果模板.json
    页码映射.csv
    运行报告.md
    markdown/
    typst/
    converted-pdf/
    screenshots/
    legacy/
```

Do not leave JSON, CSV, Markdown, screenshots, reports, or legacy PDFs in the root output folder.

## Commands

```bash
python3 scripts/check_dependencies.py
python3 scripts/install_dependencies.py
python3 scripts/open_book_exam.py INPUT_PATH --grid 4x4 --install-missing --exam-brief "考试范围、题型、老师提示"
python3 scripts/open_book_exam.py INPUT_PATH --grid 4x4 --analysis-json AI分析结果.json
```

Default layout: A4 landscape, root course folder only, natural filename order, and `combined-lookup` catalog mode. Grid has no silent default; the user must choose `--grid 4x4`, `--grid 5x4`, or `--grid 5x5` before generation. `开卷考打印版.pdf` is assembled with PyMuPDF. First-stage `目录.pdf` and final `课程重点.pdf` are rendered by Typst. `--exam-brief` is written into `_support/AI分析输入.json` as `考试要求` and must guide the AI重点. When `--analysis-json` is supplied without `--output-dir`, the command reuses the latest existing `开卷考输出-*` folder for that input if one exists.

## Student Intake

Before analysis, capture any available exam context:

- 考试范围：章节、课件、是否排除某些内容。
- 题型：名词解释、简答、论述、比较、案例。
- 老师提示：划重点、反复强调、课堂提问、复习课范围。
- 合并规格：`4x4`、`5x4`、`5x5` 三选一；未说明时先问，不要直接执行。
- 打印限制：黑白/彩色、单面/双面、是否限页、是否允许目录或自制材料。

If these details are absent, proceed with course-material analysis and say the重点 is based only on supplied files.

## When To Ask

Ask before proceeding only when:

- The user has not chosen a merge grid (`4x4`, `5x4`, or `5x5`).
- File order is ambiguous.
- Chapter titles conflict with filenames.
- The user requests a custom orientation but omits details.
- Syllabus, exam scope, question type, or teacher hints would materially change the重点.
- `_support/AI分析输入.json` is sparse because files are scanned or OCR failed.

## Workflow

1. Ask the user to choose `4x4`, `5x4`, or `5x5`, then run dependency check and main CLI with explicit `--grid`.
2. Inspect `_support/运行报告.md`, `_support/页码映射.csv`, and `_support/AI分析输入.json`.
3. Verify `开卷考打印版.pdf` has visible `第 X 页` labels.
4. First-stage `目录.pdf` is a raw draft. After AI analysis, put the directory at the front of `课程重点.pdf`, preferring AI-curated chapter subtitles: chapter name + `第 X-Y 页`, with a few useful small titles only.
5. Analyze course content by chapter, using `_support/AI分析输入.json` `考试要求` as higher-priority guidance when present.
6. Write `AI分析结果.json` when generating key points:

```json
{
  "课程名称": "课程名",
  "目录": [
    {
      "章节": "第五章 基线、内水、领海与毗连区",
      "小节": "基线制度",
      "拼版页": 6
    },
    {
      "章节": "第五章 基线、内水、领海与毗连区",
      "小节": "内水、领海与毗连区",
      "拼版页": 7
    }
  ],
  "重点": [
    {
      "章节": "第一章 海洋法概述",
      "关键词或思考题": "【重点名词解释】海洋法",
      "解释或答案": "海洋法是……"
    },
    {
      "章节": "第一章 海洋法概述",
      "关键词或思考题": "【思考题】海洋法的调整对象是什么？",
      "解释或答案": "答：……"
    }
  ]
}
```

7. Render `课程重点.pdf` with `--analysis-json`; by default it includes both `目录` and `课程重点`.
8. Verify outputs before replying.

## Writing Standard

- Use short Chinese headings and short sentences.
- Prefer bullets and compact tables over paragraphs.
- `关键词索引`: keyword/question + chapter + print page range only.
- 名词解释: what it is + key condition/effect + common exam distinction.
- 思考题: direct answer, no long derivation unless needed.
- Comparisons: use dimensions such as subject, scope, rights, limits, exceptions.
- Formulas: write concise LaTeX-style math such as `$E = mc^2$`, `$$\int_a^b f(x) dx$$`, `\frac{a}{b}`, or `\sqrt{x}`. Avoid long derivations.
- Do not copy long textbook passages.
- Do not include source metadata in student-facing text unless explicitly requested.

## Directory Standard

Good:

```text
第五章 基线、内水、领海与毗连区：第 6-10 页
  基线制度：第 6 页
  内水、港口、海湾和海峡：第 7-8 页
```

Bad:

```text
1 海洋法.pdf 源页 27 拼版页 5 格子 R1C5
```

## Verification

Pass only if all are true:

- Root contains only final PDFs and `_support/`.
- `_support/` contains JSON/CSV/Markdown/report/intermediate files.
- `_support/typst/` contains `目录.typ`; when AI analysis is supplied, it also contains `课程重点.typ`.
- `开卷考打印版.pdf` opens and has first/last visible `第 X 页` labels.
- First-stage `目录.pdf` opens, contains print-PDF page ranges such as `第 1-3 页`, and does not contain `源页`, `格子`, or `合并PDF`.
- After AI analysis in default mode, root `目录.pdf` is removed and `课程重点.pdf` contains `目录`, `关键词索引`, `重点名词解释`, and `思考题`, without `出处：` or `源页`.
- Formula answers render without literal `$...$` markers in the PDF; `_support/typst/课程重点.typ` contains Typst math.
- `开卷速查.pdf` and `_support/typst/开卷速查.typ` do not exist.
- If tests exist, run them.

## Stop And Fix

Stop before final response if:

- A claimed final file does not exist.
- Root output is cluttered with support files.
- Visible page labels are missing from the print PDF.
- Student-facing PDFs are sparse, single-column, or whitespace-heavy.
- Key points are only labels without explanations.
- Thinking questions lack answers.
- The user did not choose a merge grid before generation.
- `--exam-brief` was provided but `_support/AI分析输入.json` lacks `考试要求`.
- Extraction was weak but no limitation is reported.
