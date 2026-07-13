from wikiepwing.mediawiki.parser import parse_article
from wikiepwing.render.text import render_article


def test_ado_like_article_does_not_expose_raw_wikitext() -> None:
    source = """{{Infobox Musician
| 名前 = Ado
| 画像 = Ado.jpg
| 出生 = {{生年月日と年齢|2002|10|24}}
| 出身地 = {{JPN}} 東京都<ref>source</ref>
}}
{{Otheruses|日本の歌手}}
'''Ado''' は日本の歌手。
{{Cite web|title=Ado|url=https://example.test/ado}}

== 経歴 ==
* 2017年 - 活動開始
{| class="wikitable"
|-
! 年 !! 出来事
|-
| 2020 || デビュー
|}
"""
    rendered = render_article(parse_article(1, "Ado", source))

    assert "【名前】Ado" in rendered
    assert "【出身地】東京都" in rendered
    assert "2017年 - 活動開始" in rendered
    assert "年 | 出来事" in rendered
    assert "{{" not in rendered
    assert "<ref" not in rendered
    assert "example.test" not in rendered
    assert "@@IMAGE:" in rendered
    assert "Ado.jpg" in rendered
    assert "[[" not in rendered


def test_infobox_logo_is_image_not_raw_field() -> None:
    rendered = render_article(
        parse_article(
            1,
            "Emacs Lisp",
            "\n".join(
                (
                    "{{Infobox programming language",
                    "| name = Emacs Lisp",
                    "| logo = EmacsIcon.svg",
                    "| logo size = 150px",
                    "}}",
                )
            ),
        )
    )

    assert "Images:" in rendered
    assert "EmacsIcon.svg" in rendered
    assert "【logo】" not in rendered
    assert "【logo size】" not in rendered
