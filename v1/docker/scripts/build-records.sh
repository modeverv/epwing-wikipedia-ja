#!/bin/sh
set -eu
readonly records=$1
readonly output=$2
readonly work=/data/records-work
readonly staging=/data/records-staging
rm -rf "$work" "$staging"
mkdir -p "$work" "$staging/WIKIEP/DATA" "$staging/WIKIEP/GAIJI"
cp /workspace/toolchain/records/Makefile /workspace/toolchain/records/build_records.pl /workspace/toolchain/records/catalogs.txt "$work/"
cp "$records" "$work/records.tsv"
PYTHONPATH=/workspace/src python - "$work/records.tsv" "$work/graphics" "${WIKIEPWING_IMAGE_LIMIT:-200}" "${WIKIEPWING_IMAGE_FORCE:-}" <<'PY'
from pathlib import Path
import sys

from wikiepwing.epwing.graphics import materialize_graphics

forced = tuple(item for item in sys.argv[4].split(",") if item)
result = materialize_graphics(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), forced)
print(
    f"IMAGES_REFERENCED={result.references} IMAGES_RESOLVED={result.resolved} "
    f"IMAGES_FAILED={result.failed}"
)
PY
cp -R "$work/graphics/images" "$work/images"
cp "$work/graphics/cgraphs.txt" "$work/cgraphs.txt"
PYTHONPATH=/workspace/src python - "$work/records.tsv" "$work/gaiji" <<'PY'
from pathlib import Path
import sys

from wikiepwing.epwing.gaiji import materialize_gaiji

result = materialize_gaiji(Path(sys.argv[1]), Path(sys.argv[2]))
print(
    f"GAIJI_GENERATED={len(result.names)} GAIJI_REPLACED={result.replacements} "
    f"GAIJI_OVERFLOW={len(result.overflow_names)} "
    f"GAIJI_OVERFLOW_REPLACED={result.overflow_replacements} "
    f"TITLE_UNICODE_ESCAPED={result.title_replacements}"
)
PY
python - "$work/records.tsv" <<'PY'
from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
replaced = 0
unsupported_plane = re.compile(rb"\x8f..")
temporary = source.with_suffix(source.suffix + ".euc")
with source.open("r", encoding="utf-8") as reader, temporary.open("wb") as writer:
    for line in reader:
        encoded = line.encode("euc_jp", errors="replace")
        encoded, plane_replaced = unsupported_plane.subn(b"?", encoded)
        replaced += encoded.count(b"?") - line.count("?") + plane_replaced
        writer.write(encoded)
temporary.replace(source)
print(f"CHARACTER_REPLACED={replaced}", file=sys.stderr)
PY
chmod +x "$work/build_records.pl"
iconv -f UTF-8 -t EUC-JP "$work/catalogs.txt" > "$work/catalogs.euc" && mv "$work/catalogs.euc" "$work/catalogs.txt"
cd "$work" && fpwmake && fpwmake catalogs
cp catalogs "$staging/CATALOGS" && cp honmon "$staging/WIKIEP/DATA/HONMON"
if test -s "$work/gai16f"; then
    cp "$work/gai16f" "$staging/WIKIEP/GAIJI/GAI16F"
fi
if test -s "$work/gaiji-overflow.txt"; then
    cp "$work/gaiji-overflow.txt" "$staging/WIKIEP/GAIJI/OVERFLOW.TXT"
fi
if test -s "$work/graphics/image-report.tsv"; then
    mkdir -p "$staging/WIKIEP/GRAPHIC"
    cp "$work/graphics/image-report.tsv" "$staging/WIKIEP/GRAPHIC/IMAGE-REPORT.TSV"
fi
cd "$staging" && ebzip --force-overwrite . && test -f WIKIEP/DATA/HONMON.ebz
printf '{"schema_version":1}\n' > TOOLCHAIN.json
find CATALOGS TOOLCHAIN.json WIKIEP -exec touch -t 198001010000 {} +
rm -f "$output" && TZ=UTC zip -q -X -D -r "$output" CATALOGS TOOLCHAIN.json WIKIEP
