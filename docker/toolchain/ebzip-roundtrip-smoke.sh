#!/bin/sh
set -eu

image=${1:-wikiepwing-toolchain:dev}

docker run --rm --entrypoint sh "$image" -c '
    set -eu

    test "$(command -v ebzip)" = /opt/eb/bin/ebzip
    test "$(command -v ebunzip)" = /opt/eb/bin/ebunzip
    test "$(command -v ebzipinfo)" = /opt/eb/bin/ebzipinfo
    ebzip --version | grep -F "ebzip (EB Library) version 4.4.3"

    fixture=/tmp/ebzip-roundtrip
    source=$fixture/source
    compressed=$fixture/compressed
    restored=$fixture/restored
    rm -rf "$fixture"
    mkdir -p "$source/ROUNDTRP/DATA" "$compressed" "$restored"

    # One EPWING subbook record in a 2048-byte CATALOGS sector. ASCII keeps
    # this transport fixture independent of the character tests in TASK-B006.
    perl -e '\''
        my $catalog = chr(0) x 2048;
        substr($catalog, 0, 2) = pack("n", 1);
        substr($catalog, 2, 2) = pack("n", 1);
        substr($catalog, 16, 1) = chr(0x60);
        substr($catalog, 17, 9) = "ROUNDTRIP";
        substr($catalog, 98, 8) = "ROUNDTRP";
        substr($catalog, 110, 2) = pack("n", 1);
        print $catalog;
    '\'' > "$source/CATALOGS"

    # A deterministic body with repeated and distinct regions exercises
    # compression while making byte-for-byte restoration meaningful.
    perl -e '\''
        for my $block (0 .. 4) {
            print pack("N", $block), ("roundtrip-block-$block" . chr(10)) x 100;
        }
    '\'' > "$source/ROUNDTRP/DATA/HONMON"

    test "$(wc -c < "$source/CATALOGS" | tr -d "[:space:]")" = 2048
    test "$(wc -c < "$source/ROUNDTRP/DATA/HONMON" | tr -d "[:space:]")" = 9020
    ebzip --test "$source"
    ebzip --keep --force-overwrite --level 0 \
        --output-directory "$compressed" "$source"

    test -f "$compressed/CATALOGS"
    test -f "$compressed/ROUNDTRP/DATA/HONMON.ebz"
    test "$(dd if="$compressed/ROUNDTRP/DATA/HONMON.ebz" bs=1 count=5 2>/dev/null)" = EBZip
    test "$(wc -c < "$compressed/ROUNDTRP/DATA/HONMON.ebz" | tr -d "[:space:]")" -lt 9020
    information=$(ebzipinfo "$compressed")
    printf "%s\n" "$information"
    printf "%s\n" "$information" | grep -F "9020 ->"
    printf "%s\n" "$information" | grep -F "ebzip level 0 compression"

    ebunzip --keep --force-overwrite \
        --output-directory "$restored" "$compressed"
    cmp "$source/CATALOGS" "$restored/CATALOGS"
    cmp "$source/ROUNDTRP/DATA/HONMON" "$restored/ROUNDTRP/DATA/HONMON"
    rm -rf "$fixture"
'
