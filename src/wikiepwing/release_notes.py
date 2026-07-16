"""Human-readable release notes for an update report (TASK-S009, PLAN.md 29).

Renders `source_diff.build_update_report`'s (TASK-S006) machine-readable
payload as Markdown, so an operator can skim what changed between Snapshot
versions without parsing JSON. Reuses that module's diff computation
entirely -- this only formats an already-built report.
"""

from __future__ import annotations


def render_release_notes(report: dict[str, object], *, project: str) -> str:
    """Render an `update-report.json` payload (TASK-S006) as Markdown release notes."""
    diff = report["diff"]
    assert isinstance(diff, dict)
    updated_at = report["updated_at"]
    previous_version = diff["previous_snapshot_version"]
    new_version = diff["new_snapshot_version"]

    lines = [f"# {project} update — {updated_at}", ""]
    if previous_version is None:
        lines.append(f"Initial acquisition of Snapshot version `{new_version}`.")
    elif diff["version_changed"]:
        lines.append(f"Snapshot version changed: `{previous_version}` -> `{new_version}`.")
    else:
        lines.append(f"Snapshot version unchanged: `{new_version}`.")
    lines.append("")

    added = diff["added_chunk_identifiers"]
    removed = diff["removed_chunk_identifiers"]
    changed = diff["changed_chunk_identifiers"]
    assert isinstance(added, list)
    assert isinstance(removed, list)
    assert isinstance(changed, list)
    lines.append(f"- Chunks added: {len(added)}")
    lines.append(f"- Chunks removed: {len(removed)}")
    lines.append(f"- Chunks changed: {len(changed)}")
    lines.append(f"- Chunks unchanged: {diff['unchanged_chunk_count']}")
    lines.append("")

    previous_size = diff["previous_total_size_bytes"]
    new_size = diff["new_total_size_bytes"]
    size_delta = diff["size_delta_bytes"]
    assert isinstance(new_size, int)
    assert isinstance(size_delta, int)
    if previous_size is None:
        lines.append(f"Total size: {_human_size(new_size)}.")
    else:
        assert isinstance(previous_size, int)
        sign = "+" if size_delta >= 0 else ""
        lines.append(
            f"Total size: {_human_size(previous_size)} -> {_human_size(new_size)} "
            f"({sign}{_human_size(size_delta)})."
        )
    lines.append("")
    return "\n".join(lines)


def _human_size(size_bytes: int) -> str:
    magnitude = float(abs(size_bytes))
    sign = "-" if size_bytes < 0 else ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if magnitude < 1024 or unit == "TB":
            if unit == "B":
                return f"{sign}{int(magnitude)} {unit}"
            return f"{sign}{magnitude:.1f} {unit}"
        magnitude /= 1024
    raise AssertionError("unreachable")
