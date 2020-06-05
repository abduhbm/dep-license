import pytest

from dep_license import start_concurrent
from dep_license import worker


@pytest.mark.parametrize(
    "dependency,expected",
    [
        (
            "dep_license",
            {
                "Name": "dep_license",
                "Meta": "MIT",
                "Classifier": "OSI Approved::MIT License",
            },
        ),
        ("SomethingThatDoesntExist", None),
    ],
)
def test_worker(dependency, expected):
    assert worker(dependency) == expected


def test_concurrent_workers():
    results = start_concurrent(["dep_license", "SomethingElseThatDoesntExist"])
    assert results == [
        {
            "Name": "dep_license",
            "Meta": "MIT",
            "Classifier": "OSI Approved::MIT License",
        }
    ]
