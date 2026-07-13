from __future__ import annotations

import json
from pathlib import Path

PROBE_SOURCE = Path("docker/toolchain/eb-probe.c")
BUILD_SCRIPT = Path("docker/toolchain/build-eb.sh")
PROBE_SCRIPT = Path("docker/toolchain/probe.sh")


def test_probe_source_uses_eb_search_text_and_feature_hooks() -> None:
    source = PROBE_SOURCE.read_text(encoding="utf-8")

    assert "eb_search_word" in source
    assert "eb_hit_list" in source
    assert "eb_read_text" in source
    for hook in (
        "EB_HOOK_END_REFERENCE",
        "EB_HOOK_BEGIN_COLOR_BMP",
        "EB_HOOK_NARROW_FONT",
        "EB_HOOK_WIDE_FONT",
    ):
        assert hook in source
    assert '"Emacs"' in source
    assert '"Linux"' in source
    assert '"Wikipedia"' in source


def test_probe_binary_is_built_into_runtime_prefix() -> None:
    build = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert "/tmp/toolchain/eb-probe.c" in build
    assert "/opt/eb/bin/wikiepwing-eb-probe" in build
    assert "-Wl,-rpath,/opt/eb/lib" in build


def test_probe_command_writes_and_validates_capability_json() -> None:
    script = PROBE_SCRIPT.read_text(encoding="utf-8")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "toolchain-capabilities.json" in script
    assert "handcrafted-three-entry-smoke.sh" in script
    assert "json.load" in script
    assert "probe-toolchain:" in makefile
    assert "docker/toolchain/probe.sh" in makefile


def test_expected_probe_schema_is_json_serializable() -> None:
    expected = {
        "schema_version": 1,
        "eb_library_version": "4.4.3",
        "subbook_count": 1,
        "directory": "wikiep",
        "search_methods": ["word", "endword"],
        "queries": {"Emacs": 1, "Linux": 3, "Wikipedia": 1},
        "text_entries_read": 3,
        "hooks": {"reference": 6, "bmp": 3, "narrow_gaiji": 2, "wide_gaiji": 2},
    }
    assert json.loads(json.dumps(expected, sort_keys=True)) == expected
