SPHINXBUILD ?= poetry run sphinx-build
SOURCEDIR = source
BUILDDIR = build

.PHONY: help html clean

help:
	$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)"

html:
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)"

clean:
	$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)"
