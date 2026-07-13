from pathlib import Path

from wikiepwing.pipeline.export import export_records
from wikiepwing.storage.database import RawPage, RawPageStore


def test_exports_raw_pages_to_adapter_records(tmp_path: Path) -> None:
    database = tmp_path / "raw.sqlite3"
    store = RawPageStore(database)
    store.insert_batch([RawPage(1, "Emacs", 0, 1, "Editor", None)])
    store.close()
    records = tmp_path / "records.tsv"

    assert export_records(database, records) == 1
    assert records.read_text(encoding="utf-8") == "Emacs\tEmacs\\nEditor\\n\n"
