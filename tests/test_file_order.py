from file_order import discover_sources, natural_sort_key


def test_natural_sort_key_orders_chinese_chapter_filenames():
    names = [
        "13 海洋法 海洋环境保护.pdf",
        "2 海洋法.pdf",
        "1 海洋法.pdf",
        "21-22章战时海洋法 2024(1).pdf",
    ]

    ordered = sorted(names, key=natural_sort_key)

    assert ordered == [
        "1 海洋法.pdf",
        "2 海洋法.pdf",
        "13 海洋法 海洋环境保护.pdf",
        "21-22章战时海洋法 2024(1).pdf",
    ]


def test_discover_sources_excludes_subfolders_by_default(tmp_path):
    (tmp_path / "1 海洋法.pdf").write_bytes(b"%PDF-1.4\n")
    (tmp_path / "2 海洋法.pptx").write_bytes(b"pptx")
    merged = tmp_path / "合并"
    merged.mkdir()
    (merged / "海洋法PDF合并.pdf").write_bytes(b"%PDF-1.4\n")

    sources = discover_sources(tmp_path, include_subdirs=False)

    assert [s.path.name for s in sources] == ["1 海洋法.pdf", "2 海洋法.pptx"]


def test_discover_sources_can_include_subfolders(tmp_path):
    (tmp_path / "1 海洋法.pdf").write_bytes(b"%PDF-1.4\n")
    merged = tmp_path / "合并"
    merged.mkdir()
    (merged / "海洋法PDF合并.pdf").write_bytes(b"%PDF-1.4\n")

    sources = discover_sources(tmp_path, include_subdirs=True)

    assert [s.path.name for s in sources] == ["1 海洋法.pdf", "海洋法PDF合并.pdf"]
