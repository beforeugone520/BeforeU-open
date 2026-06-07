import dependency_utils


def test_check_dependencies_reports_missing_tools(monkeypatch):
    monkeypatch.setattr(dependency_utils.shutil, "which", lambda name: None)
    monkeypatch.setattr(dependency_utils.importlib.util, "find_spec", lambda name: None)

    statuses = dependency_utils.check_dependencies()

    by_name = {status.name: status for status in statuses}
    assert not by_name["PyMuPDF"].available
    assert not by_name["LibreOffice"].available
    assert not by_name["Typst"].available
    assert by_name["Typst"].required
    assert not by_name["officecli"].available


def test_install_command_for_linux_libreoffice():
    command = dependency_utils.manual_install_command("LibreOffice", platform_name="linux")

    assert "apt-get install -y libreoffice" in command


def test_install_command_for_linux_typst():
    command = dependency_utils.manual_install_command("Typst", platform_name="linux")

    assert "typst" in command


def test_missing_officecli_is_optional(monkeypatch):
    monkeypatch.setattr(dependency_utils.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        dependency_utils.importlib.util,
        "find_spec",
        lambda name: object() if name == "fitz" else None,
    )

    statuses = dependency_utils.check_dependencies()
    officecli = [status for status in statuses if status.name == "officecli"][0]

    assert officecli.required is False
