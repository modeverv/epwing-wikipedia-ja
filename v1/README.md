# Wikipedia EPWING Builder

`wikiepwing` is a reproducible, Docker-based pipeline for converting Wikimedia
dumps into EPWING/JIS X 4081 dictionaries. It currently provides a verified
text-only vertical slice: dump acquisition, streaming SQLite ingestion,
conservative Wikitext rendering, FreePWING packaging, and independent archive
inspection.

## Prerequisites

Only Docker and Docker Compose are required on the host. Build data is stored in the `wikiepwing-data` named volume. Final artifacts and reports are written to `./output` and `./reports` respectively; both are ignored by Git.

## Commands

```bash
make build-image
make doctor
make test
make lint
make typecheck
make format-check
make smoke-test
make toolchain-proof
```

`wikiepwing doctor` checks that the container is non-root, validates the default configuration, and verifies that its declared data, output, and report directories are writable. Add `--json` for machine-readable output.

To invoke the CLI directly through Compose, run `docker compose run --rm builder wikiepwing doctor`.

Inspect a generated package independently:

```bash
docker compose run --rm builder wikiepwing inspect \
  /workspace/output/wikiepwing-handcrafted-epwing.zip
```

For fixture or registered dump ingestion, use a dedicated SQLite path:

```bash
docker compose run --rm builder wikiepwing ingest \
  --input /data/import/jawiki.xml.bz2 \
  --database /data/intermediate/raw-pages.sqlite3
```

## Configuration

The default configuration is [config/default.toml](config/default.toml). Project and profile files are explicit inputs for later pipeline stages, but `build` and download commands are not implemented yet. Unknown keys are rejected so semantic configuration mistakes cannot silently change a build.

## Toolchain proof

The first EPWING proof uses checksum-verified FreePWING 1.5 and EB Library
4.4.3 sources. On Apple Silicon, a scoped patch updates EB Library's 2008
configuration scripts so the pinned release can identify `aarch64` correctly.

```bash
make toolchain-proof
```

This creates the deterministic `output/wikiepwing-handcrafted-epwing.zip`,
containing `Emacs`, `Linux`, and `Wikipedia` headwords, cross-references, an
`ebzip`-compressed body, and `TOOLCHAIN.json`. The proof independently extracts
the ZIP and validates its catalog with EB Library.

## Dump registration and download

Register a pre-downloaded dump without copying it:

```bash
docker compose run --rm builder wikiepwing download \
  --local /data/import/jawiki.xml.bz2 --project jawiki --date 20260701
```

For remote acquisition, `wikiepwing download --project jawiki --date 20260701`
derives the dump URL and its `sha1sums.txt` sidecar. Downloads use a locked
`.part` file, HTTP Range resume, bounded retry, disk-space preflight, SHA-1
verification, and an atomic manifest at `/data/manifests/dump.json`.

## Current milestone

The baseline renderer intentionally converts common source markup into readable
text before it reaches FreePWING:

* Internal and external link labels are retained.
* References, comments, and presentation-only HTML are removed.
* Infobox fields are emitted as compact `【field】value` lines.
* Basic lists and tables remain readable on constrained viewers.
* Unsupported Unicode is rendered as a generated 16-dot full-width gaiji,
  registered as `GAI16F`.  FreePWING permits at most 8,192 user characters;
  lower-frequency overflow characters remain visible as `[U+XXXX]` and are
  listed in `WIKIEP/GAIJI/OVERFLOW.TXT`, rather than being silently replaced.
  Unsupported title characters use the same visible escape because FreePWING
  cannot index gaiji tokens in a headword.
* Image references are extracted from infoboxes and article `File:` / `画像:`
  links, de-duplicated, and rendered as an `Images:` section. During EPWING
  builds, the first `WIKIEPWING_IMAGE_LIMIT` unique references are resolved
  through Wikimedia's public file redirect endpoint, converted to small BMP
  assets, and embedded as FreePWING color graphics. `WIKIEPWING_IMAGE_FORCE`
  can name comma-separated files, such as `EmacsIcon.svg`, that should be
  included even when the normal limit is low.

Full metadata resolution, license reporting, and unlimited image builds remain
the next image milestone. A tiny external-character proof can be built and
inspected with:

```bash
docker compose run --rm builder wikiepwing build \
  --records /workspace/tests/fixtures/gaiji-records.tsv \
  --output /output/gaiji-proof.zip
docker compose run --rm builder wikiepwing inspect /workspace/output/gaiji-proof.zip
```
