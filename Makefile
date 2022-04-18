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

lint: ## Run code linters
	black --check architek tests
	isort --check architek tests
	autoflake --remove-unused-variables --remove-unused-variables -r architek tests
	flake8 architek tests
	mypy architek

fmt format: ## Run code formatters
	black architek tests
	isort architek tests

test: ## Run tests
	pytest .

test-cov: ## Run tests with coverage
	pytest --cov=architek --cov-report term-missing tests
