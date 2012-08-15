MODULE=adrest
SPHINXBUILD=sphinx-build
ALLSPHINXOPTS= -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
BUILDDIR=_build


.PHONY: clean
clean:
	sudo rm -rf build dist docs/_build
	find . -name "*.pyc" -delete
	find . -name "*.orig" -delete

.PHONY: install
install: remove _install clean

.PHONY: register
register: _register clean

.PHONY: upload
upload: _upload install _commit doc

_upload:
	python setup.py sdist upload || echo 'Upload already'

_commit:
	git add .
	git add . -u
	git commit || echo 'No commits'
	git push origin

_register:
	python setup.py register

.PHONY: remove
remove:
	sudo pip uninstall -y $(MODULE) || echo "not installed"

_install:
	sudo pip install -U .

.PHONY: test
test:
	python setup.py test

.PHONY: doc
doc:
	python setup.py build_sphinx --source-dir=docs/ --build-dir=docs/_build --all-files
	python setup.py upload_sphinx --upload-dir=docs/_build/html
