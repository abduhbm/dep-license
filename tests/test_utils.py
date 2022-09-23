import pytest

from dep_license import utils


def test_parsing_requirement_file(tmpdir):
    x = tmpdir.join("requirements.txt")
    x.write("dep_license==0.0.0\n" "pytest")
    assert utils.parse_req_file(x.strpath) == ["dep_license", "pytest"]


def test_parsing_pip_file(tmpdir):
    x = tmpdir.join("Pipfile")
    x.write(
        """
        [[source]]
        url = "https://pypi.org/simple"
        verify_ssl = true
        name = "pypi"
        [packages]
        flask = "*"
        dep_license = "*"
        [dev-packages]
        pytest = "*"
        [requires]
        python_version = "3.7"
        """
    )
    assert utils.parse_pip_file(x.strpath) == ["flask", "dep_license"]
    assert utils.parse_pip_file(x.strpath, dev=True) == [
        "flask",
        "dep_license",
        "pytest",
    ]


def test_parsing_pip_lock_file(tmpdir):
    x = tmpdir.join("Pipfile.lock")
    x.write(
        """
        {
            "_meta": {
                "hash": {
                    "sha256": "6e593b27afd61ba861fc65b67a1b68a2ff296053aa3f08a628a27174df727652"
                },
                "pipfile-spec": 6,
                "requires": {},
                "sources": [
                    {
                        "name": "pypi",
                        "url": "https://pypi.org/simple",
                        "verify_ssl": true
                    }
                ]
            },
            "default": {
                "certifi": {
                    "hashes": [
                        "sha256:54a07c09c586b0e4c619f02a5e94e36619da8e2b053e20f594348c0611803704",
                        "sha256:40523d2efb60523e113b44602298f0960e900388cf3bb6043f645cf57ea9e3f5"
                    ],
                    "version": "==2017.7.27.1"
                }
            },
            "develop": {
                "pytest": {
                    "hashes": [
                        "sha256:b84f554f8ddc23add65c411bf112b2d88e2489fd45f753b1cae5936358bdf314",
                        "sha256:f46e49e0340a532764991c498244a60e3a37d7424a532b3ff1a6a7653f1a403a"
                    ],
                    "version": "==3.2.2"
                }
            }
        }
        """
    )
    assert utils.parse_pip_lock_file(x.strpath) == ["certifi"]
    assert utils.parse_pip_lock_file(x.strpath, dev=True) == ["certifi", "pytest"]


def test_parsing_setup_file(tmpdir):
    x = tmpdir.join("setup.py")
    x.write(
        "from setuptools import setup, find_packages\n"
        'REQUIRED = ["tabulate", "numpy", "toml"]\n'
        'setup(name="foo", version="1.0", install_requires=REQUIRED)'
    )
    assert utils.parse_setup_file(x.strpath) == ["tabulate", "numpy", "toml"]


def test_parsing_pyproject_file(tmpdir):
    x = tmpdir.join("pyproject.toml")
    x.write(
        """
        [build-system]
        requires = ["setuptools", "wheel", "numpy"]
        """
    )
    assert utils.parse_pyproject_file(x.strpath) == ["setuptools", "wheel", "numpy"]


def test_parsing_pyproject_file_poetry(tmpdir):
    x = tmpdir.join("pyproject.toml")
    x.write(
        """
        [tool.poetry.dependencies]
        python = ">=3.8,<3.11"
        pandas = "^1.4.3"
        fastapi = "^0.79.0"
        numpy = "^1.23.1"

        mkdocs  = { version = "^1.1.2", optional = true}
        jinja2 = { version = "^2.10.2", optional = true }
        MarkupSafe = { version = "2.0.1", optional = true }
        mkdocs-include-markdown-plugin  = { version = "^1.0.0", optional = true}
        mkdocs-material  = { version = "^6.1.7", optional = true}
        mkdocstrings  = { version = "^0.17.0", optional = true}
        mkdocs-material-extensions  = { version = "^1.0.1", optional = true}
        mkdocs-autorefs = {version = "^0.2.1", optional = true}
        pytkdocs = {extras = ["numpy-style"], version = "^0.15.0", optional = true}
        mkdocs-gen-files = {version = "^0.3.3", python = "^3.7", optional = true}
        mkdocs-literate-nav = {version = "^0.4.1", optional = true}
        bump2version = {version = "^1.0.1", optional = true}

        pytest  = { version = "^6.2.4", optional = true}
        pytest-cov  = { version = "^2.12.0", optional = true}

        types-pyyaml = [{optional = true, version = "*"}]
        typing_extensions = [{optional = true, version = "*"}]
        mypy = [{optional = true, version = "*"}]

        pandas-stubs = [{optional = true, version = "^1.4.3"}]
        """
    )
    assert utils.parse_pyproject_file_poetry(x.strpath) == [
        "pandas",
        "fastapi",
        "numpy",
        "mkdocs",
        "jinja2",
        "MarkupSafe",
        "mkdocs-include-markdown-plugin",
        "mkdocs-material",
        "mkdocstrings",
        "mkdocs-material-extensions",
        "mkdocs-autorefs",
        "pytkdocs",
        "mkdocs-gen-files",
        "mkdocs-literate-nav",
        "bump2version",
        "pytest",
        "pytest-cov",
        "types-pyyaml",
        "typing_extensions",
        "mypy",
        "pandas-stubs",
    ]


def test_parsing_conda_yaml_file(tmpdir):
    x = tmpdir.join("conda.yml")
    x.write(
        """
        name: hyperparam_example
        channels:
          - defaults
          - anaconda
          - conda-forge
        dependencies:
          - python=3.6
          - pip:
            - numpy==1.14.3
            - pandas==0.22.0
        """
    )
    assert utils.parse_conda_yaml_file(x.strpath) == ["numpy", "pandas"]


@pytest.mark.parametrize(
    "f", ("requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock", "conda.yml")
)
def test_passing_dependency_file(f, tmpdir):
    x = tmpdir.join(f)
    x.write(" ")
    r = utils.parse_file(x.strpath, f)
    assert r == []
