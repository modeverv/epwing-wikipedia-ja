from pathlib import Path

from wikiepwing.epwing.gaiji import MAX_GAIJI, gaiji_name, materialize_gaiji, needs_gaiji


def test_detects_only_euc_jp_unsupported_characters() -> None:
    assert not needs_gaiji("日")
    assert needs_gaiji("𠮟")
    assert gaiji_name("𠮟") == "u-20b9f"


def test_gaiji_name_is_ascii_and_stable() -> None:
    assert gaiji_name("𩸽") == "u-29e3d"
    assert gaiji_name("𩸽").isascii()


def test_gaiji_overflow_preserves_unicode_identity_as_text(tmp_path: Path) -> None:
    records = tmp_path / "records.tsv"
    characters = [chr(0x20000 + index) for index in range(MAX_GAIJI + 1)]
    records.write_text("項目\t" + "".join(characters) + "\n", encoding="utf-8")

    result = materialize_gaiji(records, tmp_path / "gaiji")

    assert len(result.names) == MAX_GAIJI
    assert len(result.overflow_names) == 1
    assert result.overflow_replacements == 1
    assert "[U+22000]" in records.read_text(encoding="utf-8")
    assert "BODY\tu-22000\tU+22000\t1" in (tmp_path / "gaiji-overflow.txt").read_text(
        encoding="ascii"
    )


def test_unsupported_title_character_is_not_replaced_with_question_mark(tmp_path: Path) -> None:
    records = tmp_path / "records.tsv"
    records.write_text("𠮟る\t本文\n", encoding="utf-8")

    result = materialize_gaiji(records, tmp_path / "gaiji")

    assert records.read_text(encoding="utf-8").startswith("[U+20B9F]る\t")
    assert result.title_replacements == 1
