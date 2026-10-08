# Developer entry points for suil. Run `make help` for the target list.

VENV ?= .venv
PIP  := $(VENV)/bin/pip

# Hook environments live in the repository, not in ~/.cache/pre-commit.
export PRE_COMMIT_HOME := $(CURDIR)/.pre-commit

.DEFAULT_GOAL := shell

.PHONY: help install lint test build docs docs-build clean shell

help:  ## Show the available targets
	@echo "suil"
	@echo
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-10s %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)

# suil itself is installed once pyproject.toml has landed in this tree.
install:  ## Create the virtualenv, install the tooling and suil, wire up the hooks
	python3 -m venv --prompt suil $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	if [ -f pyproject.toml ]; then $(PIP) install -e .; fi
	$(VENV)/bin/pre-commit install

lint:  ## Run the pre-commit hooks over every file
	$(VENV)/bin/pre-commit run --all-files

test:  ## Run the test suite
	$(VENV)/bin/pytest -q

build:  ## Build the sdist and the wheel into dist/, as the publish workflow does
	$(VENV)/bin/python -m build

docs:  ## Serve the documentation site on http://127.0.0.1:8004, reloading on edits
	$(VENV)/bin/mkdocs serve --dev-addr 127.0.0.1:8004

docs-build:  ## Build the documentation site into site/, as the Pages workflow does
	$(VENV)/bin/mkdocs build

clean:  ## Remove the virtualenv, the hook environments and the build output
	rm -rf $(VENV) .pre-commit build dist site

shell:  ## Open an interactive subshell with the virtualenv activated
	@rc="$$(mktemp)"; \
	trap 'rm -f "$$rc"' EXIT; \
	cat ~/.bashrc 2> /dev/null > "$$rc" || true; \
	echo 'export PRE_COMMIT_HOME="$(PRE_COMMIT_HOME)"' >> "$$rc"; \
	echo 'source $(CURDIR)/$(VENV)/bin/activate' >> "$$rc"; \
	bash --rcfile "$$rc" -i || true
