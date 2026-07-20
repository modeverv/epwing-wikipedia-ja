from wikiepwing.mediawiki.redirects import normalize_title, resolve_redirects


def test_normalizes_compatibility_and_whitespace() -> None:
    assert normalize_title("  Ｅｍａｃｓ__Wiki ") == "Emacs Wiki"
    assert normalize_title("日本　語") == "日本 語"


def test_resolves_chains_cycles_and_missing_targets() -> None:
    results = resolve_redirects(
        {"Emacs", "Linux"},
        {
            "GNU_Emacs": "Emacs",
            "Editor": "GNU Emacs",
            "Loop A": "Loop B",
            "Loop B": "Loop A",
            "Lost": "Absent",
        },
    )

    assert results[0].target == "Emacs"
    assert results[1].target == "Emacs"
    assert {result.diagnostic for result in results} == {
        None,
        "REDIRECT_CYCLE",
        "REDIRECT_TARGET_MISSING",
    }
