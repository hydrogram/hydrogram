VENV := venv
PYTHON := $(VENV)/bin/python
HOST = $(shell ifconfig | grep "inet " | tail -1 | cut -d\  -f2)
TAG = v$(shell grep -E '__version__ = ".*"' hydrogram/__init__.py | cut -d\" -f2)

RM := rm -rf

.PHONY: venv clean-build clean-api clean api build

venv:
	$(RM) $(VENV)
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip wheel setuptools
	$(PYTHON) -m pip install -U -r requirements.txt -r dev-requirements.txt
	@echo "Created venv with $$($(PYTHON) --version)"

clean-build:
	$(RM) *.egg-info build dist

clean-api:
	$(RM) hydrogram/errors/exceptions hydrogram/raw/all.py hydrogram/raw/base hydrogram/raw/functions hydrogram/raw/types

clean:
	make clean-build
	make clean-api

api:
	cd compiler/api && ../../$(PYTHON) compiler.py
	cd compiler/errors && ../../$(PYTHON) compiler.py

build:
	make clean
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel

tag:
	git tag $(TAG)
	git push origin $(TAG)

dtag:
	git tag -d $(TAG)
	git push origin -d $(TAG)