# Project Memory

## BeforeU-open Skill

- This repository is a reusable Codex skill with display name `BeforeU-open`.
- The Codex machine invocation name is `beforeu-open`, because skill names must be lowercase hyphen-case.
- Publish or install the folder under `beforeu-open`.
- The core workflow is not a full LaTeX toolchain. It is `PyMuPDF + Typst + AI JSON`.
- `PyMuPDF` assembles `开卷考打印版.pdf` and writes visible `第 X 页` labels.
- `Typst` renders the first-stage `目录.pdf` and the second-stage `课程重点.pdf`. Editable `.typ` files stay under `_support/typst/`.
- `课程重点.pdf` supports LaTeX-style formula markers in `解释或答案`: `$...$` and `$$...$$`. The renderer converts supported formulas to Typst math, so TeX Live/XeLaTeX is not required.
- `LibreOffice` is only for PPT/PPTX to PDF conversion. If LibreOffice is missing, PDF inputs can still work but PPT/PPTX conversion will fail.
- Before generation, ask the user to choose the merge grid: `4x4`, `5x4`, or `5x5`. The CLI requires explicit `--grid` and must not silently default.
- The first stage creates the print pack, raw catalog, page map, `_support/AI分析输入.json`, and `AI分析结果模板.json`.
- Codex writes `AI分析结果.json` from `AI分析输入.json`, `SKILL.md`, and `考试要求`.
- The second stage uses `--analysis-json AI分析结果.json` to merge the AI-curated directory into `课程重点.pdf` by default; root `目录.pdf` is a first-stage draft unless `--catalog-mode separate` is explicitly used.
- Keep root output folders clean: final PDFs plus `_support/` only; JSON, CSV, Markdown, Typst sources, converted PDFs, and reports belong under `_support/`.

## Validation

```bash
python3 scripts/check_dependencies.py
pytest -p no:cacheprovider
```
