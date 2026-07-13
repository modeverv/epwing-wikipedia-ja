PRAGMA application_id = 1464156242;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 100),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE reference_books (
    book_id INTEGER PRIMARY KEY,
    source_fingerprint TEXT NOT NULL UNIQUE CHECK (length(source_fingerprint) = 64),
    catalog_path TEXT NOT NULL CHECK (length(catalog_path) BETWEEN 1 AND 4096),
    catalog_size_bytes INTEGER NOT NULL CHECK (catalog_size_bytes > 0),
    inventory_sha256 TEXT NOT NULL CHECK (length(inventory_sha256) = 64),
    identifier TEXT CHECK (identifier IS NULL OR length(identifier) BETWEEN 1 AND 255),
    UNIQUE (catalog_path, source_fingerprint)
) STRICT;

CREATE TABLE reference_subbooks (
    subbook_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    code TEXT NOT NULL CHECK (length(code) BETWEEN 1 AND 8),
    title TEXT CHECK (title IS NULL OR length(title) BETWEEN 1 AND 4096),
    directory TEXT NOT NULL CHECK (length(directory) BETWEEN 1 AND 4096),
    FOREIGN KEY (book_id) REFERENCES reference_books(book_id) ON DELETE CASCADE,
    UNIQUE (book_id, code),
    UNIQUE (book_id, directory),
    UNIQUE (subbook_id, book_id)
) STRICT;

CREATE TABLE reference_queries (
    query_id INTEGER PRIMARY KEY,
    query_key TEXT NOT NULL UNIQUE CHECK (length(query_key) BETWEEN 1 AND 100),
    query_text TEXT NOT NULL CHECK (length(query_text) BETWEEN 1 AND 4096),
    search_mode TEXT NOT NULL CHECK (
        search_mode IN ('word', 'endword', 'keyword', 'cross', 'exact')
    ),
    ordinal INTEGER NOT NULL UNIQUE CHECK (ordinal >= 0),
    expected_presence INTEGER CHECK (expected_presence IS NULL OR expected_presence IN (0, 1)),
    UNIQUE (query_text, search_mode)
) STRICT;

CREATE TABLE reference_query_results (
    query_result_id INTEGER PRIMARY KEY,
    query_id INTEGER NOT NULL,
    subbook_id INTEGER NOT NULL,
    rank INTEGER NOT NULL CHECK (rank > 0),
    heading TEXT NOT NULL CHECK (length(heading) BETWEEN 1 AND 4096),
    entry_locator TEXT NOT NULL CHECK (length(entry_locator) BETWEEN 1 AND 4096),
    FOREIGN KEY (query_id) REFERENCES reference_queries(query_id) ON DELETE CASCADE,
    FOREIGN KEY (subbook_id) REFERENCES reference_subbooks(subbook_id) ON DELETE CASCADE,
    UNIQUE (query_id, subbook_id, rank),
    UNIQUE (query_id, subbook_id, entry_locator)
) STRICT;

CREATE TABLE reference_entries (
    entry_id INTEGER PRIMARY KEY,
    subbook_id INTEGER NOT NULL,
    entry_locator TEXT NOT NULL CHECK (length(entry_locator) BETWEEN 1 AND 4096),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 4096),
    body_excerpt TEXT,
    body_sha256 TEXT CHECK (body_sha256 IS NULL OR length(body_sha256) = 64),
    body_byte_count INTEGER CHECK (body_byte_count IS NULL OR body_byte_count >= 0),
    internal_link_count INTEGER CHECK (
        internal_link_count IS NULL OR internal_link_count >= 0
    ),
    image_count INTEGER CHECK (image_count IS NULL OR image_count >= 0),
    gaiji_count INTEGER CHECK (gaiji_count IS NULL OR gaiji_count >= 0),
    FOREIGN KEY (subbook_id) REFERENCES reference_subbooks(subbook_id) ON DELETE CASCADE,
    UNIQUE (subbook_id, entry_locator)
) STRICT;

CREATE TABLE reference_metrics (
    metric_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    subbook_id INTEGER,
    metric_name TEXT NOT NULL CHECK (length(metric_name) BETWEEN 1 AND 255),
    integer_value INTEGER,
    real_value REAL,
    text_value TEXT,
    unit TEXT CHECK (unit IS NULL OR length(unit) BETWEEN 1 AND 100),
    FOREIGN KEY (book_id) REFERENCES reference_books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (subbook_id, book_id)
        REFERENCES reference_subbooks(subbook_id, book_id) ON DELETE CASCADE,
    CHECK (
        (integer_value IS NOT NULL) +
        (real_value IS NOT NULL) +
        (text_value IS NOT NULL) = 1
    ),
    UNIQUE (book_id, subbook_id, metric_name)
) STRICT;

CREATE TABLE reference_diagnostics (
    diagnostic_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    subbook_id INTEGER,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'fatal')),
    code TEXT NOT NULL CHECK (length(code) BETWEEN 1 AND 100),
    message TEXT NOT NULL CHECK (length(message) BETWEEN 1 AND 16384),
    details_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(details_json)),
    FOREIGN KEY (book_id) REFERENCES reference_books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (subbook_id, book_id)
        REFERENCES reference_subbooks(subbook_id, book_id) ON DELETE CASCADE
) STRICT;

CREATE INDEX reference_query_results_subbook_idx
    ON reference_query_results(subbook_id, query_id, rank);
CREATE INDEX reference_entries_title_idx
    ON reference_entries(subbook_id, title);
CREATE INDEX reference_diagnostics_code_idx
    ON reference_diagnostics(severity, code);
