APP_IMAGE ?= wikiepwing-app:dev
TOOLCHAIN_IMAGE ?= wikiepwing-toolchain:dev
FREEPWING_SOURCE ?= data/sources/freepwing_1.6.1.orig.tar.bz2
ENTRIES ?= output/entries.jsonl
GRAPHICS_DIR ?=
GAIJI_DIR ?=
TITLE ?= Wikipedia
SUBBOOK_DIR ?= WIKIEP
EPWING_OUTPUT ?= output/jawiki.epwing.zip

.PHONY: app-image build-epwing check doctor download-freepwing format format-check lint package-toolchain probe-toolchain test test-app-image test-compose test-eb-image test-eb-source test-ebzip test-freepwing-build-entries test-freepwing-source test-handcrafted test-mini-end-to-end toolchain-image typecheck

app-image:
	docker build --file docker/app.Dockerfile --tag "$(APP_IMAGE)" .

build-epwing: toolchain-image
	sh docker/toolchain/build-epwing.sh "$(TOOLCHAIN_IMAGE)" "$(ENTRIES)" "$(EPWING_OUTPUT)" \
		"$(GRAPHICS_DIR)" "$(GAIJI_DIR)" "$(TITLE)" "$(SUBBOOK_DIR)"

doctor:
	mkdir -p output reports/logs
	docker compose build app
	docker compose run --rm app wikiepwing doctor

download-freepwing:
	sh docker/toolchain/download-freepwing.sh "$(FREEPWING_SOURCE)"

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

package-toolchain: toolchain-image
	sh docker/toolchain/package-smoke.sh "$(TOOLCHAIN_IMAGE)" output/toolchain-smoke.epwing.zip

probe-toolchain: toolchain-image
	sh docker/toolchain/probe.sh "$(TOOLCHAIN_IMAGE)" reports/toolchain-capabilities.json

typecheck:
	uv run mypy src

test:
	uv run pytest -m "not network and not slow and not manual"

test-app-image: app-image
	@test "$$(docker run --rm --entrypoint id "$(APP_IMAGE)" -u)" -eq 10001
	docker run --rm --entrypoint grep "$(APP_IMAGE)" -Fx 'VERSION_CODENAME=bookworm' /etc/os-release
	docker run --rm --entrypoint python "$(APP_IMAGE)" -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
	docker run --rm --entrypoint uv "$(APP_IMAGE)" --version | grep -E '^uv 0\.11\.17( |$$)'
	docker run --rm --entrypoint sh "$(APP_IMAGE)" -c 'set -eu; test -w "$$HOME"; for path in /data/sources /data/work /data/cache /data/output /data/reports /data/logs; do test -w "$$path"; done; test ! -w /data/reference; test ! -w /app'
	docker run --rm "$(APP_IMAGE)" wikiepwing --version | grep -Fx 'wikiepwing 0.1.0'

test-compose:
	sh docker/compose-smoke.sh

test-eb-source:
	uv run pytest tests/test_eb_source.py

test-ebzip: toolchain-image
	sh docker/toolchain/ebzip-roundtrip-smoke.sh "$(TOOLCHAIN_IMAGE)"

test-freepwing-build-entries: toolchain-image
	sh docker/toolchain/freepwing-build-entries-smoke.sh "$(TOOLCHAIN_IMAGE)"

test-freepwing-source:
	uv run pytest tests/test_freepwing_source.py

test-handcrafted: toolchain-image
	sh docker/toolchain/handcrafted-three-entry-smoke.sh "$(TOOLCHAIN_IMAGE)"

test-mini-end-to-end: toolchain-image
	sh docker/toolchain/mini-end-to-end-smoke.sh "$(TOOLCHAIN_IMAGE)"

toolchain-image:
	docker build --file docker/toolchain.Dockerfile --tag "$(TOOLCHAIN_IMAGE)" .

test-eb-image:
	docker build --no-cache --file docker/toolchain.Dockerfile --tag "$(TOOLCHAIN_IMAGE)" .
	sh docker/toolchain/eb-image-smoke.sh "$(TOOLCHAIN_IMAGE)"

check: format-check lint typecheck test
