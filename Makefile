VIRTUALENV=$(shell echo "$${VDIR:-'.env'}")
MODULE=adrest
SPHINXBUILD=sphinx-build
ALLSPHINXOPTS= -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
BUILDDIR=_build

all: $(VIRTUALENV)

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile

.PHONY: clean
# target: clean - Display callable targets
clean:
	@rm -rf build dist docs/_build
	@rm -f *.py[co]
	@rm -f *.orig
	@rm -f */*.py[co]
	@rm -f */*.orig

# ==============
#  Bump version
# ==============

.PHONY: release
VERSION?=minor
# target: release - Bump version
release: $(VIRTUALENV)
	@$(VIRTUALENV)/bin/pip install bumpversion
	@$(VIRTUALENV)/bin/bumpversion $(VERSION)
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push --all
	@git push --tags

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VERSION=patch

# ===============
#  Build package
# ===============

.PHONY: register
# target: register - Register module on PyPi
register: $(VIRTUALENV)
	@$(VIRTUALENV)/bin/python setup.py register

.PHONY: upload
# target: upload - Upload module on PyPi
upload: docs $(VIRTUALENV)
	@$(VIRTUALENV)/bin/pip install wheel
	@$(VIRTUALENV)/bin/python setup.py sdist upload || echo 'Skip upload'
	@$(VIRTUALENV)/bin/python setup.py bdist_wheel upload || echo 'Skip upload'

.PHONY: docs
# target: docs - Compile and upload docs
docs: $(VIRTUALENV)
	@$(VIRTUALENV)/bin/pip install sphinx
	@$(VIRTUALENV)/bin/python setup.py build_sphinx --source-dir=docs/ --build-dir=docs/_build --all-files
	# python setup.py upload_sphinx --upload-dir=docs/_build/html

# =============
#  Development
# =============

.PHONY: t
# target: t - Runs tests
t: clean
	@python setup.py test

.PHONY: audit
# target: audit - Audit code
audit:
	@pylama $(MODULE) -i E501

$(VIRTUALENV): requirements.txt
	virtualenv --no-site-packages $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install -M -r requirements.txt
