import pytest

from dep_license import start_concurrent
from dep_license import worker


@pytest.fixture
def dependency():
    return 'dep_license'


@pytest.fixture
def dependency_does_not_exist():
    return 'SomethingThatDoesntExist'


@pytest.fixture
def expected(dependency):
    return {
        "Name": dependency,
        "Meta": "MIT",
        "Classifier": "OSI Approved::MIT License",
    }.items()


def test_worker(dependency, expected):
    assert worker(dependency).items() >= expected


def test_worker_dependency_does_not_exist(dependency_does_not_exist):
    assert worker(dependency_does_not_exist) is None


def test_concurrent_workers(dependency, dependency_does_not_exist, expected):
    results = start_concurrent([dependency, dependency_does_not_exist])
    assert len(results), 1
    assert results[0].items() >= expected
