from wikiepwing.search.headwords import build_headword_index


def test_builds_canonical_and_redirect_lookup_keys() -> None:
    index = build_headword_index(("Emacs",), (("GNU_Emacs", "Emacs"),))

    assert index.entries == (("Emacs", "Emacs"), ("GNU Emacs", "Emacs"))
    assert index.collisions == ()


def test_reports_collision_without_overwrite() -> None:
    index = build_headword_index(("Emacs",), (("Ｅｍａｃｓ", "Other"),))

    assert index.entries == (("Emacs", "Emacs"),)
    assert index.collisions == ("Emacs",)
