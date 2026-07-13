import bz2
from pathlib import Path

import pytest

from wikiepwing.dump.xml_reader import stream_pages
from wikiepwing.pipeline.ingest import ingest_xml
from wikiepwing.storage.database import RawPage, RawPageStore

FIXTURE = """<mediawiki>
<page><title>Emacs</title><ns>0</ns><id>1</id><revision><id>11</id><text>Editor</text></revision></page>
<page><title>GNU Emacs</title><ns>0</ns><id>2</id><redirect title="Emacs"/>
<revision><id>12</id><text>#REDIRECT [[Emacs]]</text></revision></page>
<page><title>Talk:Emacs</title><ns>1</ns><id>3</id><revision><id>13</id><text>ignored</text></revision></page>
<page><title>日本語</title><ns>0</ns><id>4</id><revision><id>14</id><text /></revision></page>
</mediawiki>"""


def test_streams_pages_filters_namespaces_and_persists(tmp_path: Path) -> None:
    xml = tmp_path / "fixture.xml"
    xml.write_text(FIXTURE, encoding="utf-8")
    pages = list(stream_pages(xml))

    assert [page.page_id for page in pages] == [1, 2, 4]
    assert pages[1].redirect_target == "Emacs"
    assert pages[2].title == "日本語"
    assert pages[2].text == ""

    store = RawPageStore(tmp_path / "raw.sqlite3")
    store.insert_batch(pages)
    assert list(store.pages()) == pages
    store.close()


def test_streams_bzip2_without_expanding(tmp_path: Path) -> None:
    compressed = tmp_path / "fixture.xml.bz2"
    compressed.write_bytes(bz2.compress(FIXTURE.encode("utf-8")))

    assert [page.title for page in stream_pages(compressed)] == ["Emacs", "GNU Emacs", "日本語"]


def test_ingest_commits_small_batches(tmp_path: Path) -> None:
    xml = tmp_path / "fixture.xml"
    xml.write_text(FIXTURE, encoding="utf-8")

    assert ingest_xml(xml, tmp_path / "raw.sqlite3", batch_size=1) == 3
    assert ingest_xml(xml, tmp_path / "raw.sqlite3", batch_size=1) == 3


def test_store_rejects_conflicting_duplicate_page_id(tmp_path: Path) -> None:
    store = RawPageStore(tmp_path / "raw.sqlite3")
    store.insert_batch([RawPage(1, "Emacs", 0, 1, "old", None)])

    with pytest.raises(ValueError, match="conflicting duplicate"):
        store.insert_batch([RawPage(1, "Emacs", 0, 1, "new", None)])
    store.close()
