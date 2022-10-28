.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv

install: ## Install dependencies
	flit install --deps develop --symlink

install-full: ## Install dependencies
	make install
	pre-commit install -f

lint: ## Run code linters
	black --check ellar tests
	isort --check ellar tests
	autoflake --remove-unused-variables --remove-unused-variables -r ellar tests
	flake8 ellar tests
	mypy ellar

fmt format: ## Run code formatters
	black ellar tests
	isort ellar tests

test: ## Run tests
	pytest tests

test-cov: ## Run tests with coverage
	pytest --cov=ellar --cov-report term-missing tests

doc-deploy: ## Run Deploy Documentation
	make clean
	mkdocs gh-deploy --force --ignore-version


pre-commit-lint: ## Runs Requires commands during pre-commit
	make clean
	make fmt
	make lint
