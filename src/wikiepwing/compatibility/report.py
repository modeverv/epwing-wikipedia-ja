"""Compatibility report generation (TASK-Q009, COMPATIBILITY.md 13).

`build_compatibility_report` assembles TASK-Q007's `ComparisonSummary`
and TASK-Q008's `ThresholdEvaluation` into COMPATIBILITY.md 13's JSON
report shape. The schema's `articles` (per-article comparison) and
`viewers` (manual viewer testing) sections, and `queries.redirect_coverage`
(a per-query-class breakdown), are deliberately omitted rather than
filled with fabricated zeros: no engine in this project computes them
yet, and a `0` in a report reads as "measured zero", not "not measured".

`write_compatibility_report` writes the JSON payload plus a companion
HTML rendering, atomically (`wikiepwing.pipeline.atomic_write`), mirroring
`reference/report.py`'s JSON+HTML output pattern for the reference-only
report.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from wikiepwing.compatibility.comparison import ThresholdEvaluation
from wikiepwing.pipeline.atomic_write import atomic_write_text

REPORT_SCHEMA_VERSION = 1


def build_compatibility_report(
    *,
    reference_name: str,
    reference_fingerprint: str,
    candidate_profile: str,
    candidate_artifact_hash: str,
    evaluation: ThresholdEvaluation,
) -> dict[str, object]:
    """Return COMPATIBILITY.md 13's JSON report payload for `evaluation`."""
    summary = evaluation.summary
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "reference": {"name": reference_name, "fingerprint": reference_fingerprint},
        "candidate": {"profile": candidate_profile, "artifact_hash": candidate_artifact_hash},
        "queries": {
            "total": summary.total,
            "target_coverage": summary.target_coverage,
            "false_positive_count": summary.false_positive_count,
            "overlap_at_n_mean": summary.overlap_at_n_mean,
            "rank_agreement_at_n_mean": summary.rank_agreement_at_n_mean,
        },
        "thresholds": {
            "min_target_coverage": evaluation.config.min_target_coverage,
            "max_false_positives": evaluation.config.max_false_positives,
        },
        "status": evaluation.status,
    }


def write_compatibility_report(
    payload: dict[str, object], output_directory: Path
) -> tuple[Path, Path]:
    """Write `payload` as JSON and HTML atomically into `output_directory`."""
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "compatibility-report.json"
    html_path = output_directory / "compatibility-report.html"

    atomic_write_text(
        json_path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    atomic_write_text(html_path, _render_html(payload))
    return json_path, html_path


def _render_html(payload: dict[str, object]) -> str:
    queries = payload["queries"]
    thresholds = payload["thresholds"]
    reference = payload["reference"]
    candidate = payload["candidate"]
    assert isinstance(queries, dict)
    assert isinstance(thresholds, dict)
    assert isinstance(reference, dict)
    assert isinstance(candidate, dict)
    status = str(payload["status"])
    status_class = "pass" if status == "pass" else "fail"

    overlap = queries["overlap_at_n_mean"]
    overlap_text = f"{overlap:.3f}" if overlap is not None else "n/a"
    rank_agreement = queries["rank_agreement_at_n_mean"]
    rank_agreement_text = f"{rank_agreement:.3f}" if rank_agreement is not None else "n/a"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Compatibility report</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
.status-pass {{ color: #0a7a2c; font-weight: bold; }}
.status-fail {{ color: #b00020; font-weight: bold; }}
table {{ border-collapse: collapse; }}
td, th {{ border: 1px solid #ccc; padding: 0.25rem 0.5rem; text-align: left; }}
</style>
</head>
<body>
<h1>Compatibility report</h1>
<p>Status: <span class="status-{status_class}">{_escape(status)}</span></p>
<h2>Reference</h2>
<table>
<tr><th>name</th><td>{_escape(reference["name"])}</td></tr>
<tr><th>fingerprint</th><td>{_escape(reference["fingerprint"])}</td></tr>
</table>
<h2>Candidate</h2>
<table>
<tr><th>profile</th><td>{_escape(candidate["profile"])}</td></tr>
<tr><th>artifact_hash</th><td>{_escape(candidate["artifact_hash"])}</td></tr>
</table>
<h2>Queries</h2>
<table>
<tr><th>total</th><td>{_escape(queries["total"])}</td></tr>
<tr><th>target_coverage</th><td>{queries["target_coverage"]:.3f}</td></tr>
<tr><th>false_positive_count</th><td>{_escape(queries["false_positive_count"])}</td></tr>
<tr><th>overlap_at_n_mean</th><td>{overlap_text}</td></tr>
<tr><th>rank_agreement_at_n_mean</th><td>{rank_agreement_text}</td></tr>
</table>
<h2>Thresholds</h2>
<table>
<tr><th>min_target_coverage</th><td>{thresholds["min_target_coverage"]:.3f}</td></tr>
<tr><th>max_false_positives</th><td>{_escape(thresholds["max_false_positives"])}</td></tr>
</table>
</body>
</html>
"""


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)
