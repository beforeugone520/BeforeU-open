from pathlib import Path
import re
import shutil
import subprocess

Line = tuple[str, str]


def write_typst_pdf(lines: list[Line], output_pdf: Path, source_typ: Path | None = None) -> None:
    source_typ = source_typ or output_pdf.with_suffix(".typ")
    source_typ.parent.mkdir(parents=True, exist_ok=True)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    source_typ.write_text(_build_typst_document(lines), encoding="utf-8")
    _compile_typst(source_typ, output_pdf)


def _compile_typst(source_typ: Path, output_pdf: Path) -> None:
    typst = shutil.which("typst")
    if not typst:
        raise RuntimeError("typst not found; install Typst or make it available on PATH")
    result = subprocess.run(
        [typst, "compile", str(source_typ), str(output_pdf)],
        cwd=source_typ.parent,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"typst compile failed for {source_typ}: {detail}")


def _build_typst_document(lines: list[Line]) -> str:
    body = "\n".join(_line_call(text, kind) for text, kind in lines)
    return f"""#set page(\"a4\", margin: (x: 0.85cm, y: 0.9cm))
#set text(size: 8pt, lang: \"zh\")
#set par(justify: false, leading: 0.42em)

#let title(s) = [
  #text(size: 15pt, weight: \"bold\", fill: rgb(\"#17324d\"))[#s]
  #v(7pt)
]
#let chapter(s) = [
  #block(width: 100%, fill: rgb(\"#e6f0f7\"), inset: 3.5pt)[#text(size: 9.2pt, weight: \"bold\", fill: rgb(\"#17324d\"))[#s]]
  #v(3pt)
]
#let section(s) = [
  #text(size: 8.5pt, weight: \"bold\", fill: rgb(\"#1f5f3b\"))[#s]
  #v(2pt)
]
#let body(s) = [
  #text(size: 7.5pt)[#s]
  #v(1.8pt)
]
#let muted(s) = [
  #text(size: 7.1pt, fill: rgb(\"#5f6368\"))[#s]
  #v(1.8pt)
]
#let blank() = v(4pt)

#columns(2, gutter: 0.55cm)[
{body}
]
"""


def _line_call(text: str, kind: str) -> str:
    if kind == "blank":
        return "#blank()"
    function_name = {
        "title": "title",
        "chapter": "chapter",
        "section": "section",
        "body": "body",
        "muted": "muted",
    }.get(kind, "body")
    return f"#{function_name}([{_typst_content(text)}])"


def _typst_content(value: str) -> str:
    parts: list[str] = []
    cursor = 0
    for start, end, formula in _latex_formula_spans(value):
        if start > cursor:
            parts.append(_typst_text(value[cursor:start]))
        parts.append(f"${_latex_formula_to_typst_math(formula)}$")
        cursor = end
    if cursor < len(value):
        parts.append(_typst_text(value[cursor:]))
    return " ".join(part for part in parts if part)


def _latex_formula_spans(value: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    index = 0
    while index < len(value):
        start = value.find("$", index)
        if start == -1:
            break
        delimiter = "$$" if value.startswith("$$", start) else "$"
        formula_start = start + len(delimiter)
        end = value.find(delimiter, formula_start)
        if end == -1:
            break
        formula = value[formula_start:end].strip()
        if formula:
            spans.append((start, end + len(delimiter), formula))
        index = end + len(delimiter)
    return spans


def _typst_text(value: str) -> str:
    if not value:
        return ""
    return f'#text("{_escape_typst_string(value)}")'


def _latex_formula_to_typst_math(value: str) -> str:
    formula = value.strip()
    replacements = {
        r"\int": "integral",
        r"\sum": "sum",
        r"\prod": "product",
        r"\infty": "infinity",
        r"\leq": "<=",
        r"\geq": ">=",
        r"\neq": "!=",
        r"\times": "times",
        r"\cdot": "dot",
        r"\alpha": "alpha",
        r"\beta": "beta",
        r"\gamma": "gamma",
        r"\Delta": "Delta",
        r"\delta": "delta",
        r"\theta": "theta",
        r"\lambda": "lambda",
        r"\mu": "mu",
        r"\pi": "pi",
        r"\sigma": "sigma",
    }
    for latex, typst in replacements.items():
        formula = formula.replace(latex, typst)
    formula = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1) / (\2)", formula)
    formula = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", formula)
    formula = re.sub(r"\bd([A-Za-z])\b", r"dif \1", formula)
    formula = _space_implicit_letter_products(formula)
    return formula.replace("\\", "")


def _space_implicit_letter_products(value: str) -> str:
    functions = {
        "sin",
        "cos",
        "tan",
        "log",
        "ln",
        "max",
        "min",
        "lim",
        "sqrt",
        "dif",
        "sum",
        "integral",
        "product",
        "infinity",
    }

    def replace_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if token in functions or len(token) <= 1:
            return token
        return " ".join(token)

    return re.sub(r"\b[A-Za-z]{2,}\b", replace_token, value)


def _escape_typst_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
