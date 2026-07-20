.PHONY: build-image test lint typecheck format-check doctor smoke-test toolchain-proof

build-image:
	docker compose --profile build build toolchain
	docker compose build builder
test:
	docker compose run --rm --no-deps builder python -m pytest
lint:
	docker compose run --rm --no-deps builder ruff check .
typecheck:
	docker compose run --rm --no-deps builder mypy --cache-dir=/data/mypy-cache src
format-check:
	docker compose run --rm --no-deps builder ruff format --check .
doctor:
	docker compose run --rm --no-deps builder wikiepwing doctor
smoke-test: build-image doctor test lint typecheck format-check

toolchain-proof: build-image
	docker compose run --rm --no-deps builder sh /workspace/docker/scripts/build-handcrafted.sh
	docker compose run --rm --no-deps builder sh /workspace/docker/scripts/verify-handcrafted.sh
