import pytest

from wikiepwing.model.article import Article, Block, Inline, MediaReference


def test_article_serialization_is_deterministic() -> None:
    article = Article(1, "Emacs", (Block("heading", (Inline("Lead"),), 1),), ("GNU Emacs",))

    assert article.to_json() == article.to_json()
    assert '"schema_version":2' in article.to_json()


def test_invalid_block_nesting_is_rejected() -> None:
    with pytest.raises(ValueError, match="heading level"):
        Block("heading", (Inline("bad"),))


def test_article_can_carry_media_references() -> None:
    article = Article(
        1,
        "Ado",
        (),
        media=(MediaReference("Ado.jpg", "portrait", "infobox"),),
    )

    assert '"file_name":"Ado.jpg"' in article.to_json()
