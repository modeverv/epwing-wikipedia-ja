from wikiepwing.mediawiki.parser import parse_article
from wikiepwing.render.text import render_article


def test_renders_compact_source_order_layout() -> None:
    article = parse_article(1, "Emacs", "Lead\n\n== History ==\nText")

    assert render_article(article) == "Emacs\nLead\n\n# History\n\nText\n"
