from wikiepwing.mediawiki.templates import render_template


def test_unknown_template_preserves_arguments_and_diagnostic() -> None:
    result = render_template("Infobox person", ("Ada",), (("born", "1815"),))

    assert result.text == "Ada; born: 1815"
    assert result.diagnostic == "TEMPLATE_UNSUPPORTED"


def test_known_maintenance_template_is_removed() -> None:
    assert render_template("Cleanup", ()).text == ""
