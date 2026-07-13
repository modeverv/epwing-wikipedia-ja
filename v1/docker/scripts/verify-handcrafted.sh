#!/bin/sh
set -eu

readonly archive=/output/wikiepwing-handcrafted-epwing.zip
readonly extract=/data/handcrafted-verify

test -f "$archive"
rm -rf "$extract"
mkdir -p "$extract"
python -m zipfile --extract "$archive" "$extract"
test -f "$extract/CATALOGS"
test -f "$extract/TOOLCHAIN.json"
test -f "$extract/WIKIEP/DATA/HONMON.ebz"
grep -F '"version":"1.5"' "$extract/TOOLCHAIN.json"
grep -F '"version":"4.4.3"' "$extract/TOOLCHAIN.json"
ebzipinfo "$extract" > "$extract/ebzipinfo.txt"
ebinfo "$extract" > "$extract/ebinfo.txt"
grep -F "the number of subbooks: 1" "$extract/ebinfo.txt"
grep -F "directory: wikiep" "$extract/ebinfo.txt"
