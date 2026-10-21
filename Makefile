# SPDX-License-Identifier: Apache-2.0 OR MIT
# pain001-loader-xlsx developer targets. CI runs the same commands.
.DEFAULT_GOAL := help
PYTHON ?= python
# Mutation score floor for the loader and the normaliser: 88.2% (217 of
# 246) on 2026-10-21, up from 85.2% (144 of 169) on 2026-09-18 and 68.6%
# before the guard-message tests. The floor sits under it so one flaky
# mutant cannot block a release. Raise it when the score rises; never
# lower it to make a red run green.
MUTATION_FLOOR ?= 86

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install: ## Install the hash-pinned test tree, then the package (lint: requirements/lint.txt)
	$(PYTHON) -m pip install --require-hashes -r requirements/test.txt
	$(PYTHON) -m pip install --no-deps -e .

test: ## Run tests with the 100% line+branch coverage gate
	$(PYTHON) -m pytest tests/ --cov=pain001_loader_xlsx --cov-branch --cov-report=term-missing --cov-fail-under=100 -q

lint: ## Ruff check and format check
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

type-check: ## mypy --strict over the package and the gate scripts
	$(PYTHON) -m mypy pain001_loader_xlsx scripts/check_complexity.py scripts/check_suite_consistency.py

complexity: ## Complexity ceilings against complexity-baseline.json (needs requirements/complexity.txt)
	$(PYTHON) scripts/check_complexity.py
	complexipy pain001_loader_xlsx scripts benches examples fuzz --max-complexity-allowed 15 --quiet

doc-coverage: ## 100% docstring coverage
	$(PYTHON) -m interrogate --fail-under 100 pain001_loader_xlsx

docs: ## Build the Sphinx documentation (warnings are errors)
	sphinx-build -W --keep-going -b html docs docs/_build/html

mutate: ## Mutation testing (mutmut 3, config in pyproject)
	rm -rf mutants
	$(PYTHON) -m mutmut run
	$(PYTHON) -m mutmut export-cicd-stats
	$(PYTHON) scripts/mutation_gate.py --floor $(MUTATION_FLOOR)

audit: ## pip-audit every hash-pinned requirements file (needs requirements/audit.txt)
	@for f in requirements/*.txt; do \
		echo "--- $$f"; \
		pip-audit --progress-spinner off --require-hashes --disable-pip -r "$$f" || exit 1; \
	done

pip-compile: ## Regenerate hash-pinned requirements/*.txt from requirements/*.in
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@for f in requirements/*.in; do \
		[ "$$f" = requirements/fuzz.in ] && continue; \
		echo "compiling $$f"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.10 "$$f" -o "$${f%.in}.txt"; \
	done
	@echo "compiling requirements/fuzz.in (Linux x86_64, Atheris wheels only)"
	@uv pip compile --quiet --generate-hashes --python-platform x86_64-manylinux_2_17 \
		--python-version 3.12 requirements/fuzz.in -o requirements/fuzz.txt

fuzz: ## Atheris for FUZZ_SECONDS (default 60); Linux x86_64, needs requirements/fuzz.txt
	$(PYTHON) fuzz/fuzz_load_xlsx.py fuzz/corpus -max_total_time=$(or $(FUZZ_SECONDS),60)

demo: ## Re-render .github/demo.gif from .github/demo.tape (needs vhs)
	vhs .github/demo.tape

check: lint type-check complexity test doc-coverage ## Run all gates

.PHONY: help install test lint type-check complexity doc-coverage docs mutate audit pip-compile fuzz demo check
