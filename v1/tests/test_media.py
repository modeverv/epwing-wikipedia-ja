from wikiepwing.mediawiki.media import extract_media_references, strip_file_links


def test_extracts_infobox_and_article_images_deterministically() -> None:
    source = """{{Infobox Musician
| 画像 = Ado_profile.jpg
| 出生 = {{生年月日と年齢|2002|10|24}}
}}
Lead [[File:Ado_live.jpg|thumb|Ado live]] text
[[画像:Ado_profile.jpg|重複]]
"""

    media = extract_media_references(source)

    assert [item.file_name for item in media] == ["Ado profile.jpg", "Ado live.jpg"]
    assert media[0].source == "infobox"
    assert media[1].caption == "Ado live"
    assert "[[File:" not in strip_file_links(source)


def test_extracts_infobox_logo_fields() -> None:
    source = """{{Infobox programming language
| logo = EmacsIcon.svg
| logo size = 150px
}}"""

    media = extract_media_references(source)

    assert [item.file_name for item in media] == ["EmacsIcon.svg"]


def test_skips_commented_images_but_keeps_file_links() -> None:
    source = """{{Infobox
| image = <!-- [[File:Example.png|200px]] -->
| logo = [[File:Logo.png|frameless]]
}}"""

    media = extract_media_references(source)

    assert [item.file_name for item in media] == ["Logo.png"]
