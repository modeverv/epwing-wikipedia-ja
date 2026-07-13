#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

container_name="wikiepwing-compose-smoke-$$"
cleanup() {
    docker rm --force "$container_name" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

mkdir -p output reports/logs

docker compose config --quiet
docker compose build app

version_output=$(docker compose run --rm app wikiepwing --version)
printf '%s\n' "$version_output" | grep -Fx 'wikiepwing 0.1.0'

docker compose run --rm --entrypoint sh app -c '
    set -eu
    test "$(id -u)" -eq 10001
    test -w /tmp
    for path in /data/sources /data/work /data/cache /data/output /data/reports /data/logs; do
        test -w "$path"
    done
    test ! -w /data/reference
    test ! -w /app
    awk '\''$1 == "NoNewPrivs:" { found = 1; if ($2 != "1") exit 1 } END { if (!found) exit 1 }'\'' /proc/self/status
    awk '\''$1 == "CapEff:" { found = 1; if ($2 != "0000000000000000") exit 1 } END { if (!found) exit 1 }'\'' /proc/self/status
'

docker compose run --rm --detach --name "$container_name" --entrypoint sleep app 60 >/dev/null
mounts=$(docker inspect "$container_name" --format '{{range .Mounts}}{{printf "%s %s\n" .Destination .Type}}{{end}}')

assert_mount() {
    destination=$1
    expected_type=$2
    printf '%s\n' "$mounts" | awk -v destination="$destination" -v expected="$expected_type" '
        $1 == destination && $2 == expected { found = 1 }
        END { exit found ? 0 : 1 }
    '
}

assert_mount /data/sources volume
assert_mount /data/work volume
assert_mount /data/cache volume
assert_mount /data/output bind
assert_mount /data/reports bind
assert_mount /data/logs bind

test "$(docker inspect "$container_name" --format '{{.HostConfig.ReadonlyRootfs}}')" = true
test "$(docker inspect "$container_name" --format '{{index .HostConfig.Tmpfs "/tmp"}}')" = \
    'rw,noexec,nosuid,nodev,uid=10001,gid=10001,mode=1777'
