from wikiepwing.epwing.source import freepwing_records
from wikiepwing.mediawiki.parser import parse_article


def test_serializes_stable_freepwing_adapter_records() -> None:
    emacs = parse_article(1, "Emacs", "Editor")
    linux = parse_article(2, "Linux", "Kernel")

    assert freepwing_records((linux, emacs)) == (
        "Emacs\tEmacs\\nEditor\\n\nLinux\tLinux\\nKernel\\n\n"
    )
