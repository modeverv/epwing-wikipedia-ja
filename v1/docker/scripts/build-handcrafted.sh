#!/bin/sh
set -eu

readonly source_dir=/workspace/toolchain/handcrafted
readonly work_dir=/data/handcrafted-work
readonly staging_dir=/data/handcrafted-staging
readonly output_dir=/output
readonly archive_name=wikiepwing-handcrafted-epwing.zip

rm -rf "$work_dir" "$staging_dir"
mkdir -p "$work_dir" "$staging_dir/WIKIEP/DATA" "$output_dir"
cp "$source_dir/Makefile" "$source_dir/build_fixture.pl" "$source_dir/catalogs.txt" "$work_dir/"
chmod +x "$work_dir/build_fixture.pl"
iconv --from-code=UTF-8 --to-code=EUC-JP "$work_dir/catalogs.txt" > "$work_dir/catalogs.eucjp"
mv "$work_dir/catalogs.eucjp" "$work_dir/catalogs.txt"

cd "$work_dir"
fpwmake
fpwmake catalogs
cp catalogs "$staging_dir/CATALOGS"
cp honmon "$staging_dir/WIKIEP/DATA/HONMON"

cd "$staging_dir"
ebzip --force-overwrite .
test -f WIKIEP/DATA/HONMON.ebz

cat > TOOLCHAIN.json <<'EOF'
{"eb_library":{"sha256":"abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f","version":"4.4.3"},"freepwing":{"sha256":"51e3acf62c9c634c049116e99f02185143a81e4da0971896d48ea84fcffa5dd8","version":"1.5"},"schema_version":1}
EOF
find CATALOGS WIKIEP -exec touch -t 198001010000 {} +
touch -t 198001010000 TOOLCHAIN.json
rm -f "$output_dir/$archive_name"
TZ=UTC zip --quiet -X -D --recurse-paths "$output_dir/$archive_name" CATALOGS TOOLCHAIN.json WIKIEP
sha256sum "$output_dir/$archive_name" > "$output_dir/$archive_name.sha256"
