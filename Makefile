.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name "*.pyc" -type f -delete
	find . -name "*.pyo" -type f -delete
	find . -name "*~" -type f -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true

install: ## Install dependencies
	pip install -r requirements.txt
	flit install --symlink

install-full: ## Install dependencies
	make install
	pre-commit install -f

lint:fmt ## Run code linters
	ruff check ellar tests samples
	mypy ellar

ruff-fix: ## Run Ruff fixer
	ruff check ellar tests samples --fix --unsafe-fixes

fmt format:clean ## Run code formatters
	ruff format ellar tests samples
	ruff check --fix ellar tests samples

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
