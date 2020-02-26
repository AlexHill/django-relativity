venv:
	python3 -m env
	venv/bin/pip install setuptools wheel twine

build: venv
	venv/bin/python setup.py sdist bdist_wheel --universal

deploy:
	venv/bin/twine upload dist/*
