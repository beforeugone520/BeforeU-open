from dataclasses import dataclass
import importlib.util
import platform
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    available: bool
    required: bool
    detail: str


def check_dependencies() -> list[DependencyStatus]:
    fitz_available = importlib.util.find_spec("fitz") is not None
    libreoffice_path = shutil.which("soffice") or shutil.which("libreoffice")
    typst_path = shutil.which("typst")
    officecli_path = shutil.which("officecli")
    return [
        DependencyStatus("PyMuPDF", fitz_available, True, "Python package fitz"),
        DependencyStatus(
            "LibreOffice",
            libreoffice_path is not None,
            True,
            libreoffice_path or "soffice/libreoffice not found",
        ),
        DependencyStatus(
            "Typst",
            typst_path is not None,
            True,
            typst_path or "typst not found",
        ),
        DependencyStatus(
            "officecli",
            officecli_path is not None,
            False,
            officecli_path or "optional officecli not found",
        ),
    ]


def manual_install_command(name: str, platform_name: str | None = None) -> str:
    current = (platform_name or platform.system()).lower()
    if name == "PyMuPDF":
        return f"{sys.executable} -m pip install PyMuPDF"
    if name == "LibreOffice":
        if "linux" in current:
            return "sudo apt-get update && sudo apt-get install -y libreoffice"
        if "darwin" in current:
            return "brew install --cask libreoffice"
        return "Install LibreOffice from https://www.libreoffice.org/download/download-libreoffice/"
    if name == "Typst":
        if "linux" in current:
            return "Install Typst from https://github.com/typst/typst/releases or run: cargo install typst-cli"
        if "darwin" in current:
            return "brew install typst"
        return "Install Typst from https://github.com/typst/typst/releases"
    if name == "officecli":
        if "windows" in current:
            return "irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex"
        return "curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash"
    raise ValueError(f"Unknown dependency: {name}")


def install_missing(auto_install: bool = True) -> list[str]:
    messages: list[str] = []
    for status in check_dependencies():
        if status.available:
            messages.append(f"OK: {status.name}")
            continue
        command = manual_install_command(status.name)
        if not auto_install:
            messages.append(f"MISSING: {status.name}; install with: {command}")
            continue
        if status.name == "PyMuPDF":
            subprocess.run([sys.executable, "-m", "pip", "install", "PyMuPDF"], check=False)
            messages.append(f"INSTALL_ATTEMPTED: {status.name}")
        else:
            messages.append(f"MISSING: {status.name}; install with: {command}")
    return messages
