#!/bin/sh
set -eu

script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
. "$script_directory/eb-source.env"

work_directory=/tmp/eb-build
archive="$work_directory/$EB_SOURCE_FILENAME"
source_directory="$work_directory/source"

rm -rf "$work_directory"
mkdir -p "$source_directory"
"$script_directory/download-eb.sh" "$archive"

# The checksum fixes this exact archive, but the prefix check also prevents a
# future lock update from silently changing extraction layout or escaping it.
tar --list --bzip2 --file "$archive" | while IFS= read -r member; do
    case "$member" in
        "eb-$EB_VERSION" | "eb-$EB_VERSION"/*) ;;
        *)
            echo "unexpected EB archive member: $member" >&2
            exit 1
            ;;
    esac
done

tar --extract --bzip2 --file "$archive" \
    --directory "$source_directory" \
    --strip-components=1 \
    --no-same-owner \
    --no-same-permissions

patch --directory="$source_directory" --strip=1 \
    --input=/tmp/patches/eb/eb-4.4.3-modern-linux.patch

cd "$source_directory"
# Dictionary input is local-only. EBNet is unnecessary for this pipeline and
# enabling the legacy network path exposes code that modern GCC flags as an
# out-of-bounds write in multiplex.c.
./configure --prefix=/opt/eb --disable-ebnet
make -j"$(getconf _NPROCESSORS_ONLN)"
make check
make install

mkdir -p /opt/eb/share/wikiepwing
cp "$script_directory/eb-source.env" /opt/eb/share/wikiepwing/eb-source.env
cp /tmp/patches/eb/eb-4.4.3-modern-linux.patch \
    /opt/eb/share/wikiepwing/eb-4.4.3-modern-linux.patch

LD_LIBRARY_PATH=/opt/eb/lib /opt/eb/bin/ebinfo --version
cc -std=c11 -Wall -Wextra -Werror -O2 \
    -I/opt/eb/include /tmp/toolchain/eb-probe.c \
    -L/opt/eb/lib -Wl,-rpath,/opt/eb/lib -leb \
    -o /opt/eb/bin/wikiepwing-eb-probe
cc -std=c11 -Wall -Wextra -Werror -O2 \
    -I/opt/eb/include /tmp/toolchain/eb-search.c \
    -L/opt/eb/lib -Wl,-rpath,/opt/eb/lib -leb \
    -o /opt/eb/bin/wikiepwing-eb-search
cc -std=c11 -Wall -Wextra -Werror -O2 \
    -I/opt/eb/include /tmp/toolchain/eb-entry.c \
    -L/opt/eb/lib -Wl,-rpath,/opt/eb/lib -leb \
    -o /opt/eb/bin/wikiepwing-eb-entry
rm -rf "$work_directory"
