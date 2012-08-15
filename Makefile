MODULE=adrest
SPHINXBUILD=sphinx-build
ALLSPHINXOPTS= -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
BUILDDIR=_build


clean:
	sudo rm -rf build dist docs/_build
	find . -name "*.pyc" -delete
	find . -name "*.orig" -delete

install: remove _install clean

register: _register clean

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

remove:
	sudo pip uninstall -y $(MODULE) || echo "not installed"

_install:
	sudo pip install -U .

test:
	python setup.py test

doc:
	python setup.py build_sphinx --source-dir=docs/ --build-dir=docs/_build --all-files
	python setup.py upload_sphinx --upload-dir=docs/_build/html
