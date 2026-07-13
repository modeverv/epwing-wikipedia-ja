CREATE TABLE reference_query_results_new (
    query_result_id INTEGER PRIMARY KEY,
    query_id INTEGER NOT NULL,
    subbook_id INTEGER NOT NULL,
    rank INTEGER NOT NULL CHECK (rank > 0),
    heading TEXT NOT NULL CHECK (length(heading) BETWEEN 1 AND 4096),
    entry_locator TEXT NOT NULL CHECK (length(entry_locator) BETWEEN 1 AND 4096),
    FOREIGN KEY (query_id) REFERENCES reference_queries(query_id) ON DELETE CASCADE,
    FOREIGN KEY (subbook_id) REFERENCES reference_subbooks(subbook_id) ON DELETE CASCADE,
    UNIQUE (query_id, subbook_id, rank)
) STRICT;

INSERT INTO reference_query_results_new (
    query_result_id,
    query_id,
    subbook_id,
    rank,
    heading,
    entry_locator
)
SELECT
    query_result_id,
    query_id,
    subbook_id,
    rank,
    heading,
    entry_locator
FROM reference_query_results
ORDER BY query_result_id;

DROP TABLE reference_query_results;
ALTER TABLE reference_query_results_new RENAME TO reference_query_results;

CREATE INDEX reference_query_results_subbook_idx
    ON reference_query_results(subbook_id, query_id, rank);
