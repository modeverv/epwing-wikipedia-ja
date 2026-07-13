#!/bin/sh
set -eu

image=${1:-wikiepwing-toolchain:dev}
output=${2:-}
package_output=${3:-}
script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
fixture_directory=$(CDPATH= cd "$script_directory/../../tests/fixtures/handcrafted" && pwd)
probe_directory=$(mktemp -d)
trap 'rm -rf "$probe_directory"' EXIT HUP INT TERM

docker run --rm \
    --volume "$fixture_directory:/fixture:ro" \
    --volume "$probe_directory:/probe-output" \
    --entrypoint sh "$image" -c '
        set -eu
        work=/tmp/handcrafted-three-entry
        stage=$work/stage
        rm -rf "$work"
        mkdir -p "$work/source" "$stage/WIKIEP/DATA" "$stage/WIKIEP/GAIJI"

        cp /fixture/Makefile /fixture/build_fixture.pl /fixture/cgraphs.txt \
            /fixture/generate_bitmap.pl /fixture/halfchars.txt \
            /fixture/fullchars.txt /fixture/generate_gaiji.pl "$work/source/"
        iconv --from-code=UTF-8 --to-code=EUC-JP \
            /fixture/entries.tsv > "$work/source/entries.tsv"
        iconv --from-code=UTF-8 --to-code=EUC-JP \
            /fixture/catalogs.txt > "$work/source/catalogs.txt"
        chmod 0555 "$work/source/build_fixture.pl"

        cd "$work/source"
        perl ./generate_bitmap.pl bitmap.bmp
        perl ./generate_gaiji.pl half16.xbm full16.xbm
        fpwmake
        fpwmake catalogs
        test -s work/cgr
        test -s honmon
        test "$(wc -c < gai16h | tr -d "[:space:]")" = 4096
        test "$(wc -c < gai16f | tr -d "[:space:]")" = 4096
        test "$(wc -c < catalogs | tr -d "[:space:]")" = 2048
        perl -e '\''
            use strict;
            use warnings;
            sub read_file {
                my ($path) = @_;
                open my $input, "<:raw", $path or die "cannot read $path: $!\n";
                local $/;
                my $data = <$input>;
                close $input or die "cannot close $path: $!\n";
                return $data;
            }
            my $bitmap = read_file("bitmap.bmp");
            my $cgraph = read_file("work/cgr");
            my $honmon = read_file("honmon");
            die "invalid color graphic record\n"
                if substr($cgraph, 0, 4) ne "data"
                || unpack("V", substr($cgraph, 4, 4)) != length($bitmap)
                || substr($cgraph, 8, length($bitmap)) ne $bitmap;
            die "missing BMP payload in HONMON\n" if index($honmon, $bitmap) < 0;
        '\''

        cp catalogs "$stage/CATALOGS"
        cp honmon "$stage/WIKIEP/DATA/HONMON"
        cp gai16h "$stage/WIKIEP/GAIJI/GA16HALF"
        cp gai16f "$stage/WIKIEP/GAIJI/GA16FULL"
        information=$(ebinfo "$stage")
        printf "%s\n" "$information"
        printf "%s\n" "$information" | grep -F "the number of subbooks: 1"
        printf "%s\n" "$information" | grep -F "directory: wikiep"
        printf "%s\n" "$information" | grep -F "font sizes: 16"
        printf "%s\n" "$information" \
            | grep -F "narrow font characters: 0xa121 -- 0xa121"
        printf "%s\n" "$information" \
            | grep -F "wide font characters: 0xa121 -- 0xa121"
        /opt/eb/bin/wikiepwing-eb-probe "$stage" \
            > /probe-output/toolchain-capabilities.json
        package="$work/package"
        mkdir -p "$package"
        ebzip --level 0 --output-directory "$package" "$stage"
        ebinfo "$package"
        /opt/eb/bin/wikiepwing-eb-probe "$package" \
            > /probe-output/toolchain-capabilities-ebzip.json
        cmp /probe-output/toolchain-capabilities.json \
            /probe-output/toolchain-capabilities-ebzip.json
        find "$package" -exec touch -t 200001010000 {} +
        cd "$package"
        zip -X -q -r /probe-output/toolchain-smoke.epwing.zip CATALOGS WIKIEP
        cd "$work/source"
        rm -rf "$work"
    '

if [ -n "$output" ]; then
    mkdir -p "$(dirname "$output")"
    cp "$probe_directory/toolchain-capabilities.json" "$output"
fi
if [ -n "$package_output" ]; then
    mkdir -p "$(dirname "$package_output")"
    cp "$probe_directory/toolchain-smoke.epwing.zip" "$package_output"
fi
