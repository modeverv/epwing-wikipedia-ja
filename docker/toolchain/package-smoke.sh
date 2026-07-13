#!/bin/sh
set -eu

image=${1:-wikiepwing-toolchain:dev}
output=${2:-output/toolchain-smoke.epwing.zip}
script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
temporary_directory=$(mktemp -d)
trap 'rm -rf "$temporary_directory"' EXIT HUP INT TERM

report="$temporary_directory/toolchain-capabilities.json"
sh "$script_directory/handcrafted-three-entry-smoke.sh" \
    "$image" "$report" "$output"
mkdir -p "$temporary_directory/extracted"
python - "$output" "$temporary_directory/extracted" <<'PY'
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

archive_path = Path(sys.argv[1])
destination = Path(sys.argv[2])
expected = {
    "CATALOGS",
    "WIKIEP/DATA/HONMON.ebz",
    "WIKIEP/GAIJI/GA16HALF.ebz",
    "WIKIEP/GAIJI/GA16FULL.ebz",
}
with zipfile.ZipFile(archive_path) as archive:
    files = {info.filename for info in archive.infolist() if not info.is_dir()}
    if files != expected:
        raise SystemExit(f"unexpected ZIP members: {sorted(files)!r}")
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        mode = info.external_attr >> 16
        is_symlink = stat.S_IFMT(mode) == stat.S_IFLNK
        if path.is_absolute() or ".." in path.parts or is_symlink:
            raise SystemExit(f"unsafe ZIP member: {info.filename!r}")
    archive.extractall(destination)
PY
docker run --rm \
    --volume "$temporary_directory/extracted:/book:ro" \
    --entrypoint /opt/eb/bin/wikiepwing-eb-probe "$image" /book \
    > "$temporary_directory/extracted-capabilities.json"
cmp "$report" "$temporary_directory/extracted-capabilities.json"
