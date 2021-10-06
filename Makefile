venv:
	python3 -mvenv venv
	venv/bin/pip install --upgrade pip setuptools wheel
	venv/bin/pip install twine

build: venv
	venv/bin/python setup.py sdist bdist_wheel --universal

deploy:
	venv/bin/twine upload dist/*
