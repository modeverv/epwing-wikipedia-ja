# DATA_CONTRACTS.md

## 1. 目的

この文書は、ステージ間で受け渡すデータ形式を固定します。弱い実装エージェントが、同じ概念を別名・別形式で増殖させることを防ぎます。

契約変更時:

1. schema versionを増やす
2. migrationまたは再生成方針を追加
3. codec/validator testを更新
4. stage versionを増やす
5. `DECISIONS.md`へ影響を記録

---

## 2. Source lock contract

Path:

```text
/data/sources/<project>/<snapshot-version>/source.lock.json
```

Required JSON:

```json
{
  "schema_version": 1,
  "provider": "wikimedia-enterprise-snapshot",
  "project": "jawiki",
  "namespace": 0,
  "snapshot_identifier": "jawiki_namespace_0",
  "snapshot_version": "string",
  "date_modified": "RFC3339",
  "downloaded_at": "RFC3339",
  "files": [
    {
      "relative_path": "jawiki_namespace_0_chunk_0.ndjson.gz",
      "chunk_identifier": "jawiki_namespace_0_chunk_0",
      "size_bytes": 1,
      "sha256": "64 lowercase hex chars",
      "media_type": "application/gzip"
    }
  ],
  "supplements": [],
  "metadata_response_sha256": "64 lowercase hex chars",
  "acquirer": {
    "name": "wikiepwing",
    "version": "semver",
    "git_commit": "hex"
  }
}
```

Snapshotはproject/namespaceあたり複数chunkへ分割配信される(ADR-016)。`files`は1 chunkにつき1エントリを持ち、`chunk_identifier`はSnapshot metadataの`chunks`配列の要素と1:1対応する。

Invariants:

- `files` non-empty
- `files`の`chunk_identifier`は重複しない
- path relative, no `..`
- concrete `snapshot_version`; `latest` forbidden
- no credentials
- timestamps UTC
- actual size/hash match before use

---

## 3. Stage manifest contract

Path:

```text
/data/work/runs/<run-id>/manifests/<stage>.json
```

```json
{
  "schema_version": 1,
  "stage": "30-ingest",
  "stage_version": 1,
  "status": "complete",
  "run_id": "...",
  "started_at": "RFC3339",
  "completed_at": "RFC3339",
  "inputs": {
    "source_lock": "sha256:...",
    "config": "sha256:..."
  },
  "outputs": [
    {
      "relative_path": "raw.sqlite3",
      "size_bytes": 1,
      "sha256": "...",
      "logical_hash": "..."
    }
  ],
  "metrics": {
    "records_read": 0,
    "records_written": 0,
    "records_rejected": 0,
    "warnings": 0,
    "errors": 0,
    "fatals": 0
  },
  "software": {
    "git_commit": "...",
    "app_image_digest": "...",
    "toolchain_image_digest": "..."
  }
}
```

Status enum:

```text
running
complete
failed
interrupted
invalid
```

`complete`以外をcache reuseしてはいけません。

---

## 4. raw.sqlite3 schema draft

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA busy_timeout = 30000;

CREATE TABLE schema_info (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT;

CREATE TABLE articles (
    page_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    namespace_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    html_zstd BLOB,
    wikitext_zstd BLOB,
    source_hash TEXT NOT NULL,
    source_sequence INTEGER NOT NULL,
    ingest_status TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    CHECK (ingest_status IN ('accepted', 'rejected', 'deleted')),
    CHECK (is_deleted IN (0, 1))
) STRICT;

CREATE UNIQUE INDEX articles_normalized_title_page
    ON articles(normalized_title, page_id);

CREATE TABLE redirects (
    target_page_id INTEGER NOT NULL,
    redirect_title TEXT NOT NULL,
    normalized_redirect_title TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (target_page_id, normalized_redirect_title),
    FOREIGN KEY (target_page_id) REFERENCES articles(page_id)
) WITHOUT ROWID;

CREATE INDEX redirects_lookup
    ON redirects(normalized_redirect_title);

CREATE TABLE categories (
    page_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    normalized_category_name TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (page_id, normalized_category_name),
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) WITHOUT ROWID;

CREATE TABLE templates (
    page_id INTEGER NOT NULL,
    template_name TEXT NOT NULL,
    normalized_template_name TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (page_id, normalized_template_name),
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) WITHOUT ROWID;

CREATE TABLE licenses (
    license_id INTEGER PRIMARY KEY,
    identifier TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    UNIQUE(identifier, url)
) STRICT;

CREATE TABLE article_licenses (
    page_id INTEGER NOT NULL,
    license_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (page_id, license_id),
    FOREIGN KEY (page_id) REFERENCES articles(page_id),
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
) WITHOUT ROWID;

CREATE TABLE main_images (
    page_id INTEGER PRIMARY KEY,
    content_url TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) STRICT;

CREATE TABLE ingest_duplicates (
    duplicate_id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL,
    kept_revision_id INTEGER NOT NULL,
    dropped_revision_id INTEGER NOT NULL,
    kept_hash TEXT NOT NULL,
    dropped_hash TEXT NOT NULL,
    reason TEXT NOT NULL,
    source_sequence INTEGER NOT NULL
) STRICT;

CREATE TABLE diagnostics (
    diagnostic_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    severity TEXT NOT NULL,
    stage TEXT NOT NULL,
    page_id INTEGER,
    title TEXT,
    message TEXT NOT NULL,
    source_path TEXT,
    source_excerpt TEXT,
    details_json TEXT NOT NULL,
    CHECK (severity IN ('info', 'warning', 'error', 'fatal'))
) STRICT;

CREATE INDEX diagnostics_code ON diagnostics(code);
CREATE INDEX diagnostics_page ON diagnostics(page_id);
```

Raw DBはsource contentの保存だけを行い、semantic blockを持ちません。

---

## 5. model.sqlite3 schema draft

```sql
CREATE TABLE schema_info (...);

CREATE TABLE articles (
    page_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_date_modified TEXT NOT NULL,
    abstract TEXT,
    article_json_zstd BLOB NOT NULL,
    article_logical_hash TEXT NOT NULL,
    normalize_status TEXT NOT NULL,
    block_count INTEGER NOT NULL,
    diagnostic_count INTEGER NOT NULL,
    CHECK (normalize_status IN ('complete', 'fallback', 'rejected'))
) STRICT;

CREATE TABLE links (
    source_page_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    target_page_id INTEGER,
    target_title TEXT NOT NULL,
    target_fragment TEXT,
    resolution TEXT NOT NULL,
    PRIMARY KEY (source_page_id, ordinal),
    CHECK (resolution IN ('resolved', 'missing', 'externalized'))
) WITHOUT ROWID;

CREATE INDEX links_target ON links(target_page_id);

CREATE TABLE media_references (
    page_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    media_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_name TEXT,
    alt_text TEXT,
    caption TEXT,
    role TEXT NOT NULL,
    source_width INTEGER,
    source_height INTEGER,
    PRIMARY KEY (page_id, ordinal)
) WITHOUT ROWID;

CREATE TABLE diagnostics (...same logical columns...);
```

`article_json_zstd`の正本schemaは次のArticle JSON contractです。

---

## 6. Article JSON contract

```json
{
  "schema_version": 1,
  "page_id": 123,
  "revision_id": 456,
  "title": "Emacs",
  "normalized_title": "Emacs",
  "source_url": "https://ja.wikipedia.org/wiki/Emacs",
  "source_date_modified": "2026-01-01T00:00:00Z",
  "abstract": null,
  "blocks": [],
  "aliases": [],
  "categories": [],
  "media": [],
  "diagnostics": [],
  "source_license_ids": ["CC-BY-SA-3.0"]
}
```

### Block JSON

Common:

```json
{
  "type": "paragraph",
  "source_path": "body/section[1]/p[2]"
}
```

Paragraph:

```json
{
  "type": "paragraph",
  "inlines": []
}
```

Heading:

```json
{
  "type": "heading",
  "level": 2,
  "anchor": "History",
  "inlines": []
}
```

List:

```json
{
  "type": "unordered_list",
  "items": [
    {"blocks": []}
  ]
}
```

Table:

```json
{
  "type": "table",
  "caption": [],
  "rows": [
    [
      {
        "blocks": [],
        "row_span": 1,
        "col_span": 1,
        "is_header": true
      }
    ]
  ],
  "source_class_names": ["wikitable"],
  "complexity": "simple"
}
```

Unsupported:

```json
{
  "type": "unsupported",
  "element_name": "custom-tag",
  "fallback_text": "visible text",
  "diagnostic_code": "DOM_UNKNOWN_ELEMENT"
}
```

### Inline JSON

Text:

```json
{"type": "text", "value": "text"}
```

Internal link:

```json
{
  "type": "internal_link",
  "label": [{"type": "text", "value": "GNU Emacs"}],
  "target_title": "GNU Emacs",
  "target_normalized_title": "GNU Emacs",
  "target_fragment": null,
  "target_page_id": 1234,
  "resolution": "resolved"
}
```

Unknown `type`はcodec error。将来type追加時にschema versionまたはbackward-compatible decoderを明示します。

---

## 7. rendered.sqlite3 schema draft

```sql
CREATE TABLE entries (
    entry_id TEXT PRIMARY KEY,
    page_id INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    body_json_zstd BLOB NOT NULL,
    estimated_size INTEGER NOT NULL,
    rendered_logical_hash TEXT NOT NULL,
    render_status TEXT NOT NULL,
    CHECK (render_status IN ('complete', 'split', 'rejected'))
) STRICT;

CREATE TABLE entry_parts (
    parent_entry_id TEXT NOT NULL,
    part_index INTEGER NOT NULL,
    part_entry_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    body_json_zstd BLOB NOT NULL,
    PRIMARY KEY (parent_entry_id, part_index),
    FOREIGN KEY (parent_entry_id) REFERENCES entries(entry_id)
) WITHOUT ROWID;

CREATE TABLE search_terms (
    term_id INTEGER PRIMARY KEY,
    key TEXT NOT NULL,
    normalized_key TEXT NOT NULL,
    target_entry_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    priority INTEGER NOT NULL,
    source TEXT NOT NULL
) STRICT;

CREATE INDEX search_terms_lookup
    ON search_terms(normalized_key, priority, target_entry_id);

CREATE TABLE graphics (
    graphic_id TEXT PRIMARY KEY,
    source_hash TEXT NOT NULL,
    format TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE entry_graphics (
    entry_id TEXT NOT NULL,
    graphic_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (entry_id, ordinal),
    FOREIGN KEY (entry_id) REFERENCES entries(entry_id),
    FOREIGN KEY (graphic_id) REFERENCES graphics(graphic_id)
) WITHOUT ROWID;
```

---

## 8. SearchTerm contract

```json
{
  "key": "Ｅｍａｃｓ",
  "normalized_key": "emacs",
  "target_entry_id": "p12345",
  "kind": "alias",
  "priority": 300,
  "source": "redirect"
}
```

Priority proposal:

```text
1000 exact title
900 original redirect
800 normalized title variant
700 explicit alias
600 kana variant
500 category
400 heading keyword
300 infobox keyword
200 lead term
100 cross component
```

同priorityは`normalized_key`, `target_entry_id`, `source`で安定sort。

---

## 9. Media cache contract

Path:

```text
/data/cache/media/<first2>/<sha256>/
├── source.bin
├── converted.png
└── metadata.json
```

Metadata:

```json
{
  "schema_version": 1,
  "cache_key": "sha256",
  "canonical_url": "https://...",
  "downloaded_at": "RFC3339",
  "http": {
    "status": 200,
    "content_type": "image/png",
    "etag": null,
    "last_modified": null
  },
  "source": {
    "size_bytes": 1,
    "sha256": "..."
  },
  "converted": {
    "format": "png",
    "width": 320,
    "height": 200,
    "size_bytes": 1,
    "sha256": "...",
    "converter_version": "..."
  },
  "attribution": {
    "source_page_url": null,
    "author": null,
    "license_identifier": null,
    "license_url": null
  }
}
```

Incomplete cache directory is never a hit.

---

## 10. Gaiji registry contract

```sql
CREATE TABLE gaiji (
    sequence TEXT PRIMARY KEY,
    normalized_sequence TEXT NOT NULL,
    width_class TEXT NOT NULL,
    assigned_code TEXT NOT NULL UNIQUE,
    bitmap_path TEXT NOT NULL,
    bitmap_sha256 TEXT NOT NULL,
    font_identifier TEXT NOT NULL,
    usage_count INTEGER NOT NULL,
    CHECK (width_class IN ('narrow', 'wide'))
) STRICT;
```

AssignmentはUnicode sort order + width classなどの決定論的規則を使用。処理順依存にしません。

---

## 11. Diagnostic details contract

`details_json`はcodeごとに任意ですが、秘密情報・巨大HTML全体を含めません。

最大サイズを設定し、source excerptは数百〜数千文字に制限。

Example:

```json
{
  "element": "table",
  "classes": ["wikitable"],
  "row_count": 5000,
  "cell_count": 50000,
  "policy": "split"
}
```

---

## 12. Build artifact contract

```text
output/
├── jawiki-<snapshot>-mini.epwing.zip
├── jawiki-<snapshot>-lite.epwing.zip
├── jawiki-<snapshot>-full.epwing.zip
├── jawiki-<snapshot>-<profile>.sha256
├── jawiki-<snapshot>-<profile>-BUILD-INFO.json
├── jawiki-<snapshot>-<profile>-report.json
├── jawiki-<snapshot>-<profile>-report.html
└── jawiki-<snapshot>-<profile>-attribution.jsonl
```

ZIP internal root:

```text
<book-directory>/
BUILD-INFO.json
LICENSES.txt
ATTRIBUTION.txt or attribution data
```

backendが辞書directory以外の添付を許さない場合、sidecar archive/adjacent filesとしてpackage contractを調整しADRへ記録。
