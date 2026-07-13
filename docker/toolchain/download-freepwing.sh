#!/bin/sh
set -eu

script_directory=$(CDPATH= cd "$(dirname "$0")" && pwd)
# This file is repository-owned input, not data from the download target.
. "$script_directory/freepwing-source.env"

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: $0 DESTINATION [LOCAL_MIRROR]" >&2
    exit 2
fi

destination=$1
if [ "$#" -eq 2 ]; then
    exec "$script_directory/fetch-verified.sh" \
        --local-file "$2" "$FREEPWING_SOURCE_SHA256" \
        "$FREEPWING_SOURCE_SIZE_BYTES" "$destination"
fi

exec "$script_directory/fetch-verified.sh" \
    --url "$FREEPWING_SOURCE_URL" "$FREEPWING_SOURCE_SHA256" \
    "$FREEPWING_SOURCE_SIZE_BYTES" "$destination"
