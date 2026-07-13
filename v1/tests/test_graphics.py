from pathlib import Path

from PIL import Image

from wikiepwing.epwing import graphics


def test_materializes_only_successful_graphics(tmp_path: Path, monkeypatch: object) -> None:
    source = tmp_path / "records.tsv"
    source.write_text(
        "Emacs\tImages:\\n- @@IMAGE:RW1hY3NJY29uLnN2Zw:@@ EmacsIcon.svg\\n"
        "Missing\tImages:\\n- @@IMAGE:TWlzc2luZy5wbmc:@@ Missing.png\\n",
        encoding="utf-8",
    )
    sample = tmp_path / "sample.png"
    Image.new("RGB", (8, 8), "red").save(sample)

    def fake_fetch(file_name: str) -> bytes:
        if file_name == "Missing.png":
            raise ValueError("missing")
        return sample.read_bytes()

    monkeypatch.setattr(graphics, "_fetch_image", fake_fetch)

    result = graphics.materialize_graphics(source, tmp_path / "graphics", 10)

    rewritten = source.read_text(encoding="utf-8")
    assert result.resolved == 1
    assert result.failed == 1
    assert "@@CGRAPH:img-" in rewritten
    assert "[image] Missing.png" in rewritten
    assert (tmp_path / "graphics" / "cgraphs.txt").read_text(encoding="utf-8").count(".bmp") == 1


def test_forced_graphics_are_resolved(tmp_path: Path, monkeypatch: object) -> None:
    source = tmp_path / "records.tsv"
    source.write_text("Emacs\t@@IMAGE:RW1hY3NJY29uLnN2Zw:@@ EmacsIcon.svg\n", encoding="utf-8")
    sample = tmp_path / "sample.png"
    Image.new("RGB", (8, 8), "blue").save(sample)

    monkeypatch.setattr(graphics, "_fetch_image", lambda _file_name: sample.read_bytes())

    result = graphics.materialize_graphics(source, tmp_path / "graphics", 0, ("EmacsIcon.svg",))

    assert result.resolved == 1
    assert "@@CGRAPH:img-" in source.read_text(encoding="utf-8")
