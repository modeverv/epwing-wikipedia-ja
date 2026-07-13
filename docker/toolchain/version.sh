#!/bin/sh
set -eu

. /opt/freepwing/share/wikiepwing/freepwing-source.env

printf 'FreePWING %s\n' "$FREEPWING_VERSION"
exec ebinfo --version
