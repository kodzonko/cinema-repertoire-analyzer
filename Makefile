PROJECT_ROOT := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
SRC := $(PROJECT_ROOT)src
TESTS := $(PROJECT_ROOT)tests
CONFIG_FILE := $(PROJECT_ROOT)pyproject.toml
.PHONY: install format lint test-e2e test-int test-unit update

install:
	poetry install

format:
	poetry run ruff format $(SRC) $(TESTS)
	poetry run autoflake --recursive --in-place --expand-star-imports --remove-all-unused-imports --ignore-init-module-imports $(SRC) $(TESTS)

lint:
	poetry run ruff $(SRC)

test-e2e:
	poetry run pytest -m e2e

test-int:
	poetry run pytest -m integration

test-unit:
	poetry run pytest --failed-first --new-first --cov=$(SRC) -m unit

update:
	poetry update
