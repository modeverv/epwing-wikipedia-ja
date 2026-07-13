#!/bin/sh
set -eu

usage() {
    echo "usage: $0 (--url URL | --local-file PATH) SHA256 SIZE_BYTES DESTINATION" >&2
    exit 2
}

if [ "$#" -ne 5 ]; then
    usage
fi

mode=$1
source_location=$2
expected_sha256=$3
expected_size=$4
destination=$5

case "$expected_sha256" in
    '' | *[!0-9a-f]*)
        echo "invalid expected SHA-256: must be 64 lowercase hexadecimal characters" >&2
        exit 2
        ;;
esac
if [ "${#expected_sha256}" -ne 64 ]; then
    echo "invalid expected SHA-256: must be 64 lowercase hexadecimal characters" >&2
    exit 2
fi

case "$expected_size" in
    '' | *[!0-9]*)
        echo "invalid expected size: must be a non-negative integer" >&2
        exit 2
        ;;
esac

destination_directory=$(dirname "$destination")
mkdir -p "$destination_directory"
temporary_file=$(mktemp "${destination}.part.XXXXXX")

cleanup() {
    if [ -n "${temporary_file:-}" ]; then
        rm -f "$temporary_file"
    fi
}
trap cleanup 0 HUP INT TERM

case "$mode" in
    --url)
        case "$source_location" in
            https://*) ;;
            *)
                echo "refusing non-HTTPS source URL: $source_location" >&2
                exit 2
                ;;
        esac
        curl \
            --fail \
            --location \
            --proto '=https' \
            --proto-redir '=https' \
            --retry 3 \
            --show-error \
            --silent \
            --output "$temporary_file" \
            "$source_location"
        ;;
    --local-file)
        if [ ! -f "$source_location" ]; then
            echo "local source is not a regular file: $source_location" >&2
            exit 2
        fi
        cp "$source_location" "$temporary_file"
        ;;
    *)
        usage
        ;;
esac

actual_size=$(wc -c <"$temporary_file" | tr -d '[:space:]')
if [ "$actual_size" != "$expected_size" ]; then
    echo "source size mismatch: expected=$expected_size actual=$actual_size" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    actual_sha256=$(sha256sum "$temporary_file" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
    actual_sha256=$(shasum -a 256 "$temporary_file" | awk '{print $1}')
else
    echo "no SHA-256 implementation found (sha256sum or shasum required)" >&2
    exit 2
fi

if [ "$actual_sha256" != "$expected_sha256" ]; then
    echo "source SHA-256 mismatch: expected=$expected_sha256 actual=$actual_sha256" >&2
    exit 1
fi

mv -f "$temporary_file" "$destination"
temporary_file=
trap - 0 HUP INT TERM
printf '%s\n' "$destination"
