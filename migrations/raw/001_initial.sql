PRAGMA application_id = 1380013892;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 100),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE articles (
    page_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL CHECK (revision_id > 0),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 8192),
    normalized_title TEXT NOT NULL CHECK (length(normalized_title) BETWEEN 1 AND 8192),
    namespace_id INTEGER NOT NULL,
    url TEXT NOT NULL CHECK (length(url) BETWEEN 1 AND 8192),
    date_modified TEXT NOT NULL CHECK (length(date_modified) BETWEEN 1 AND 64),
    html_zstd BLOB,
    wikitext_zstd BLOB,
    source_hash TEXT NOT NULL CHECK (length(source_hash) = 64),
    source_sequence INTEGER NOT NULL CHECK (source_sequence >= 0),
    ingest_status TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    CHECK (ingest_status IN ('accepted', 'rejected', 'deleted')),
    CHECK (is_deleted IN (0, 1))
) STRICT;

CREATE UNIQUE INDEX articles_normalized_title_page
    ON articles(normalized_title, page_id);

CREATE INDEX articles_source_sequence ON articles(source_sequence);

CREATE TABLE redirects (
    target_page_id INTEGER NOT NULL,
    redirect_title TEXT NOT NULL CHECK (length(redirect_title) BETWEEN 1 AND 8192),
    normalized_redirect_title TEXT NOT NULL CHECK (length(normalized_redirect_title) BETWEEN 1 AND 8192),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (target_page_id, normalized_redirect_title),
    FOREIGN KEY (target_page_id) REFERENCES articles(page_id)
) WITHOUT ROWID, STRICT;

CREATE INDEX redirects_lookup
    ON redirects(normalized_redirect_title);

CREATE TABLE categories (
    page_id INTEGER NOT NULL,
    category_name TEXT NOT NULL CHECK (length(category_name) BETWEEN 1 AND 8192),
    normalized_category_name TEXT NOT NULL CHECK (length(normalized_category_name) BETWEEN 1 AND 8192),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (page_id, normalized_category_name),
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) WITHOUT ROWID, STRICT;

CREATE TABLE templates (
    page_id INTEGER NOT NULL,
    template_name TEXT NOT NULL CHECK (length(template_name) BETWEEN 1 AND 8192),
    normalized_template_name TEXT NOT NULL CHECK (length(normalized_template_name) BETWEEN 1 AND 8192),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (page_id, normalized_template_name),
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) WITHOUT ROWID, STRICT;

CREATE TABLE licenses (
    license_id INTEGER PRIMARY KEY,
    identifier TEXT NOT NULL CHECK (length(identifier) BETWEEN 1 AND 255),
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 8192),
    url TEXT NOT NULL CHECK (length(url) BETWEEN 1 AND 8192),
    UNIQUE (identifier, url)
) STRICT;

CREATE TABLE article_licenses (
    page_id INTEGER NOT NULL,
    license_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    PRIMARY KEY (page_id, license_id),
    FOREIGN KEY (page_id) REFERENCES articles(page_id),
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
) WITHOUT ROWID, STRICT;

CREATE TABLE main_images (
    page_id INTEGER PRIMARY KEY,
    content_url TEXT NOT NULL CHECK (length(content_url) BETWEEN 1 AND 8192),
    width INTEGER CHECK (width IS NULL OR width > 0),
    height INTEGER CHECK (height IS NULL OR height > 0),
    FOREIGN KEY (page_id) REFERENCES articles(page_id)
) STRICT;

CREATE TABLE ingest_duplicates (
    duplicate_id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL,
    kept_revision_id INTEGER NOT NULL CHECK (kept_revision_id > 0),
    dropped_revision_id INTEGER NOT NULL CHECK (dropped_revision_id > 0),
    kept_hash TEXT NOT NULL CHECK (length(kept_hash) = 64),
    dropped_hash TEXT NOT NULL CHECK (length(dropped_hash) = 64),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 255),
    source_sequence INTEGER NOT NULL CHECK (source_sequence >= 0)
) STRICT;

CREATE INDEX ingest_duplicates_page ON ingest_duplicates(page_id);

CREATE TABLE diagnostics (
    diagnostic_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL CHECK (length(code) BETWEEN 1 AND 100),
    severity TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (length(stage) BETWEEN 1 AND 100),
    page_id INTEGER,
    title TEXT,
    message TEXT NOT NULL CHECK (length(message) BETWEEN 1 AND 8192),
    source_path TEXT,
    source_excerpt TEXT,
    details_json TEXT NOT NULL,
    CHECK (severity IN ('info', 'warning', 'error', 'fatal'))
) STRICT;

CREATE INDEX diagnostics_code ON diagnostics(code);
CREATE INDEX diagnostics_page ON diagnostics(page_id);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY CHECK (length(key) BETWEEN 1 AND 100),
    value TEXT NOT NULL
) STRICT;
