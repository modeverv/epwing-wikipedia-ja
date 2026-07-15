#!/bin/sh
# Lite 100-article build (TASK-P005): the 100-article gate from DECISIONS.md
# ADR-015. Runs the real Python pipeline (register-local-source -> ingest ->
# normalize -> generate) over tests/fixtures/enterprise/hundred_articles.ndjson
# (TASK-H012), then drives freepwing_build_entries.pl (TASK-H009) inside the
# toolchain image to build a real honmon from all 100 entries, and verifies
# via wikiepwing-eb-search that multiple distinct titles/aliases resolve
# correctly -- not just that nothing crashed.
set -eu

image=${1:-wikiepwing-toolchain:dev}
script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
repo_root=$(CDPATH= cd "$script_directory/../.." && pwd)
fixture_directory="$repo_root/tests/fixtures/handcrafted"
work_directory=$(mktemp -d)
trap 'rm -rf "$work_directory"' EXIT HUP INT TERM

cd "$repo_root"
uv run python3 - "$work_directory" <<'PYEOF'
import sys
import tarfile
import io
from datetime import UTC, datetime
from pathlib import Path

from wikiepwing.config import load_config
from wikiepwing.ingest.orchestrate import run_ingest
from wikiepwing.ingest.validate import ValidationLimits
from wikiepwing.model.validate import ModelValidationLimits
from wikiepwing.normalize.orchestrate import run_normalize
from wikiepwing.normalize.pipeline import NormalizeOptions
from wikiepwing.render.generate import run_generate
from wikiepwing.render.verify import verify_entries_jsonl
from wikiepwing.source.register import LocalSourceFile, register_local_source

work = Path(sys.argv[1])
fixture = Path("tests/fixtures/enterprise/hundred_articles.ndjson")

downloads = work / "downloads"
downloads.mkdir(parents=True)
chunk_tar = downloads / "chunk_0.tar.gz"
body = fixture.read_bytes()
with tarfile.open(chunk_tar, mode="w:gz") as archive:
    info = tarfile.TarInfo(name="chunk_0.ndjson")
    info.size = len(body)
    archive.addfile(info, io.BytesIO(body))

acquired = register_local_source(
    [LocalSourceFile(source_path=chunk_tar, chunk_identifier="jawiki_namespace_0_chunk_0")],
    project="jawiki",
    namespace=0,
    snapshot_identifier="jawiki_namespace_0",
    snapshot_version="lite-100",
    date_modified=datetime(2026, 7, 14, tzinfo=UTC),
    sources_root=work / "sources",
    acquirer_name="wikiepwing",
    acquirer_version="0.1.0",
    acquirer_git_commit="abc1234",
)

config = load_config(Path("config/default.toml"), [Path("config/profiles/lite.toml")])
validation_limits = ValidationLimits.from_config(config, expected_namespace_id=0)
raw_database_path = work / "raw.sqlite3"
ingest_result = run_ingest(
    acquired.lock,
    snapshot_directory=acquired.snapshot_directory,
    raw_database_path=raw_database_path,
    migrations_path=Path("migrations/raw"),
    manifest_path=work / "manifests" / "30-ingest.json",
    run_id="lite-100-ingest",
    validation_limits=validation_limits,
    git_commit="abc1234",
)
assert ingest_result.manifest.status == "complete", ingest_result.manifest.payload()
assert ingest_result.manifest.metrics.records_written == 100

model_validation_limits = ModelValidationLimits.from_config(config)
normalize_section = config.section("normalize")
normalize_options = NormalizeOptions(
    max_dom_depth=normalize_section["max_dom_depth"],
    html_recover=normalize_section["html_recover"],
    remove_edit_ui=normalize_section["remove_edit_ui"],
    remove_navboxes=normalize_section["remove_navboxes"],
    remove_authority_control=normalize_section["remove_authority_control"],
    images_enabled=config.section("images")["enabled"],
)
model_database_path = work / "model.sqlite3"
normalize_result = run_normalize(
    raw_database_path=raw_database_path,
    model_database_path=model_database_path,
    model_migrations_path=Path("migrations/model"),
    manifest_path=work / "manifests" / "40-normalize.json",
    run_id="lite-100-normalize",
    model_validation_limits=model_validation_limits,
    normalize_options=normalize_options,
    git_commit="abc1234",
)
assert normalize_result.manifest.status == "complete", normalize_result.manifest.payload()
assert normalize_result.manifest.metrics.articles_read == 100

entries_path = work / "entries.jsonl"
generate_result = run_generate(
    model_database_path=model_database_path,
    entries_path=entries_path,
    manifest_path=work / "manifests" / "50-generate.json",
    run_id="lite-100-generate",
    git_commit="abc1234",
)
assert generate_result.manifest.status == "complete", generate_result.manifest.payload()
assert generate_result.manifest.metrics.entries_written == 100

verification = verify_entries_jsonl(entries_path)
assert verification.ok, verification.payload()
print("Python pipeline OK: 100 articles ingested, normalized, generated, verified.")
PYEOF

docker run --rm \
    --volume "$fixture_directory:/fixture:ro" \
    --volume "$script_directory/freepwing_build_entries.pl:/fixture-script/freepwing_build_entries.pl:ro" \
    --volume "$work_directory:/entries-input:ro" \
    --entrypoint sh "$image" -c '
        set -eu
        work=/tmp/lite-100-article
        stage=$work/stage
        rm -rf "$work"
        mkdir -p "$work/source" "$stage/WIKIEP/DATA" "$stage/WIKIEP/GAIJI"

        cp /fixture/Makefile /fixture/cgraphs.txt /fixture/generate_bitmap.pl \
            /fixture/halfchars.txt /fixture/fullchars.txt /fixture/generate_gaiji.pl \
            /fixture-script/freepwing_build_entries.pl "$work/source/"
        cp /entries-input/entries.jsonl "$work/source/entries.jsonl"
        iconv --from-code=UTF-8 --to-code=EUC-JP \
            /fixture/catalogs.txt > "$work/source/catalogs.txt"
        sed -i "s#\./build_fixture\.pl#./freepwing_build_entries.pl#" "$work/source/Makefile"
        chmod 0555 "$work/source/freepwing_build_entries.pl"

        cd "$work/source"
        perl ./generate_bitmap.pl bitmap.bmp
        perl ./generate_gaiji.pl half16.xbm full16.xbm
        fpwmake
        fpwmake catalogs
        test -s work/cgr
        test -s honmon

        cp catalogs "$stage/CATALOGS"
        cp honmon "$stage/WIKIEP/DATA/HONMON"
        cp gai16h "$stage/WIKIEP/GAIJI/GA16HALF"
        cp gai16f "$stage/WIKIEP/GAIJI/GA16FULL"
        ebinfo "$stage"

        # Spot-check several distinct real titles/aliases from the
        # 100-article fixture actually resolve, proving the whole 100-entry
        # dictionary was built correctly, not just that fpwmake did not crash.
        for query in "Emacs" "Linux" "Vim alias" "GNU Project"; do
            hit=$(/opt/eb/bin/wikiepwing-eb-search "$stage" word "$query" 5)
            printf "%s\n" "$hit" | grep -q "^R" \
                || { echo "FAIL: no hit for: $query" >&2; exit 1; }
            echo "OK: found hit for: $query"
        done
        echo "OK: 100-article honmon built and searchable (ADR-015 100-article gate)"
    '
