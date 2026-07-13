"""Deterministic reference inspection reports and manual review checklist."""

from __future__ import annotations

import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from wikiepwing.reference.database import connect_reference_database

REPORT_SCHEMA_VERSION = 1
_OUTPUT_NAMES = (
    "reference-report.json",
    "reference-report.html",
    "reference-manual-checklist.md",
)


class ReferenceReportError(ValueError):
    """Raised when a reference report cannot be safely generated."""


def write_reference_report(database_path: Path, output_directory: Path) -> tuple[Path, Path, Path]:
    """Write deterministic JSON, HTML, and Markdown reference artifacts atomically."""
    database = _validate_database(database_path)
    output = _prepare_output_directory(output_directory)
    destinations = tuple(output / name for name in _OUTPUT_NAMES)
    for destination in destinations:
        if destination.is_symlink():
            raise ReferenceReportError(f"report output must not be a symlink: {destination}")
        if destination.exists() and not destination.is_file():
            raise ReferenceReportError(f"report output must be a regular file: {destination}")

    payload = _load_report(database)
    contents = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        _render_html(payload),
        _render_manual_checklist(payload),
    )
    temporary_paths: list[Path] = []
    try:
        for destination, content in zip(destinations, contents, strict=True):
            temporary_paths.append(_write_temporary(output, destination.name, content))
        for temporary, destination in zip(temporary_paths, destinations, strict=True):
            os.replace(temporary, destination)
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)
    return destinations[0], destinations[1], destinations[2]


def _validate_database(database_path: Path) -> Path:
    source = database_path.expanduser()
    if source.is_symlink():
        raise ReferenceReportError(f"reference database must not be a symlink: {source}")
    try:
        database = source.resolve(strict=True)
    except FileNotFoundError as error:
        raise ReferenceReportError(f"reference database does not exist: {source}") from error
    if not database.is_file():
        raise ReferenceReportError(f"reference database must be a regular file: {database}")
    return database


def _prepare_output_directory(output_directory: Path) -> Path:
    requested = output_directory.expanduser()
    if requested.is_symlink():
        raise ReferenceReportError(f"report directory must not be a symlink: {requested}")
    requested.mkdir(parents=True, exist_ok=True)
    output = requested.resolve(strict=True)
    if not output.is_dir():
        raise ReferenceReportError(f"report output must be a directory: {output}")
    return output


def _load_report(database: Path) -> dict[str, object]:
    with connect_reference_database(database) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ReferenceReportError("reference database failed integrity_check")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ReferenceReportError("reference database failed foreign_key_check")
        books = connection.execute(
            """
            SELECT book_id, source_fingerprint, catalog_path, catalog_size_bytes,
                   inventory_sha256, identifier
            FROM reference_books ORDER BY book_id
            """
        ).fetchall()
        if len(books) != 1:
            raise ReferenceReportError("reference report requires exactly one reference book")
        book = dict(books[0])
        subbooks = [
            dict(row)
            for row in connection.execute(
                """
                SELECT subbook_id, code, title, directory
                FROM reference_subbooks ORDER BY subbook_id
                """
            ).fetchall()
        ]
        queries: list[dict[str, object]] = []
        query_rows = connection.execute(
            """
            SELECT query_id, query_key, query_text, search_mode, ordinal, expected_presence
            FROM reference_queries ORDER BY ordinal
            """
        ).fetchall()
        for query_row in query_rows:
            query = dict(query_row)
            query["results"] = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT r.rank, s.code AS subbook_code, r.heading, r.entry_locator
                    FROM reference_query_results AS r
                    JOIN reference_subbooks AS s ON s.subbook_id = r.subbook_id
                    WHERE r.query_id = ?
                    ORDER BY r.rank, s.subbook_id, r.query_result_id
                    """,
                    (query_row["query_id"],),
                ).fetchall()
            ]
            del query["query_id"]
            queries.append(query)
        entries = [
            dict(row)
            for row in connection.execute(
                """
                SELECT s.code AS subbook_code, e.entry_locator, e.title, e.body_excerpt,
                       e.body_sha256, e.body_byte_count, e.internal_link_count,
                       e.image_count, e.gaiji_count
                FROM reference_entries AS e
                JOIN reference_subbooks AS s ON s.subbook_id = e.subbook_id
                ORDER BY e.entry_id
                """
            ).fetchall()
        ]
        diagnostics: list[dict[str, object]] = []
        for row in connection.execute(
            """
            SELECT d.severity, d.code, d.message, d.details_json,
                   s.code AS subbook_code
            FROM reference_diagnostics AS d
            LEFT JOIN reference_subbooks AS s ON s.subbook_id = d.subbook_id
            ORDER BY d.diagnostic_id
            """
        ).fetchall():
            diagnostic = dict(row)
            diagnostic["details"] = json.loads(diagnostic.pop("details_json"))
            diagnostics.append(diagnostic)
        result_count = connection.execute(
            "SELECT COUNT(query_result_id) FROM reference_query_results"
        ).fetchone()[0]

    book.pop("book_id")
    for subbook in subbooks:
        subbook.pop("subbook_id")
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "book": book,
        "subbooks": subbooks,
        "summary": {
            "subbook_count": len(subbooks),
            "query_count": len(queries),
            "query_result_count": result_count,
            "entry_count": len(entries),
            "diagnostic_count": len(diagnostics),
        },
        "queries": queries,
        "entries": entries,
        "diagnostics": diagnostics,
    }


def _render_html(payload: dict[str, object]) -> str:
    summary = _mapping(payload["summary"])
    book = _mapping(payload["book"])
    subbooks = _list_of_mappings(payload["subbooks"])
    queries = _list_of_mappings(payload["queries"])
    entries = _list_of_mappings(payload["entries"])
    diagnostics = _list_of_mappings(payload["diagnostics"])

    lines = [
        "<!doctype html>",
        '<html lang="ja">',
        '<meta charset="utf-8">',
        "<title>Reference inspection report</title>",
        "<h1>Reference inspection report</h1>",
        f"<p>Identifier: {_escape(book.get('identifier'))}</p>",
        f"<p>Source fingerprint: <code>{_escape(book['source_fingerprint'])}</code></p>",
        "<h2>Summary</h2>",
        "<ul>",
    ]
    for key in (
        "subbook_count",
        "query_count",
        "query_result_count",
        "entry_count",
        "diagnostic_count",
    ):
        lines.append(f"<li>{_escape(key)}: {_escape(summary[key])}</li>")
    lines.extend(("</ul>", "<h2>Subbooks</h2>", "<ul>"))
    for subbook in subbooks:
        lines.append(
            f"<li>{_escape(subbook['code'])}: {_escape(subbook.get('title'))} "
            f"(<code>{_escape(subbook['directory'])}</code>)</li>"
        )
    lines.extend(("</ul>", "<h2>Fixed queries</h2>"))
    for query in queries:
        results = _list_of_mappings(query["results"])
        lines.append(f"<h3>{_escape(query['query_text'])} / {_escape(query['search_mode'])}</h3>")
        lines.append(f"<p>{len(results)} result(s)</p><ol>")
        for result in results:
            lines.append(
                f"<li>{_escape(result['heading'])} "
                f"<code>{_escape(result['entry_locator'])}</code></li>"
            )
        lines.append("</ol>")
    lines.append("<h2>Entry samples</h2>")
    for entry in entries:
        lines.extend(
            (
                f"<h3>{_escape(entry['title'])}</h3>",
                f"<p><code>{_escape(entry['entry_locator'])}</code>; "
                f"body bytes {_escape(entry['body_byte_count'])}; "
                f"links {_escape(entry['internal_link_count'])}; "
                f"images {_escape(entry['image_count'])}; "
                f"gaiji {_escape(entry['gaiji_count'])}</p>",
                f"<pre>{_escape(entry.get('body_excerpt'))}</pre>",
            )
        )
    lines.extend(("<h2>Diagnostics</h2>", "<ul>"))
    for diagnostic in diagnostics:
        lines.append(
            f"<li>{_escape(diagnostic['severity'])} "
            f"<code>{_escape(diagnostic['code'])}</code>: "
            f"{_escape(diagnostic['message'])}</li>"
        )
    lines.extend(("</ul>", "</html>", ""))
    return "\n".join(lines)


def _render_manual_checklist(payload: dict[str, object]) -> str:
    book = _mapping(payload["book"])
    entries = _list_of_mappings(payload["entries"])
    diagnostics = _list_of_mappings(payload["diagnostics"])
    lines = [
        "# Reference dictionary manual checklist",
        "",
        f"Reference source fingerprint: `{book['source_fingerprint']}`",
        "",
        "## Review environment",
        "",
        "- [ ] Viewer name/version: ",
        "- [ ] OS/version: ",
        "- [ ] Artifact SHA-256: ",
        "- [ ] Verified date (YYYY-MM-DD): ",
        "- [ ] Screenshot reference path (optional): ",
        "",
        "## Search behavior",
        "",
        "- [ ] word検索で固定queryの主要entryを選択できる",
        "- [ ] endword検索の結果と順位を確認した",
        "- [ ] 存在しない語が誤ったentryを返さない",
        "",
        "## Entry rendering",
        "",
    ]
    entry_checks = (
        "titleが正常に表示される",
        "leadが読める",
        "headings階層が理解できる",
        "internal linkを選択できる",
        "tableが読める",
        "infoboxが過度に場所を取らない",
        "mathが読める",
        "imageが読める、または欠落が明示される",
        "gaiji・rare characterを識別できる",
        "referencesを利用できる",
    )
    for entry in entries:
        lines.extend(
            (
                f"### {entry['title']} (`{entry['entry_locator']}`)",
                "",
                *(f"- [ ] {check}" for check in entry_checks),
                "- Known issue: ",
                "- Result: PASS / FAIL / NOT APPLICABLE",
                "",
            )
        )
    unresolved = [item for item in diagnostics if item["severity"] in ("warning", "error", "fatal")]
    lines.extend(("## Automated observations requiring attention", ""))
    if unresolved:
        for diagnostic in unresolved:
            lines.append(f"- [ ] `{diagnostic['code']}`: {diagnostic['message']}")
    else:
        lines.append("- [ ] No warning/error/fatal diagnostics were reported")
    lines.extend(("", "## Final decision", "", "- [ ] PASS", "- [ ] FAIL", "- Notes: ", ""))
    return "\n".join(str(line) for line in lines)


def _write_temporary(directory: Path, name: str, content: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{name}.",
        suffix=".tmp",
        dir=directory,
        delete=False,
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReferenceReportError("report payload contains an invalid mapping")
    return value


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ReferenceReportError("report payload contains an invalid mapping list")
    return value


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)
