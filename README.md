# BeforeU-open

![BeforeU-open 导入 meme](assets/beforeu-open-import-meme.png)

> 场景直觉：开卷考试不是资料越多越好，而是要把“找知识点”的成本提前降下来。

`BeforeU-open` 是一个用于开卷考试的 Codex skill。它可以把课程 PDF、PPT、PPTX 整理成紧凑、可打印、便于考场快速查找的资料包。

机器调用名遵循 Codex skill 规范，使用小写形式：

```text
$beforeu-open
```

## 功能

- 生成带可见 `第 X 页` 页码的 `开卷考打印版.pdf`
- 第一阶段生成按打印页码定位的 `目录.pdf`
- 第二阶段根据 AI 分析结果生成 `课程重点.pdf`
- 默认把 `目录` 合并到 `课程重点.pdf` 开头，再生成 `关键词索引`
- 按章节整理 `重点名词解释` 和 `思考题`
- 支持 `--exam-brief`，让考试范围、题型、老师提示进入 AI 分析输入
- 支持 LaTeX 风格公式输入：`$...$` 和 `$$...$$`

## 输出结构

```text
开卷考输出-<timestamp>/
  开卷考打印版.pdf
  目录.pdf            # 第一阶段生成；第二阶段默认从根目录移除
  课程重点.pdf        # 提供 AI分析结果.json 后生成，默认包含目录
  _support/
    AI分析输入.json
    AI分析结果模板.json
    AI分析结果.json
    页码映射.csv
    运行报告.md
    markdown/
    typst/
    converted-pdf/
```

根输出目录只放最终 PDF 和 `_support/`。JSON、CSV、Markdown、Typst 源文件、转换中间文件和报告都放在 `_support/`。

## 工具链

- `PyMuPDF`：拼装 `开卷考打印版.pdf`，写入可见页码标签。
- `Typst`：渲染学生可读的第一阶段 `目录.pdf` 和第二阶段 `课程重点.pdf`。
- `LibreOffice`：把 PPT/PPTX 转换为 PDF。
- `officecli`：可选，用于增强 PPTX 文本和结构提取。
- 公式：输入可用 LaTeX 风格，最终由 Typst 渲染，不需要 TeX Live 或 XeLaTeX。

## 安装为 Codex Skill

将目录放到 Codex skills 目录下，目录名建议为 `beforeu-open`：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /path/to/beforeu-open "${CODEX_HOME:-$HOME/.codex}/skills/beforeu-open"
```

使用时：

```text
$beforeu-open 帮我把 /path/to/course-materials 整理成开卷考试打印资料包
```

## 本地依赖

```bash
python3 -m pip install -r requirements.txt
python3 scripts/check_dependencies.py
```

如需尝试自动安装缺失依赖：

```bash
python3 scripts/install_dependencies.py
```

`LibreOffice` 和 `Typst` 可能仍需要根据系统环境手动安装。

## 使用流程

执行前先确认合并规格，必须三选一：

- `4x4`：每页 16 格，字号相对大，适合内容密、截图多的课件。
- `5x4`：每页 20 格，平衡清晰度和压缩率。
- `5x5`：每页 25 格，最省页数，但单格内容更小。

第一阶段：生成打印版、原始目录、页码映射和 AI 输入。

```bash
python3 scripts/open_book_exam.py /path/to/course-materials \
  --grid 4x4 \
  --install-missing \
  --exam-brief "考试范围、题型、老师提示"
```

第一阶段会生成：

- `开卷考打印版.pdf`
- `目录.pdf`
- `_support/页码映射.csv`
- `_support/AI分析输入.json`
- `_support/AI分析结果模板.json`

第二阶段：Codex 根据 `_support/AI分析输入.json` 写出 `AI分析结果.json` 后，默认把 AI 整理后的目录并入 `课程重点.pdf`。

```bash
python3 scripts/open_book_exam.py /path/to/course-materials \
  --grid 4x4 \
  --analysis-json /path/to/AI分析结果.json
```

如果 `--analysis-json` 没有同时指定 `--output-dir`，脚本会复用该输入路径下最新的 `开卷考输出-*` 目录。
脚本不会静默使用默认规格；未提供 `--grid` 时会提示先选择 `4x4`、`5x4` 或 `5x5`。

## AI 分析结果格式

`课程重点.pdf` 必须来自 AI 编写的 `AI分析结果.json`，不能只依赖脚本启发式规则。

```json
{
  "课程名称": "课程名",
  "目录": [
    {
      "章节": "章节名",
      "小节": "适合查找的小标题",
      "拼版页": 6
    }
  ],
  "重点": [
    {
      "章节": "章节名",
      "关键词或思考题": "【重点名词解释】关键词",
      "解释或答案": "简明解释，可包含公式，例如 $E = mc^2$。"
    },
    {
      "章节": "章节名",
      "关键词或思考题": "【思考题】问题？",
      "解释或答案": "答：直接答案。"
    }
  ]
}
```

## 输出规范

- `开卷考打印版.pdf` 是页码权威。
- 第一阶段 `目录.pdf` 使用打印 PDF 页码范围，例如 `第 1-3 页`。
- 第二阶段默认不在根目录保留单独 `目录.pdf`；目录作为 `课程重点.pdf` 的第一部分。
- `课程重点.pdf` 先列 `目录`，再列 `关键词索引`，最后按章节分组。
- 思考题答案必须以 `答：` 开头。
- 学生可见 PDF 不应突出源文件、源页、格子位置、置信度说明等原始元数据。

## 测试

```bash
python3 -m pip install -r requirements-dev.txt
pytest -p no:cacheprovider
```

## 许可证

MIT
