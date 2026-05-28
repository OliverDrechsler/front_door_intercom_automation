# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = _source
BUILDDIR      = _build
VENV_PYTHON   = .venv/bin/python
VENV_PIP      = .venv/bin/pip
PYTEST        = .venv/bin/pytest

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

venv:
	python3.11 -m venv .venv

install: venv
	$(VENV_PIP) install -r requirements.txt

test:
	$(PYTEST)

test-cov:
	$(PYTEST) --cov=./ --cov-report=html

.PHONY: help venv install test test-cov Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
