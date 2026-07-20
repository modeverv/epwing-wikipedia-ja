import zipfile
from pathlib import Path

from tests.test_doctor import _write_config
from wikiepwing.cli import main


def test_doctor_json_output(tmp_path: Path, capsys: object) -> None:
    config_path = tmp_path / "config.toml"
    _write_config(config_path)

    assert main(["doctor", "--config", str(config_path), "--json"]) == 0
    assert '"ok": true' in capsys.readouterr().out  # type: ignore[attr-defined]


def test_inspect_returns_success_for_valid_package(tmp_path: Path) -> None:
    archive = tmp_path / "dictionary.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("CATALOGS", b"")
        output.writestr("TOOLCHAIN.json", b"{}")
        output.writestr("WIKIEP/DATA/HONMON.ebz", b"")

    assert main(["inspect", str(archive)]) == 0
