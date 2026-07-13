#!/bin/sh
set -eu

image=${1:-wikiepwing-toolchain:dev}
expected_architecture=$(docker version --format '{{.Server.Arch}}')

test "$(docker run --rm --entrypoint id "$image" -u)" -eq 10001
docker run --rm --entrypoint grep "$image" -Fx 'VERSION_CODENAME=bookworm' /etc/os-release
docker run --rm "$image" | grep -F '4.4.3'
docker run --rm "$image" | grep -F 'FreePWING 1.6.1'

docker run --rm --entrypoint sh "$image" -c '
    set -eu
    test "$(command -v ebinfo)" = /opt/eb/bin/ebinfo
    test "$(command -v fpwmake)" = /opt/freepwing/bin/fpwmake
    test "$(command -v gmake)" = /usr/bin/gmake
    fpwmake --version | grep -F "GNU Make 4.3"
    test -x /usr/local/bin/toolchain-version
    test -f /opt/eb/include/eb/eb.h
    test -f /opt/eb/include/eb/sysdefs.h
    ! grep -F "#define EB_ENABLE_EBNET" /opt/eb/include/eb/sysdefs.h
    test -f /opt/eb/lib/libeb.a
    test -e /opt/eb/lib/libeb.so
    test -f /opt/eb/share/wikiepwing/eb-source.env
    test -f /opt/freepwing/share/wikiepwing/freepwing-source.env
    test -f /opt/freepwing/share/freepwing/fpwutils.mk
    for command in catdump cphier fpwcgraph fpwcontrol fpwfullchar fpwhalfchar \
        fpwindex fpwlink fpwsort fpwsound mkdirhier perl.sh; do
        test -x "/opt/freepwing/libexec/freepwing/$command"
    done
    test -f /opt/freepwing/lib/perl5/FreePWING/Text.pm
    test ! -e /usr/local/lib/site_perl/FreePWING
    perl -MFreePWING::Text -MFreePWING::Link::GDBM -MFreePWING::Link::BDB \
        -e '\''print "FreePWING runtime modules OK\n"'\''
    test "$(dpkg-query -W -f='\''${Version}'\'' make)" = 4.3-4.1
    test "$(dpkg-query -W -f='\''${Version}'\'' perl)" = 5.36.0-7+deb12u3
    test ! -e /tmp/eb-build
    test ! -e /tmp/freepwing-build
    ! command -v cc >/dev/null 2>&1
    ! command -v curl >/dev/null 2>&1
    if ldd -r /opt/eb/bin/ebinfo 2>&1 | grep -E "not found|undefined symbol"; then
        exit 1
    fi
'

test "$(docker image inspect "$image" --format '{{.Os}}/{{.Architecture}}')" = "linux/$expected_architecture"
test "$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.version"}}')" = 4.4.3
test "$(docker image inspect "$image" --format '{{index .Config.Labels "io.wikiepwing.eb.source.sha256"}}')" = abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f
test "$(docker image inspect "$image" --format '{{index .Config.Labels "io.wikiepwing.freepwing.version"}}')" = 1.6.1
test "$(docker image inspect "$image" --format '{{index .Config.Labels "io.wikiepwing.freepwing.source.sha256"}}')" = 274a8cf392e2c46662bcf3eedce331fe84e65f7e5e6044d0178b2150a0704fc2
