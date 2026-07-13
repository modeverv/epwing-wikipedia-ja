#!/bin/sh
set -eu

script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
. "$script_directory/freepwing-source.env"

work_directory=/tmp/freepwing-build
archive="$work_directory/$FREEPWING_SOURCE_FILENAME"
source_directory="$work_directory/source"

rm -rf "$work_directory"
mkdir -p "$source_directory"
"$script_directory/download-freepwing.sh" "$archive"

# The checksum identifies the archive; these checks also keep a future lock
# update from silently introducing traversal paths or link-based extraction.
tar --list --bzip2 --file "$archive" | while IFS= read -r member; do
    case "$member" in
        "$FREEPWING_SOURCE_ROOT" | "$FREEPWING_SOURCE_ROOT"/*) ;;
        *)
            echo "unexpected FreePWING archive member: $member" >&2
            exit 1
            ;;
    esac
done
tar --list --verbose --bzip2 --file "$archive" | while IFS=' ' read -r mode _rest; do
    case "$mode" in
        d* | -*) ;;
        *)
            echo "unsupported FreePWING archive member type: $mode" >&2
            exit 1
            ;;
    esac
done

tar --extract --bzip2 --file "$archive" \
    --directory "$source_directory" \
    --strip-components=1 \
    --no-same-owner \
    --no-same-permissions

# Patch order is repository-controlled and stable. TASK-B004 currently proves
# that the unmodified 1.6.1 source builds, so this loop intentionally finds none.
find /tmp/patches/freepwing -maxdepth 1 -type f -name '*.patch' -print \
    | LC_ALL=C sort \
    | while IFS= read -r patch_file; do
        patch --directory="$source_directory" --strip=1 --input="$patch_file"
    done

cd "$source_directory"
./configure \
    --prefix=/opt/freepwing \
    --with-perllibdir=/opt/freepwing/lib/perl5
make -j"$(getconf _NPROCESSORS_ONLN)"
make check
make install

mkdir -p /opt/freepwing/share/wikiepwing
cp "$script_directory/freepwing-source.env" \
    /opt/freepwing/share/wikiepwing/freepwing-source.env

PERL5LIB=/opt/freepwing/lib/perl5 perl \
    -MFreePWING::Text \
    -MFreePWING::Link::GDBM \
    -MFreePWING::Link::BDB \
    -e 'print "FreePWING modules OK\n"'
/opt/freepwing/bin/fpwmake --version
rm -rf "$work_directory"
