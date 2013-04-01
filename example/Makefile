VIRTUALENV=$(CURDIR)/.env
PYTHON=$(VIRTUALENV)/bin/python

DJANGO_MANAGER=$(PYTHON) $(CURDIR)/manage.py
DJANGO_SETTINGS=$${DJANGO_SETTINGS_MODULE:-settings.development}
DJANGO_TEST_SETTINGS=$${DJANGO_TEST_SETTINGS_MODULE:-settings.test}
DJANGO_TESTAPP=$${DJANGO_TESTAPP:-main}


$(VIRTUALENV): requirements.txt
	virtualenv --no-site-packages $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install -M -r requirements.txt
	touch $(VIRTUALENV)


# target: help - Display callable targets
.PHONY: help
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g' | sort


# target: clean - Clean project
.PHONY: clean
clean:
	@rm -rf build dist docs/_build
	@rm -f *.py[co]
	@rm -f *.orig
	@rm -f */*.py[co]
	@rm -f */*.orig


# target: run - Run Django devserver
.PHONY: run
run: $(VIRTUALENV)
	$(DJANGO_MANAGER) runserver --settings=$(DJANGO_SETTINGS)


# target: shell - Run Django debug shell
.PHONY: shell
shell: $(VIRTUALENV)
	$(DJANGO_MANAGER) shell --settings=$(DJANGO_SETTINGS)


# target: db - Update database scheme
.PHONY: db
db: $(VIRTUALENV)
	$(DJANGO_MANAGER) syncdb --noinput --settings=$(DJANGO_SETTINGS)
	$(DJANGO_MANAGER) migrate --settings=$(DJANGO_SETTINGS)


# target: t - Run project's tests
.PHONY: t
t: $(VIRTUALENV)
	$(DJANGO_MANAGER) test $(DJANGO_TESTAPP) --settings=$(DJANGO_TEST_SETTINGS)


# target: lint - Audit project code
.PHONY: lint
lint:
	pylama --skip=*/migrations/*,*/settings/*,*/features/*,*/static/*,$(VIRTUALENV)/*


# target: static - Compile project static
.PHONY: static
static:
	$(MANAGER) collectstatic --noinput --clear --settings=$(DJANGO_SETTINGS)
