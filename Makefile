PYTHON ?= .venv/bin/python
SPEC ?= ../saas-be/api/openapi.yaml

.PHONY: install generate sync-spec lint format typecheck test check build clean

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e . --group dev

generate:
	$(PYTHON) scripts/generate_models.py

sync-spec:
	$(PYTHON) scripts/generate_models.py --from-spec $(SPEC)

lint:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m ruff format --check src tests scripts

format:
	$(PYTHON) -m ruff check --fix src tests scripts
	$(PYTHON) -m ruff format src tests scripts

typecheck:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest

check: lint typecheck test

build:
	$(PYTHON) -m build

clean:
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache
