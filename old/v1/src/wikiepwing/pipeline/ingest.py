"""Raw XML ingestion stage orchestration."""

from __future__ import annotations

from pathlib import Path

from wikiepwing.dump.xml_reader import stream_pages
from wikiepwing.storage.database import RawPage, RawPageStore


def ingest_xml(xml_path: Path, database_path: Path, batch_size: int = 500) -> int:
    """Atomically commit bounded batches and return the stored record count."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    store = RawPageStore(database_path)
    batch: list[RawPage] = []
    count = 0
    try:
        for page in stream_pages(xml_path):
            batch.append(page)
            if len(batch) == batch_size:
                store.insert_batch(batch)
                count += len(batch)
                batch.clear()
        if batch:
            store.insert_batch(batch)
            count += len(batch)
    finally:
        store.close()
    return count
