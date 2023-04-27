DJANGO_VERSION ?= 4.2

venv:
	python3 -mvenv venv
	venv/bin/pip install --upgrade pip setuptools wheel

build: venv
	venv/bin/pip install twine
	venv/bin/python setup.py sdist bdist_wheel --universal

deploy:
	venv/bin/twine upload dist/*

test: venv
	xargs venv/bin/pip install --upgrade "django==$(DJANGO_VERSION).*" < test-requirements.txt
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.settings venv/bin/django-admin test
