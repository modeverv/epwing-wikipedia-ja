from wikiepwing.mediawiki.parser import parse_article


def test_parses_headings_paragraphs_and_internal_links() -> None:
    article = parse_article(1, "Emacs", "Lead [[GNU Emacs|editor]].\n\n== History ==\nText")

    assert [block.kind for block in article.blocks] == ["paragraph", "heading", "paragraph"]
    assert article.blocks[0].inlines[1].target == "GNU Emacs"
    assert article.blocks[1].level == 1
