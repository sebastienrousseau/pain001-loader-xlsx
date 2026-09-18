# pain001-loader-xlsx developer targets. CI runs the same commands.
.DEFAULT_GOAL := help
PYTHON ?= python
# Mutation score floor for the loader and the normaliser: 85.2% (144 of
# 169) on 2026-09-18, up from 68.6% before the guard-message tests. The
# floor sits under it so one flaky mutant cannot block a release. Raise it
# when the score rises; never lower it to make a red run green.
MUTATION_FLOOR ?= 83

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install: ## Install the package with its development extras
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run tests with the 100% line+branch coverage gate
	$(PYTHON) -m pytest tests/ --cov=pain001_loader_xlsx --cov-branch --cov-report=term-missing --cov-fail-under=100 -q

lint: ## Ruff check and format check
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

type-check: ## mypy
	$(PYTHON) -m mypy pain001_loader_xlsx

doc-coverage: ## 100% docstring coverage
	$(PYTHON) -m interrogate --fail-under 100 pain001_loader_xlsx

docs: ## Build the Sphinx documentation (warnings are errors)
	sphinx-build -W --keep-going -b html docs docs/_build/html

mutate: ## Mutation testing (mutmut 3, config in pyproject)
	rm -rf mutants
	$(PYTHON) -m mutmut run
	$(PYTHON) -m mutmut export-cicd-stats
	$(PYTHON) scripts/mutation_gate.py --floor $(MUTATION_FLOOR)

check: lint type-check test doc-coverage ## Run all gates

.PHONY: help install test lint type-check doc-coverage docs mutate check
