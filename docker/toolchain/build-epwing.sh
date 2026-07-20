#!/bin/sh
# Production EPWING build (TASK-T007): drives the same fpwmake pipeline
# TASK-H013's mini-end-to-end-smoke.sh proved at 100-article scale, but
# generalized for any entries.jsonl and any number of graphics/gaiji glyphs
# instead of the fixed handcrafted fixture.
#
# Inputs (all already produced by the real wikiepwing CLI / library
# functions -- this script does not invent new build logic, it only wires
# existing pieces together):
#   - entries.jsonl        `wikiepwing generate`'s output
#   - graphics directory   `write_graphics_build_files` output (*.bmp + cgraphs.txt),
#                           e.g. from image-convert's --graphics-dir. Optional:
#                           omit for a Mini build with images disabled.
#   - gaiji directory       `write_gaiji_build_files` output (*.xbm +
#                           halfchars.txt/fullchars.txt). Optional: omit if
#                           the corpus needed no gaiji substitutes.
#
# Usage:
#   build-epwing.sh IMAGE ENTRIES OUTPUT [GRAPHICS_DIR] [GAIJI_DIR] [TITLE] [SUBBOOK_DIR]
set -eu

image=${1:?usage: build-epwing.sh IMAGE ENTRIES OUTPUT [GRAPHICS_DIR] [GAIJI_DIR] [TITLE] [SUBBOOK_DIR]}
entries=${2:?usage: build-epwing.sh IMAGE ENTRIES OUTPUT [GRAPHICS_DIR] [GAIJI_DIR] [TITLE] [SUBBOOK_DIR]}
output=${3:?usage: build-epwing.sh IMAGE ENTRIES OUTPUT [GRAPHICS_DIR] [GAIJI_DIR] [TITLE] [SUBBOOK_DIR]}
graphics_dir=${4:-}
gaiji_dir=${5:-}
title=${6:-ウィキペディア}
subbook_dir=${7:-WIKIEP}

if [ ! -f "$entries" ]; then
    echo "entries.jsonl not found: $entries" >&2
    exit 1
fi
if [ -n "$graphics_dir" ] && [ ! -d "$graphics_dir" ]; then
    echo "graphics directory not found: $graphics_dir" >&2
    exit 1
fi
if [ -n "$gaiji_dir" ] && [ ! -d "$gaiji_dir" ]; then
    echo "gaiji directory not found: $gaiji_dir" >&2
    exit 1
fi

# `docker run -v` only treats its host side as a bind mount when it looks
# like a path (leading `/`, `./`, or a drive letter); a bare relative
# filename like "entries-mini.jsonl" is instead parsed as a *named volume*,
# silently mounting an empty directory at the container path instead of the
# real file. Resolve every host path passed to `-v` to an absolute path
# before it gets there.
entries=$(CDPATH= cd "$(dirname "$entries")" && pwd)/$(basename "$entries")
if [ -n "$graphics_dir" ]; then
    graphics_dir=$(CDPATH= cd "$graphics_dir" && pwd)
fi
if [ -n "$gaiji_dir" ]; then
    gaiji_dir=$(CDPATH= cd "$gaiji_dir" && pwd)
fi

script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
work_directory=$(mktemp -d)
trap 'rm -rf "$work_directory"' EXIT HUP INT TERM

generated="$work_directory/generated"
empty_graphics="$work_directory/empty-graphics"
empty_gaiji="$work_directory/empty-gaiji"
build_output="$work_directory/build-output"
mkdir -p "$generated" "$empty_graphics" "$empty_gaiji" "$build_output"

: > "$empty_graphics/cgraphs.txt"
: > "$empty_gaiji/halfchars.txt"
: > "$empty_gaiji/fullchars.txt"

cp "$script_directory/freepwing_build_entries.pl" "$generated/"

# FPWPARSERFLAGS points the parser straight at the read-only entries mount:
# fpwutils.mk appends it to the parser command line, and FPWParser's own
# Getopt (pass_through) strips -workdir first, so the parser script sees the
# path as its first plain argument. This avoids copying the (potentially
# multi-GB) entries.jsonl into the container's writable layer first.
cat > "$generated/Makefile" <<EOF
FPWPARSER = ./freepwing_build_entries.pl
FPWPARSERFLAGS = /input/entries.jsonl
CGRAPHS = cgraphs.txt
HALFCHARS = halfchars.txt
FULLCHARS = fullchars.txt
DIR = $subbook_dir

include /opt/freepwing/share/freepwing/fpwutils.mk
EOF

# fpwmake's catalogs.txt is EUC-JP, matching every other FreePWING build
# input this project already produces (see handcrafted-three-entry-smoke.sh
# and mini-end-to-end-smoke.sh's own `iconv --to-code=EUC-JP` step).
cat > "$generated/catalogs.txt.utf8" <<EOF
[Catalog]
FileName = catalogs
Type = EPWING1
Books = 1

[Book]
Title = "$title"
BookType = 6001
Directory = "$subbook_dir"
HanGaiji = "GA16HALF"
ZenGaiji = "GA16FULL"
EOF
iconv --from-code=UTF-8 --to-code=EUC-JP \
    "$generated/catalogs.txt.utf8" > "$generated/catalogs.txt"
rm "$generated/catalogs.txt.utf8"

# WIKIEPWING_PARSE_JOBS (empty = every container CPU) reaches
# freepwing_build_entries.pl's parallel parse workers.
docker run --rm \
    --env WIKIEPWING_PARSE_JOBS="${WIKIEPWING_PARSE_JOBS:-}" \
    --volume "$generated:/generated:ro" \
    --volume "$entries:/input/entries.jsonl:ro" \
    --volume "${graphics_dir:-$empty_graphics}:/input/graphics:ro" \
    --volume "${gaiji_dir:-$empty_gaiji}:/input/gaiji:ro" \
    --volume "$build_output:/build-output" \
    --entrypoint sh "$image" -c '
        set -eu
        phase() { printf "phase=%s state=%s\n" "$1" "$2" >&2; }
        subbook_dir="'"$subbook_dir"'"
        work=/tmp/build-epwing
        stage=$work/stage
        rm -rf "$work"
        mkdir -p "$work/source" "$stage/$subbook_dir/DATA" "$stage/$subbook_dir/GAIJI"

        phase build-input-copy running
        cp /generated/Makefile /generated/catalogs.txt /generated/freepwing_build_entries.pl \
            "$work/source/"
        chmod 0555 "$work/source/freepwing_build_entries.pl"

        cp /input/graphics/cgraphs.txt "$work/source/cgraphs.txt"
        for bmp in /input/graphics/*.bmp; do
            [ -e "$bmp" ] && cp "$bmp" "$work/source/"
        done
        cp /input/gaiji/halfchars.txt "$work/source/halfchars.txt"
        cp /input/gaiji/fullchars.txt "$work/source/fullchars.txt"
        for xbm in /input/gaiji/*.xbm; do
            [ -e "$xbm" ] && cp "$xbm" "$work/source/"
        done
        phase build-input-copy complete

        cd "$work/source"
        phase fpwmake running
        fpwmake
        phase fpwmake complete
        phase fpwmake-catalogs running
        fpwmake catalogs
        phase fpwmake-catalogs complete
        test -s honmon

        phase epwing-stage-copy running
        cp catalogs "$stage/CATALOGS"
        cp honmon "$stage/$subbook_dir/DATA/HONMON"
        if [ -s gai16h ]; then cp gai16h "$stage/$subbook_dir/GAIJI/GA16HALF"; fi
        if [ -s gai16f ]; then cp gai16f "$stage/$subbook_dir/GAIJI/GA16FULL"; fi
        phase epwing-stage-copy complete
        phase ebinfo-stage running
        ebinfo "$stage"
        phase ebinfo-stage complete

        package="$work/package"
        mkdir -p "$package"
        phase ebzip running
        ebzip --level 0 --output-directory "$package" "$stage"
        phase ebzip complete
        phase ebinfo-package running
        ebinfo "$package"
        phase ebinfo-package complete

        phase deterministic-zip running
        find "$package" -exec touch -t 200001010000 {} +
        cd "$package"
        zip -X -q -r /build-output/result.epwing.zip CATALOGS "$subbook_dir"
        phase deterministic-zip complete
    '

mkdir -p "$(dirname "$output")"
echo "phase=output-copy state=running" >&2
cp "$build_output/result.epwing.zip" "$output"
echo "phase=output-copy state=complete" >&2
echo "$output"
