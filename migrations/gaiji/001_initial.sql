PRAGMA application_id = 1195461193;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 100),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE gaiji (
    sequence TEXT PRIMARY KEY,
    normalized_sequence TEXT NOT NULL CHECK (length(normalized_sequence) BETWEEN 1 AND 64),
    width_class TEXT NOT NULL,
    assigned_code TEXT NOT NULL UNIQUE CHECK (length(assigned_code) BETWEEN 1 AND 20),
    bitmap_path TEXT NOT NULL CHECK (length(bitmap_path) BETWEEN 1 AND 4096),
    bitmap_sha256 TEXT NOT NULL CHECK (length(bitmap_sha256) = 64),
    font_identifier TEXT NOT NULL CHECK (length(font_identifier) BETWEEN 1 AND 200),
    usage_count INTEGER NOT NULL CHECK (usage_count >= 0),
    CHECK (width_class IN ('narrow', 'wide'))
) STRICT;
