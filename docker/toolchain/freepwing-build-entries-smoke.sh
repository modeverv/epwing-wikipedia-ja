#!/bin/sh
# End-to-end smoke test for the generic FreePWING entry builder (TASK-H009):
# generates a variable-shaped entries.jsonl via the real Python writer
# (wikiepwing.render.freepwing_source.write_entries_jsonl_stream), then drives
# freepwing_build_entries.pl inside the toolchain image to build a real
# fpwmake source tree, unlike the fixed 3-entry/2-alias handcrafted smoke
# test.
set -eu

image=${1:-wikiepwing-toolchain:dev}
script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
repo_root=$(CDPATH= cd "$script_directory/../.." && pwd)
fixture_directory="$repo_root/tests/fixtures/handcrafted"
work_directory=$(mktemp -d)
trap 'rm -rf "$work_directory"' EXIT HUP INT TERM

cd "$repo_root"
uv run python3 - "$work_directory/entries.jsonl" <<'PYEOF'
import sys
from pathlib import Path

from wikiepwing.render.freepwing_source import write_entries_jsonl_stream
from wikiepwing.render.rendered_entry import RenderedEntry
from wikiepwing.render.render_node import GraphicRenderNode, LinkRenderNode, TextRenderNode

entries = (
    RenderedEntry(
        entry_id="pone",
        page_id=1,
        title="Entry One",
        headwords=("Entry One",),
        body=(
            TextRenderNode(text="Body of entry one. See "),
            LinkRenderNode(label="Entry Two", target="ptwo"),
            TextRenderNode(text=" and "),
            LinkRenderNode(label="Entry Three", target="pthree"),
            TextRenderNode(text=".\n"),
            GraphicRenderNode(name="wiki-mark"),
        ),
        internal_targets=("ptwo", "pthree"),
        graphics=("wiki-mark",),
        estimated_size=0,
        diagnostics=(),
    ),
    RenderedEntry(
        entry_id="ptwo",
        page_id=2,
        title="Entry Two",
        headwords=("Entry Two", "Alias A", "Alias B", "Alias C", "‐"),
        body=(
            TextRenderNode(text="Body of entry two. See "),
            LinkRenderNode(label="Entry One", target="pone"),
            TextRenderNode(text=".\nSecond line."),
        ),
        internal_targets=("pone",),
        graphics=(),
        estimated_size=0,
        diagnostics=(),
    ),
    RenderedEntry(
        entry_id="pthree",
        page_id=3,
        title="Entry Three",
        headwords=("Entry Three", "Alias A"),
        body=(),
        internal_targets=(),
        graphics=(),
        estimated_size=0,
        diagnostics=(),
    ),
    RenderedEntry(
        entry_id="pjapan",
        page_id=4,
        title="日本",
        heading="日本〔にほんこく〕",
        headwords=("日本", "Japan", "日 本"),
        body=(TextRenderNode(text="日本の本文。"),),
        internal_targets=(),
        graphics=(),
        estimated_size=0,
        diagnostics=(),
    ),
    RenderedEntry(
        entry_id="pjapanalbum",
        page_id=5,
        title="日本 (アルバム)",
        heading="日本 (アルバム)〔にほん〕",
        headwords=("日本 (アルバム)", "日本", "にほん"),
        body=(TextRenderNode(text="アルバムの本文。"),),
        internal_targets=(),
        graphics=(),
        estimated_size=0,
        diagnostics=(),
    ),
    RenderedEntry(
        entry_id="pjapanpaper",
        page_id=6,
        title="日本 (新聞)",
        heading="日本 (新聞)〔にっぽん〕",
        headwords=("日本 (新聞)", "日本", "にっぽん"),
        body=(TextRenderNode(text="新聞の本文。"),),
        internal_targets=(),
        graphics=(),
        estimated_size=0,
        diagnostics=(),
    ),
)
write_entries_jsonl_stream(lambda: entries, Path(sys.argv[1]))

PYEOF

cd "$repo_root"
docker run --rm \
    --volume "$fixture_directory:/fixture:ro" \
    --volume "$script_directory/freepwing_build_entries.pl:/fixture-script/freepwing_build_entries.pl:ro" \
    --volume "$work_directory:/entries-input:ro" \
    --entrypoint sh "$image" -c '
        set -eu
        work=/tmp/freepwing-build-entries
        rm -rf "$work"
        mkdir -p "$work/source"

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
        fpwmake 2> "$work/build.stderr" \
            || { cat "$work/build.stderr" >&2; exit 1; }
        grep -q "headwords duplicated count=3" "$work/build.stderr"
        grep -q "headwords skipped reason=word-is-empty count=1" "$work/build.stderr"
        fpwmake catalogs
        test -s work/cgr
        test -s honmon

        stage=$work/stage
        mkdir -p "$stage/WIKIEP/DATA" "$stage/WIKIEP/GAIJI"
        cp catalogs "$stage/CATALOGS"
        cp honmon "$stage/WIKIEP/DATA/HONMON"
        cp gai16h "$stage/WIKIEP/GAIJI/GA16HALF"
        cp gai16f "$stage/WIKIEP/GAIJI/GA16FULL"

        # Real content checks, not just non-crash: the title of the
        # single-alias entry, and an alias of the multi-alias entry, must
        # both be found -- and the alias search must resolve to its own
        # entry (a different result than the direct title search), proving
        # the variable alias/target counts were genuinely processed rather
        # than silently dropped.
        /opt/eb/bin/ebinfo "$stage" >&2
        title_hit=$(/opt/eb/bin/wikiepwing-eb-search "$stage" word "Entry One" 5)
        printf "%s\n" "$title_hit" | grep -q "^R" \
            || { echo "FAIL: no hit for title Entry One" >&2; exit 1; }
        alias_hit=$(/opt/eb/bin/wikiepwing-eb-search "$stage" word "Alias A" 5)
        printf "%s\n" "$alias_hit" | grep -q "^R" \
            || { echo "FAIL: no hit for alias Alias A" >&2; exit 1; }
        [ "$(printf "%s\n" "$alias_hit" | grep -c "^R")" -eq 2 ] \
            || { echo "FAIL: shared alias did not resolve to both entries" >&2; exit 1; }
        title_heading=$(printf "%s\n" "$title_hit" | awk -F"\t" "/^R/{print \$4; exit}")
        alias_heading=$(printf "%s\n" "$alias_hit" | awk -F"\t" "/^R/{print \$4; exit}")
        [ "$title_heading" != "$alias_heading" ] \
            || { echo "FAIL: alias resolved to the same heading as an unrelated title" >&2; exit 1; }

        # Lookup plain input uses EB exactword. The shared base headword
        # must therefore resolve to distinct article positions/headings,
        # while a space-normalized duplicate in the same entry ("日 本") must
        # not add a fourth hit.
        japan_exact=$(/opt/eb/bin/wikiepwing-eb-search "$stage" exact "日本" 10)
        [ "$(printf "%s\n" "$japan_exact" | grep -c "^R")" -eq 3 ] \
            || { echo "FAIL: exact 日本 did not return three distinct articles" >&2; printf "%s\n" "$japan_exact" >&2; exit 1; }
        [ "$(printf "%s\n" "$japan_exact" | grep "^R" | cut -f7,8 | sort -u | wc -l | tr -d " ")" -eq 3 ] \
            || { echo "FAIL: exact 日本 contains duplicate text positions" >&2; exit 1; }
        for expected in "日本〔にほんこく〕" "日本 (アルバム)〔にほん〕" "日本 (新聞)〔にっぽん〕"; do
            expected_hex=$(printf "%s" "$expected" | iconv -f UTF-8 -t EUC-JP | od -An -tx1 | tr -d " \n")
            printf "%s\n" "$japan_exact" | grep -q "$expected_hex" \
                || { echo "FAIL: missing reading heading $expected" >&2; exit 1; }
        done

        echo "OK: honmon built and searchable for a variable-shaped 6-entry set" \
            "(title + multi-alias headwords both resolve correctly)"
    '
