PRAGMA application_id = 1297040460;

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
    source_url TEXT NOT NULL CHECK (length(source_url) BETWEEN 1 AND 8192),
    source_date_modified TEXT NOT NULL CHECK (length(source_date_modified) BETWEEN 1 AND 64),
    abstract TEXT,
    article_json_zstd BLOB NOT NULL,
    article_logical_hash TEXT NOT NULL CHECK (length(article_logical_hash) = 64),
    normalize_status TEXT NOT NULL,
    block_count INTEGER NOT NULL CHECK (block_count >= 0),
    diagnostic_count INTEGER NOT NULL CHECK (diagnostic_count >= 0),
    CHECK (normalize_status IN ('complete', 'fallback', 'rejected'))
) STRICT;

CREATE INDEX articles_normalize_status ON articles(normalize_status);

CREATE TABLE links (
    source_page_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    target_page_id INTEGER,
    target_title TEXT NOT NULL CHECK (length(target_title) BETWEEN 1 AND 8192),
    target_fragment TEXT,
    resolution TEXT NOT NULL,
    PRIMARY KEY (source_page_id, ordinal),
    FOREIGN KEY (source_page_id) REFERENCES articles(page_id),
    CHECK (resolution IN ('resolved', 'missing', 'externalized'))
) WITHOUT ROWID, STRICT;

CREATE INDEX links_target ON links(target_page_id);

CREATE TABLE media_references (
    page_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    media_id TEXT NOT NULL CHECK (length(media_id) BETWEEN 1 AND 8192),
    source_url TEXT NOT NULL CHECK (length(source_url) BETWEEN 1 AND 8192),
    source_name TEXT,
    alt_text TEXT,
    caption TEXT,
    role TEXT NOT NULL,
    source_width INTEGER CHECK (source_width IS NULL OR source_width >= 0),
    source_height INTEGER CHECK (source_height IS NULL OR source_height >= 0),
    PRIMARY KEY (page_id, ordinal),
    FOREIGN KEY (page_id) REFERENCES articles(page_id),
    CHECK (role IN ('main', 'infobox', 'lead', 'body', 'icon', 'unknown'))
) WITHOUT ROWID, STRICT;

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
