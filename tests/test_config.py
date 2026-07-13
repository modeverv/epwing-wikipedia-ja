from __future__ import annotations

import re
from pathlib import Path

import pytest

from wikiepwing.config import ConfigurationError, load_config

DEFAULT_CONFIG = Path("config/default.toml")


def test_loads_default_configuration() -> None:
    config = load_config(DEFAULT_CONFIG)

    assert config.schema_version == 1
    assert config.project == "jawiki"
    assert config.profile == "lite"
    assert config.paths.sources == Path("/data/sources")


def test_deep_merges_override_and_resolves_relative_path(tmp_path: Path) -> None:
    override = tmp_path / "override.toml"
    override.write_text(
        """
[paths]
output = "artifacts"

[images]
max_per_article = 8
""",
        encoding="utf-8",
    )

    config = load_config(DEFAULT_CONFIG, [override])

    assert config.paths.output == (tmp_path / "artifacts").resolve()
    assert config.paths.sources == Path("/data/sources")
    assert config.section("images")["enabled"] is True
    assert config.section("images")["max_per_article"] == 8


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("unknown = true\n", "unknown configuration key: unknown"),
        ("[images]\nunknown = true\n", "unknown configuration key: images.unknown"),
        ("schema_version = 2\n", "unsupported schema_version: 2"),
        ("[images]\nmax_per_article = 'many'\n", "images.max_per_article must be an integer"),
        ("[ingest]\nbatch_size = -1\n", "ingest.batch_size must not be negative"),
        (
            "[images]\nenabled = true\nmax_per_article = 0\n",
            "images.max_per_article must be positive when images are enabled",
        ),
    ],
)
def test_rejects_invalid_configuration(
    tmp_path: Path,
    contents: str,
    message: str,
) -> None:
    override = tmp_path / "invalid.toml"
    override.write_text(contents, encoding="utf-8")

    with pytest.raises(ConfigurationError, match=re.escape(message)):
        load_config(DEFAULT_CONFIG, [override])


def test_rejects_invalid_toml(tmp_path: Path) -> None:
    override = tmp_path / "invalid.toml"
    override.write_text("[paths\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="invalid TOML"):
        load_config(DEFAULT_CONFIG, [override])


def test_rejects_writable_paths_inside_reference(tmp_path: Path) -> None:
    override = tmp_path / "invalid-path.toml"
    override.write_text(
        """
[paths]
output = "/data/reference/generated"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="paths.output must not be inside"):
        load_config(DEFAULT_CONFIG, [override])


def test_rejects_unsafe_public_distribution_policy(tmp_path: Path) -> None:
    override = tmp_path / "public.toml"
    override.write_text(
        """
[distribution]
mode = "public"
include_attribution_appendix = true
exclude_images_without_license = true
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="missing_license_action cannot be warn"):
        load_config(DEFAULT_CONFIG, [override])
