import zipfile
from pathlib import Path

from wikiepwing.epwing.verify import inspect_archive


def test_inspects_minimum_epwing_package(tmp_path: Path) -> None:
    archive = tmp_path / "dictionary.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("CATALOGS", b"catalog")
        output.writestr("TOOLCHAIN.json", b"{}")
        output.writestr("WIKIEP/DATA/HONMON.ebz", b"compressed")

    assert inspect_archive(archive).ok


def test_reports_missing_structure(tmp_path: Path) -> None:
    archive = tmp_path / "dictionary.zip"
    with zipfile.ZipFile(archive, "w"):
        pass

    assert inspect_archive(archive).errors == (
        "CATALOG_MISSING",
        "TOOLCHAIN_MANIFEST_MISSING",
        "COMPRESSED_HONMON_MISSING",
    )
