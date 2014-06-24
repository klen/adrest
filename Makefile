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

.PHONY: register
# target: register - Register module on PyPi
register:
	@python setup.py register

.PHONY: upload
# target: upload - Upload module on PyPi
upload: docs
	@python setup.py sdist upload || echo 'Skip upload'
	@python setup.py bdist_wheel upload || echo 'Skip upload'

.PHONY: t
# target: t - Runs tests
t: clean
	@python setup.py test

.PHONY: audit
# target: audit - Audit code
audit:
	@pylama $(MODULE) -i E501

.PHONY: docs
# target: docs - Compile and upload docs
docs:
	python setup.py build_sphinx --source-dir=docs/ --build-dir=docs/_build --all-files
	# python setup.py upload_sphinx --upload-dir=docs/_build/html

$(VIRTUALENV): requirements.txt
	virtualenv --no-site-packages $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install -M -r requirements.txt
