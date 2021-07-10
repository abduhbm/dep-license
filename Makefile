#!/usr/bin/env make
#
# Makefile
#

PACKAGE_NAME=dep_license

install:
	pip3 install . --user

uninstall:
	pip3 uninstall --yes $(PACKAGE_NAME)

install-dev:
	pipenv install --dev
	pipenv run pre-commit install

uninstall-dev:
	pipenv --rm

test:
	pipenv run python -m unittest $(PACKAGE_NAME).tests.tests --failfast --locals --verbose

dist:
	pipenv run python setup.py sdist
	pipenv run python setup.py bdist_wheel
	pipenv run twine check dist/*

upload:
	pipenv run twine upload dist/*
