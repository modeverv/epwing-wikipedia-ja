from wikiepwing.mediawiki.tables import parse_table, render_table


def test_parses_and_renders_simple_table() -> None:
    result = parse_table("{|\n! Year !! Event\n|-\n| 2024 || Success\n|}")

    assert result.diagnostic is None
    assert render_table(result) == "Year | Event\n2024 | Success"


def test_rejects_malformed_table() -> None:
    assert parse_table("not a table").diagnostic == "TABLE_PARSE_FAILED"
