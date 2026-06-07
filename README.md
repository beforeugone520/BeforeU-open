# BeforeU-open

![License: MIT](https://img.shields.io/badge/license-MIT-111111.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-0B5FFF.svg)

把课程 PDF、PPT、PPTX 整理成适合开卷考试使用的打印资料包：压缩课件、标清页码、生成目录，再用 AI 整理课程重点和关键词索引。

![BeforeU-open 导入 meme](assets/beforeu-open-import-meme.png)

> 开卷考试不是资料越多越好，而是要把“找知识点”的成本提前降下来。

## 适合场景

- 考试允许带纸质资料，但课件太多、页数太散。
- PPT/PDF 里有大量定义、图表、公式、案例，临场翻找很慢。
- 需要把课程资料整理成“打印版 + 目录 + 课程重点”的组合。
- 希望保留页码定位，让目录和重点能直接指向打印资料。

## 核心输出

| 文件 | 用途 |
| --- | --- |
| `开卷考打印版.pdf` | 把课程材料拼成紧凑打印版，并写入可见 `第 X 页` 页码。 |
| `目录.pdf` | 第一阶段生成的页码目录，用于快速定位打印页。 |
| `课程重点.pdf` | 第二阶段生成的复习索引，默认把目录合并在开头。 |
| `_support/` | 保存 AI 输入、AI 结果模板、页码映射、Typst/Markdown 中间文件和运行报告。 |

第二阶段默认只在根目录保留 `开卷考打印版.pdf`、`课程重点.pdf` 和 `_support/`，避免考前资料夹变乱。

## 安装

将本目录复制到 Codex skills 目录，目录名建议保持为 `beforeu-open`：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /path/to/beforeu-open "${CODEX_HOME:-$HOME/.codex}/skills/beforeu-open"
```

调用名：

```text
$beforeu-open
```

示例：

```text
$beforeu-open 帮我把 /path/to/course-materials 整理成开卷考试打印资料包
```

## 依赖

```bash
python3 -m pip install -r requirements.txt
python3 scripts/check_dependencies.py
```

如需尝试自动安装缺失依赖：

```bash
python3 scripts/install_dependencies.py
```

工具链说明：

| 工具 | 作用 |
| --- | --- |
| `PyMuPDF` | 拼装打印版 PDF，并写入可见页码。 |
| `LibreOffice` | 将 PPT/PPTX 转换为 PDF。 |
| `Typst` | 渲染 `目录.pdf` 和 `课程重点.pdf`。 |
| `officecli` | 可选，用于增强 PPTX 文本和结构提取。 |

公式输入支持 LaTeX 风格的 `$...$` 和 `$$...$$`，最终由 Typst 渲染，不需要 TeX Live 或 XeLaTeX。

## 快速开始

执行前必须先选合并规格，脚本不会静默使用默认值。

| 规格 | 每页格数 | 适合情况 |
| --- | ---: | --- |
| `4x4` | 16 | 字号相对大，适合内容密、截图多的课件。 |
| `5x4` | 20 | 清晰度和压缩率比较均衡。 |
| `5x5` | 25 | 最省页数，但单格内容更小。 |

### 第一阶段：生成打印资料和 AI 输入

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

### 第二阶段：生成课程重点

Codex 根据 `_support/AI分析输入.json` 写出 `AI分析结果.json` 后，再运行：

```bash
python3 scripts/open_book_exam.py /path/to/course-materials \
  --grid 4x4 \
  --analysis-json /path/to/AI分析结果.json
```

如果 `--analysis-json` 没有同时指定 `--output-dir`，脚本会复用该输入路径下最新的 `开卷考输出-*` 目录。

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
