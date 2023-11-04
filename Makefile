.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv
	find . -name .ruff_cache  | xargs  rm -rfv

install: ## Install dependencies
	flit install --deps develop --symlink

install-full: ## Install dependencies
	make install
	pre-commit install -f

lint:fmt ## Run code linters
	black --check ellar tests examples
	ruff check ellar tests examples
	mypy ellar

fmt format:clean ## Run code formatters
	black ellar tests examples
	ruff check --fix ellar tests examples

test:clean ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=ellar --cov-report term-missing

doc-deploy:clean ## Run Deploy Documentation
	mkdocs gh-deploy --force --ignore-version

doc-serve: ## Launch doc local server
	mkdocs serve

pre-commit-lint: ## Runs Requires commands during pre-commit
	make clean
	make fmt
	make lint
