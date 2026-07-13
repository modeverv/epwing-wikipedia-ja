#!/bin/sh
set -eu

image=${1:-wikiepwing-toolchain:dev}
output=${2:-reports/toolchain-capabilities.json}
script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)

sh "$script_directory/handcrafted-three-entry-smoke.sh" "$image" "$output"
python - "$output" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
with path.open(encoding="utf-8") as file:
    report = json.load(file)
expected = {
    "schema_version": 1,
    "eb_library_version": "4.4.3",
    "subbook_count": 1,
    "directory": "wikiep",
    "search_methods": ["word", "endword"],
    "queries": {"Emacs": 1, "Linux": 3, "Wikipedia": 1},
    "text_entries_read": 3,
    "hooks": {"reference": 6, "bmp": 3, "narrow_gaiji": 2, "wide_gaiji": 2},
}
if report != expected:
    raise SystemExit(f"unexpected toolchain capability report: {report!r}")
PY
