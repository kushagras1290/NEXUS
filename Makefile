SHELL := /bin/bash

.PHONY: api-install api-test api-lint web-install web-test web-build test dev dataset

api-install:
	cd apps/api && python -m pip install -e '.[dev]'

api-test:
	cd apps/api && pytest -q

api-lint:
	cd apps/api && ruff check . && ruff format --check . && mypy src

web-install:
	cd apps/web && npm ci

web-test:
	cd apps/web && npm run typecheck && npm run lint

web-build:
	cd apps/web && npm run build

test: api-test web-test

dev:
	docker compose up --build

dataset:
	python tools/generate_eukb.py --output data/generated --documents 50000 --eval-queries 5000
