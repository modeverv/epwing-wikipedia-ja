from pathlib import Path

import pytest

from wikiepwing.config import ConfigurationError, load_config


def test_loads_default_configuration() -> None:
    config = load_config(Path("config/default.toml"))

    assert config.build.project == "jawiki"
    assert config.paths.data_dir == Path("/data")


def test_rejects_missing_required_table(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.toml"
    config_path.write_text(
        "[build]\nschema_version = 1\nproject = 'jawiki'\nprofile = 'minimal'\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match=r"\[paths\]"):
        load_config(config_path)
