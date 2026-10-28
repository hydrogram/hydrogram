UV = uv
PYTHON = python
SPHINX_BUILD = sphinx-build
SPHINX_AUTOBUILD = sphinx-autobuild
TOWNCRIER = towncrier

HYDROGRAM_DIR = hydrogram
DOCS_DIR = docs
DOCS_SOURCE = $(DOCS_DIR)/source
DOCS_BUILD = $(DOCS_DIR)/build
API_DIRS = $(HYDROGRAM_DIR)/errors/exceptions $(HYDROGRAM_DIR)/raw/all.py $(HYDROGRAM_DIR)/raw/base $(HYDROGRAM_DIR)/raw/functions $(HYDROGRAM_DIR)/raw/types
DOCS_API_DIRS = $(DOCS_SOURCE)/api/bound-methods $(DOCS_SOURCE)/api/methods $(DOCS_SOURCE)/api/types $(DOCS_SOURCE)/telegram

.PHONY: all build clean clean-api clean-docs api api-raw api-errors docs docs-compile docs-serve live-docs towncrier towncrier-draft dev-tools check-api-schema update-api-schema validate-api-schema generate-docs-json compare-bot-api cherry-pick-pyro help

all: api docs

# Hatchling generates the API automatically when building the wheel.
build:
	@$(UV) build --no-sources

clean: clean-api clean-docs
	@echo "All directories cleaned successfully"

clean-api:
	@echo "Cleaning generated API files..."
	@rm -rf $(API_DIRS)

clean-docs:
	@echo "Cleaning generated documentation..."
	@rm -rf $(DOCS_BUILD) $(DOCS_API_DIRS)

api: api-raw api-errors
	@echo "API compilation finished"

api-raw:
	@echo "Compiling raw API..."
	@$(PYTHON) -c "from compiler.api.compiler import start; start()"

api-errors:
	@echo "Compiling API errors..."
	@$(PYTHON) -c "from compiler.errors.compiler import start; start()"

docs: docs-compile docs-serve

docs-compile:
	@echo "Compiling documentation..."
	@$(PYTHON) -c "from compiler.docs.compiler import start; start()"

docs-serve:
	@echo "Building and serving documentation..."
	@$(SPHINX_BUILD) -b html $(DOCS_SOURCE) $(DOCS_BUILD)/html -j auto

live-docs:
	@echo "Starting documentation server with live reload..."
	@$(SPHINX_AUTOBUILD) $(DOCS_SOURCE) $(DOCS_BUILD)/html -j auto --watch $(HYDROGRAM_DIR)

towncrier:
	@echo "Generating release notes..."
	@$(TOWNCRIER) build --yes

towncrier-draft:
	@echo "Generating draft release notes..."
	@$(TOWNCRIER) build --draft

check-api-schema:
	@echo "Checking Telegram API schema for updates..."
	@$(PYTHON) dev_tools/check_api_schema_updates.py

update-api-schema:
	@$(PYTHON) dev_tools/check_api_schema_updates.py --apply

validate-api-schema:
	@$(PYTHON) dev_tools/check_api_schema_updates.py --validate

generate-docs-json:
	@echo "Generating API documentation JSON..."
	@$(PYTHON) dev_tools/generate_docs_json.py

compare-bot-api:
	@echo "Comparing implementation against Bot API..."
	@$(PYTHON) dev_tools/compare_to_bot_api.py

cherry-pick-pyro:
	@echo "Usage: make cherry-pick-pyro TYPE=<pr|branch|commit> ID=<number|name|hash>"
	@[ "$(TYPE)" ] && [ "$(ID)" ] && $(PYTHON) dev_tools/cherry_pick_pyro.py $(TYPE) $(ID) || echo "Please provide TYPE and ID parameters"

help:
	@echo "Available targets:"
	@echo "  all            : Compile API and documentation"
	@echo "  build          : Generate API and build source and wheel distributions"
	@echo "  clean          : Remove all generated files"
	@echo "  api            : Compile all API components"
	@echo "  docs           : Compile and serve documentation"
	@echo "  live-docs      : Start documentation server with live reload"
	@echo "  towncrier      : Generate release notes"
	@echo "  towncrier-draft: Generate draft release notes"
	@echo "  check-api-schema: Check Telegram API schema for updates"
	@echo "  update-api-schema: Validate and apply the latest verified schema"
	@echo "  validate-api-schema: Validate local schema and deterministic generation offline"
	@echo "  generate-docs-json: Generate API documentation JSON"
	@echo "  compare-bot-api: Compare implementation against Bot API"
	@echo "  cherry-pick-pyro: Cherry-pick code from Pyrogram (usage: make cherry-pick-pyro TYPE=<pr|branch|commit> ID=<number|name|hash>)"
