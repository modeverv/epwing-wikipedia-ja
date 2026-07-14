PRAGMA application_id = 1195461193;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 100),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE gaiji_registry (
    gaiji_id INTEGER PRIMARY KEY,
    unicode_sequence TEXT NOT NULL CHECK (length(unicode_sequence) BETWEEN 1 AND 64),
    normalized_sequence TEXT NOT NULL UNIQUE CHECK (length(normalized_sequence) BETWEEN 1 AND 64),
    width_class TEXT NOT NULL CHECK (width_class IN ('half', 'full')),
    font_source_identifier TEXT NOT NULL CHECK (length(font_source_identifier) BETWEEN 1 AND 200),
    bitmap_hash TEXT CHECK (bitmap_hash IS NULL OR length(bitmap_hash) = 64),
    assigned_gaiji_code TEXT CHECK (
        assigned_gaiji_code IS NULL OR length(assigned_gaiji_code) BETWEEN 1 AND 20
    ),
    usage_count INTEGER NOT NULL DEFAULT 0 CHECK (usage_count >= 0)
) STRICT;
