"""EPWING generate command: model.sqlite3 -> RenderedEntry -> entries.jsonl (TASK-H010).

Mirrors `wikiepwing.ingest.orchestrate`/`wikiepwing.normalize.orchestrate`'s
manifest lifecycle (running/complete/failed, `--force`) for the generate
stage. This produces the FreePWING build input
(`wikiepwing.render.freepwing_source.write_entries_jsonl`, which also
resolves gaiji per ARCHITECTURE.md 17.2's "graphic/gaiji登録"
responsibility and GAIJI.md) plus, when `gaiji_dir` is given, the matching
gaiji build directory (XBM bitmaps + halfchars.txt/fullchars.txt) that
`docker/toolchain/build-epwing.sh`'s `GAIJI_DIR` argument expects. Actually
invoking `fpwmake` to build and package the EPWING binary is a later task
(it needs catalog/subbook generation that doesn't exist yet --
ARCHITECTURE.md 17.2's "catalog/subbook設定" responsibility).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from wikiepwing.gaiji.database import connect_gaiji_database, initialize_gaiji_database
from wikiepwing.gaiji.embedding import GaijiPlan
from wikiepwing.gaiji.freepwing_gaiji import GaijiBuildEntry, write_gaiji_build_files
from wikiepwing.gaiji.glyph_renderer import bitmap_hash, resolve_font_path
from wikiepwing.gaiji.report import build_unicode_report, write_unicode_report
from wikiepwing.gaiji.unrepresentable import UnrepresentableTracker
from wikiepwing.ingest.zstd_codec import decompress
from wikiepwing.model.article import Article
from wikiepwing.model.canonical import decode_article
from wikiepwing.model.database import connect_model_database
from wikiepwing.pipeline.fingerprint import compute_input_fingerprint
from wikiepwing.pipeline.progress import PhaseProgress, fingerprint_progress_callback
from wikiepwing.pipeline.resume import decide_resume
from wikiepwing.pipeline.stage_manifest import StageManifestError, parse_manifest_timestamp
from wikiepwing.pipeline.stage_manifest import extract_status as _extract_manifest_status
from wikiepwing.pipeline.stage_manifest import read_manifest_payload as _read_manifest_payload
from wikiepwing.pipeline.stage_manifest import (
    write_stage_manifest_payload as _write_stage_manifest_payload,
)
from wikiepwing.render.freepwing_source import write_entries_jsonl
from wikiepwing.render.mini_layout import render_article_to_entry
from wikiepwing.render.rendered_entry import RenderedEntry
from wikiepwing.search.backend_mapping import headwords_for_articles
from wikiepwing.source.checksums import compute_fingerprint

SCHEMA_VERSION = 1
STAGE_NAME = "50-generate"
STAGE_VERSION = 1
DEFAULT_GAIJI_FONT_IDENTIFIER = "unknown"


class GenerateError(RuntimeError):
    """Raised when a generate run cannot complete safely."""


@dataclass(slots=True)
class GenerateMetrics:
    """Running counters matching the stage manifest's `metrics` object."""

    articles_read: int = 0
    entries_written: int = 0
    articles_skipped: int = 0

    def payload(self) -> dict[str, object]:
        """Return this counter set as a JSON-serializable mapping."""
        return {
            "articles_read": self.articles_read,
            "entries_written": self.entries_written,
            "articles_skipped": self.articles_skipped,
        }


@dataclass(frozen=True, slots=True)
class GenerateManifest:
    """A stage manifest for one generate run (DATA_CONTRACTS.md section 3)."""

    schema_version: int
    stage: str
    stage_version: int
    status: str
    run_id: str
    started_at: datetime
    completed_at: datetime | None
    inputs: dict[str, str]
    outputs: tuple[dict[str, object], ...]
    metrics: GenerateMetrics
    software: dict[str, str | None]

    def payload(self) -> dict[str, object]:
        """Return this manifest as a JSON-serializable mapping."""
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "stage_version": self.stage_version,
            "status": self.status,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "inputs": self.inputs,
            "outputs": list(self.outputs),
            "metrics": self.metrics.payload(),
            "software": self.software,
        }


@dataclass(frozen=True, slots=True)
class GenerateResult:
    """What one generate run produced."""

    manifest: GenerateManifest
    manifest_path: Path
    entries_path: Path


def read_manifest_status(manifest_path: Path) -> str | None:
    """Return a manifest's `status` field, or None if no manifest exists yet."""
    try:
        payload = _read_manifest_payload(manifest_path)
    except StageManifestError as error:
        raise GenerateError(str(error)) from error
    if payload is None:
        return None
    try:
        return _extract_manifest_status(payload, manifest_path)
    except StageManifestError as error:
        raise GenerateError(str(error)) from error


def run_generate(
    *,
    model_database_path: Path,
    entries_path: Path,
    manifest_path: Path,
    run_id: str,
    git_commit: str | None = None,
    force: bool = False,
    on_progress: Callable[[GenerateMetrics], None] | None = None,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
    gaiji_dir: Path | None = None,
    gaiji_database_path: Path | None = None,
    gaiji_migrations_path: Path | None = None,
    unicode_report_path: Path | None = None,
    font_path: Path | None = None,
    font_identifier: str = DEFAULT_GAIJI_FONT_IDENTIFIER,
) -> GenerateResult:
    """Render every non-rejected model article into entries.jsonl.

    If the previous manifest at `manifest_path` shows status "complete" with
    a matching `stage_version` and matching input fingerprints, this stage is
    skipped entirely and the previous manifest is returned as-is (TASK-I005's
    `decide_resume`). Pass `force=True` to always rerun.

    When `gaiji_dir` is given, every gaiji candidate character found while
    writing entries.jsonl also gets its bitmap rendered there (XBM files +
    halfchars.txt/fullchars.txt, ready for `docker/toolchain/build-epwing.sh`'s
    `GAIJI_DIR` argument); `gaiji_database_path` additionally persists the
    ARCHITECTURE.md 18.3 registry (recreated fresh each run: gaiji code
    assignment depends on the *whole* corpus, DATA_CONTRACTS.md 10, so a
    registry from a previous, different corpus is not meaningful to carry
    forward), and `unicode_report_path` writes the category-D/fallback
    character occurrence report (ARCHITECTURE.md 18.5).
    """
    previous_status = read_manifest_status(manifest_path)
    if previous_status == "running" and not force:
        raise GenerateError(
            f"manifest {manifest_path} shows a previous run still 'running'; "
            "pass force=True to proceed after confirming that run is dead"
        )
    if not force:
        previous_payload = _read_manifest_payload(manifest_path)
        decision = decide_resume(
            previous_payload,
            stage_version=STAGE_VERSION,
            current_inputs=_manifest_inputs(
                model_database_path, on_phase_progress=on_phase_progress
            ),
            current_output_fingerprint=_current_output_fingerprint(
                entries_path, on_phase_progress=on_phase_progress
            ),
        )
        if decision.should_skip:
            assert previous_payload is not None
            return _resume_result(previous_payload, manifest_path, entries_path)
    started_at = datetime.now(UTC)

    metrics = GenerateMetrics()
    _write_manifest(
        _build_manifest(
            status="running",
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            model_database_path=model_database_path,
            entries_path=None,
            metrics=metrics,
            git_commit=git_commit,
            on_phase_progress=on_phase_progress,
        ),
        manifest_path,
    )

    status = "failed"
    try:
        connection = connect_model_database(model_database_path)
        try:
            entries = _render_all(
                connection,
                metrics=metrics,
                on_progress=on_progress,
                on_phase_progress=on_phase_progress,
            )
        finally:
            connection.close()
        tracker = UnrepresentableTracker()
        plan = write_entries_jsonl(
            entries, entries_path, tracker=tracker, on_progress=on_phase_progress
        )
        if gaiji_dir is not None:
            _write_gaiji_build_directory(
                plan,
                gaiji_dir,
                font_path=font_path,
                on_phase_progress=on_phase_progress,
            )
        if gaiji_database_path is not None:
            _write_gaiji_registry(
                plan,
                database_path=gaiji_database_path,
                migrations_path=gaiji_migrations_path,
                gaiji_dir=gaiji_dir,
                font_identifier=font_identifier,
                on_phase_progress=on_phase_progress,
            )
        if unicode_report_path is not None:
            _report_phase(on_phase_progress, "generate-unicode-report", 0, 1)
            write_unicode_report(build_unicode_report(tracker), unicode_report_path)
            _report_phase(on_phase_progress, "generate-unicode-report", 1, 1)
        status = "complete"
    finally:
        manifest = _build_manifest(
            status=status,
            run_id=run_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            model_database_path=model_database_path,
            entries_path=entries_path if status == "complete" else None,
            metrics=metrics,
            git_commit=git_commit,
            on_phase_progress=on_phase_progress,
        )
        _write_manifest(manifest, manifest_path)

    return GenerateResult(manifest=manifest, manifest_path=manifest_path, entries_path=entries_path)


def _write_gaiji_build_directory(
    plan: GaijiPlan,
    gaiji_dir: Path,
    *,
    font_path: Path | None,
    on_phase_progress: Callable[[PhaseProgress], None] | None,
) -> None:
    build_entries: list[GaijiBuildEntry] = []
    if not plan.is_empty():
        resolved_font_path = resolve_font_path(font_path=font_path)
        if resolved_font_path is None:
            raise GenerateError(
                f"{len(plan.assigned_codes)} gaiji character(s) need a bitmap font to render, "
                "but no CJK font was found (pass font_path or install one)"
            )
        build_entries = [
            GaijiBuildEntry(
                sequence=character,
                assigned_code=code,
                width_class=cast(Literal["narrow", "wide"], plan.width_classes[character]),
                font_path=resolved_font_path,
            )
            for character, code in plan.assigned_codes.items()
        ]
    if not build_entries:
        _report_phase(on_phase_progress, "generate-gaiji-bitmaps", 0, 0)
    write_gaiji_build_files(
        build_entries,
        gaiji_dir,
        on_progress=(
            None
            if on_phase_progress is None
            else lambda completed, total: _report_phase(
                on_phase_progress, "generate-gaiji-bitmaps", completed, total
            )
        ),
    )


def _write_gaiji_registry(
    plan: GaijiPlan,
    *,
    database_path: Path,
    migrations_path: Path | None,
    gaiji_dir: Path | None,
    font_identifier: str,
    on_phase_progress: Callable[[PhaseProgress], None] | None,
) -> None:
    # Gaiji code assignment depends on the whole corpus (DATA_CONTRACTS.md
    # 10); a registry left over from a previous, different corpus is stale
    # and would silently mix assigned_code values from two unrelated builds,
    # so this is always recreated from scratch rather than updated in place.
    if database_path.is_file():
        database_path.unlink()
    initialize_gaiji_database(database_path, migrations_path)
    if plan.is_empty():
        _report_phase(on_phase_progress, "generate-gaiji-registry", 0, 0)
        return
    if gaiji_dir is None:
        raise GenerateError("gaiji_database_path requires gaiji_dir to locate bitmap files")
    with connect_gaiji_database(database_path) as connection:
        total = len(plan.assigned_codes)
        for index, (character, code) in enumerate(plan.assigned_codes.items(), start=1):
            bitmap_path = gaiji_dir / f"{code}.xbm"
            connection.execute(
                "INSERT INTO gaiji (sequence, normalized_sequence, width_class, assigned_code, "
                "bitmap_path, bitmap_sha256, font_identifier, usage_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    character,
                    character,
                    plan.width_classes[character],
                    code,
                    str(bitmap_path),
                    bitmap_hash(bitmap_path.read_bytes()),
                    font_identifier,
                    plan.usage_counts[character],
                ),
            )
            _report_phase(on_phase_progress, "generate-gaiji-registry", index, total)
        connection.commit()


def _render_all(
    connection: sqlite3.Connection,
    *,
    metrics: GenerateMetrics,
    on_progress: Callable[[GenerateMetrics], None] | None,
    on_phase_progress: Callable[[PhaseProgress], None] | None,
) -> tuple[RenderedEntry, ...]:
    _report_phase(on_phase_progress, "generate-model-load", 0, 1)
    rows = connection.execute(
        "SELECT page_id, article_json_zstd, normalize_status FROM articles ORDER BY page_id"
    ).fetchall()
    _report_phase(on_phase_progress, "generate-model-load", 1, 1)
    articles: list[Article] = []
    if not rows:
        _report_phase(on_phase_progress, "generate-model-decode", 0, 0)
    for index, row in enumerate(rows, start=1):
        metrics.articles_read += 1
        if row["normalize_status"] == "rejected":
            metrics.articles_skipped += 1
            continue
        canonical_json = decompress(row["article_json_zstd"])
        articles.append(decode_article(canonical_json))
        _report_phase(on_phase_progress, "generate-model-decode", index, len(rows))

    # Headwords are resolved across every article at once (TASK-J007) so a
    # SearchTerm collision between two different articles' variants is
    # settled globally, not article-by-article.
    if not articles:
        _report_phase(on_phase_progress, "generate-headwords-terms", 0, 0)
        _report_phase(on_phase_progress, "generate-headwords-group", 0, 0)
    headwords_by_page_id = headwords_for_articles(
        articles,
        on_progress=(
            None
            if on_phase_progress is None
            else lambda phase, completed, total: _report_phase(
                on_phase_progress, f"generate-headwords-{phase}", completed, total
            )
        ),
    )

    entries: list[RenderedEntry] = []
    for article in articles:
        entries.append(
            render_article_to_entry(article, headwords=headwords_by_page_id[article.page_id])
        )
        metrics.entries_written += 1
        if on_progress is not None:
            on_progress(metrics)
    return tuple(entries)


def _current_output_fingerprint(
    path: Path, *, on_phase_progress: Callable[[PhaseProgress], None] | None
) -> tuple[int, str] | None:
    if not path.is_file():
        return None
    fingerprint = compute_fingerprint(
        path,
        on_progress=fingerprint_progress_callback(
            on_phase_progress, "generate-resume-output-fingerprint"
        ),
    )
    return (fingerprint.size_bytes, fingerprint.sha256)


def _resume_result(
    previous_payload: dict[str, object], manifest_path: Path, entries_path: Path
) -> GenerateResult:
    metrics = GenerateMetrics(**cast(dict[str, int], previous_payload["metrics"]))
    manifest = GenerateManifest(
        schema_version=cast(int, previous_payload["schema_version"]),
        stage=STAGE_NAME,
        stage_version=cast(int, previous_payload["stage_version"]),
        status=cast(str, previous_payload["status"]),
        run_id=cast(str, previous_payload["run_id"]),
        started_at=cast(datetime, parse_manifest_timestamp(previous_payload["started_at"])),
        completed_at=parse_manifest_timestamp(previous_payload["completed_at"]),
        inputs=cast(dict[str, str], previous_payload["inputs"]),
        outputs=tuple(cast(list[dict[str, object]], previous_payload["outputs"])),
        metrics=metrics,
        software=cast(dict[str, str | None], previous_payload["software"]),
    )
    return GenerateResult(manifest=manifest, manifest_path=manifest_path, entries_path=entries_path)


def _manifest_inputs(
    model_database_path: Path,
    *,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
) -> dict[str, str]:
    inputs = {"model_database_path": str(model_database_path)}
    if model_database_path.is_file():
        inputs["model_database_fingerprint"] = compute_input_fingerprint(
            model_database_path,
            on_progress=fingerprint_progress_callback(
                on_phase_progress, "generate-input-fingerprint"
            ),
        )
    return inputs


def _build_manifest(
    *,
    status: str,
    run_id: str,
    started_at: datetime,
    completed_at: datetime | None,
    model_database_path: Path,
    entries_path: Path | None,
    metrics: GenerateMetrics,
    git_commit: str | None,
    on_phase_progress: Callable[[PhaseProgress], None] | None = None,
) -> GenerateManifest:
    outputs: tuple[dict[str, object], ...] = ()
    if entries_path is not None and entries_path.is_file():
        fingerprint = compute_fingerprint(
            entries_path,
            on_progress=fingerprint_progress_callback(
                on_phase_progress, "generate-output-fingerprint"
            ),
        )
        outputs = (
            {
                "relative_path": entries_path.name,
                "size_bytes": fingerprint.size_bytes,
                "sha256": fingerprint.sha256,
                "logical_hash": None,
            },
        )
    return GenerateManifest(
        schema_version=SCHEMA_VERSION,
        stage=STAGE_NAME,
        stage_version=STAGE_VERSION,
        status=status,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        inputs=_manifest_inputs(model_database_path, on_phase_progress=on_phase_progress),
        outputs=outputs,
        metrics=metrics,
        software={
            "git_commit": git_commit,
            "app_image_digest": None,
            "toolchain_image_digest": None,
        },
    )


def _write_manifest(manifest: GenerateManifest, destination: Path) -> None:
    _write_stage_manifest_payload(manifest.payload(), destination)


def _report_phase(
    callback: Callable[[PhaseProgress], None] | None,
    phase: str,
    completed: int,
    total: int,
) -> None:
    if callback is not None:
        callback(
            PhaseProgress(
                phase=phase,
                completed=completed,
                total=total,
                unit="items",
                complete=completed >= total,
            )
        )
