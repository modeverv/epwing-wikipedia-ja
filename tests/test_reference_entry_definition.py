from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_eb_entry_binary_uses_bounded_text_and_required_hooks() -> None:
    source = (ROOT / "docker/toolchain/eb-entry.c").read_text(encoding="utf-8")
    build = (ROOT / "docker/toolchain/build-eb.sh").read_text(encoding="utf-8")

    for token in (
        "eb_seek_text",
        "eb_read_text",
        "eb_is_text_stopped",
        "EB_HOOK_END_REFERENCE",
        "EB_HOOK_BEGIN_COLOR_BMP",
        "EB_HOOK_NARROW_FONT",
        "EB_HOOK_WIDE_FONT",
        "MAX_BODY_BYTES",
    ):
        assert token in source
    assert "-Werror" in build
    assert "wikiepwing-eb-entry" in build
