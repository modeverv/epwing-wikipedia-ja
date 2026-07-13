from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_eb_search_binary_uses_required_library_and_encoding_apis() -> None:
    source = (ROOT / "docker/toolchain/eb-search.c").read_text(encoding="utf-8")
    build = (ROOT / "docker/toolchain/build-eb.sh").read_text(encoding="utf-8")

    for token in (
        "eb_character_code",
        "iconv_open",
        "eb_search_word",
        "eb_search_endword",
        "eb_hit_list",
        "eb_read_heading",
        "FTW_PHYS",
    ):
        assert token in source
    assert "-Werror" in build
    assert "wikiepwing-eb-search" in build


def test_reference_inspector_runtime_combines_python_and_toolchain_safely() -> None:
    dockerfile = (ROOT / "docker/toolchain.Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.reference.yaml").read_text(encoding="utf-8")

    assert "python:3.12.13-slim-bookworm@sha256:" in dockerfile
    assert "uv==0.11.17" in dockerfile
    assert "reference-inspector:" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "create_host_path: false" in compose
