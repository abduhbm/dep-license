dep_license
===========

[![CI](https://github.com/abduhbm/dep-license/workflows/CI/badge.svg?branch=master)](https://github.com/abduhbm/dep-license/actions?query=workflow%3A%22CI%22)
[![PyPI version](https://img.shields.io/pypi/v/dep-license.svg)](https://pypi.python.org/pypi/dep-license)

**dep_license (deplic)**: a simple utility to report licenses information for dependencies in use by a Python project.

deplic supports reporting dependencies from local project directories, local / remote `git` repos,
or selected virtual environment paths.

Supported dependency files:
* `setup.py`
* `setup.cfg`
* `requirements.txt`
* `pyproject.toml`
* `Pipfile`
* `Pipfile.lock`
* `conda.yaml`
* `poetry.lock`

### Installation

```
$ pip install dep_license
```

### Command-Line Options

```
usage: deplic [-h] [-w WORKERS] [-f FORMAT] [-o OUTPUT] [-d] [-n NAME]
              [-c CHECK] [-e] [-v]
              PROJECT [PROJECT ...]

positional arguments:
  PROJECT               path to project or its GIT repo

optional arguments:
  -h, --help            show this help message and exit
  -w WORKERS, --workers WORKERS
                        number of workers to run in parallel (default: 5)
  -f FORMAT, --format FORMAT
                        define how result is formatted (default: github)
  -o OUTPUT, --output OUTPUT
                        path for output file (default: None)
  -d, --dev             include dev packages from Pipfile (default: False)
  -n NAME, --name NAME  name for dependency file (default: None)
  -c CHECK, --check CHECK
                        path to a configuration file to check against banned
                        licenses (default: None)
  -e, --env             check against selected python executable (default:
                        False)
  -v, --version         show program's version number and exit
```

### Usage

Report a list of dependency licenses used in a local project:
```
$ deplic /path/to/python/project
Found dependencies: 3

| Name       | Meta   | Classifier                                       |
|------------|--------|--------------------------------------------------|
| pandas     | BSD    |                                                  |
| matplotlib | PSF    | OSI Approved::Python Software Foundation License |
| numpy      | BSD    | OSI Approved                                     |
```

Specify the file to be parsed:

```
$ deplic /path/to/python/project/requirements.txt
Found dependencies: 1

| Name   | Meta   | Classifier   |
|--------|--------|--------------|
| numpy  | BSD    | OSI Approved |

```

Support for Pipfile:
```
$ deplic /path/to/python/project/Pipfile
Found dependencies: 3

| Name       | Meta   | Classifier                                       |
|------------|--------|--------------------------------------------------|
| numpy      | BSD    | OSI Approved                                     |
| pandas     | BSD    |                                                  |
| matplotlib | PSF    | OSI Approved::Python Software Foundation License |
```

Report from selected `virtualenv` path:
```
deplic $VIRTUAL_ENV/bin/python --env
Found dependencies: 3

| Name               | Meta                                 | Classifier                                       |
|--------------------|--------------------------------------|--------------------------------------------------|
| smmap              | BSD                                  | OSI Approved::BSD License                        |
| tabulate           | MIT                                  | OSI Approved::MIT License                        |
| six                | MIT                                  | OSI Approved::MIT License                        |
```

Format and store output as JSON file:
```
deplic /path/to/python/project -f json -o dep-licenses.json
Found dependencies: 3

[
    {
        "Name": "matplotlib",
        "Meta": "PSF",
        "Classifier": "OSI Approved::Python Software Foundation License"
    },
    {
        "Name": "pandas",
        "Meta": "BSD",
        "Classifier": ""
    },
    {
        "Name": "numpy",
        "Meta": "BSD",
        "Classifier": "OSI Approved"
    }
]
```

Get the list dev-packages from the project's GIT repo:
```
$ deplic https://github.com/kennethreitz/requests -p 16 -d -f md
Found dependencies: 16
Running with 16 processes...

Name             Meta                                                          Classifier
---------------  ------------------------------------------------------------  -------------------------------------
pytest           MIT license                                                   OSI Approved::MIT License
codecov          http://www.apache.org/licenses/LICENSE-2.0                    OSI Approved::Apache Software License
pytest-mock      MIT                                                           OSI Approved::MIT License
sphinx           BSD                                                           OSI Approved::BSD License
tox              MIT                                                           OSI Approved::MIT License
pytest-httpbin   MIT                                                           OSI Approved::MIT License
docutils         public domain, Python, 2-Clause BSD, GPL 3 (see COPYING.txt)  Public Domain
pytest-cov       MIT                                                           OSI Approved::BSD License
pytest-xdist     MIT                                                           OSI Approved::MIT License
pysocks          BSD
httpbin          MIT                                                           OSI Approved::MIT License
alabaster                                                                      OSI Approved::BSD License
readme-renderer  Apache License, Version 2.0                                   OSI Approved::Apache Software License
detox            MIT                                                           OSI Approved::MIT License

```

Specify which requirements file to parse:
```
$ deplic https://github.com/pandas-dev/pandas -n requirements-dev.txt -f csv -p 16 -o pandas_dev.csv
```

Run a check against banned licenses listed in a configuration file:
```bash
$ more deplic.cfg
```
```ini
[deplic]
banned = AGPL-3.0
# or multi-lines
# banned =
#     AGPL-3.0,
#     ...
```

```
$ deplic --check ./deplic.cfg /path/to/working/project

BANNED: edx-opaque-keys :: AGPL-3.0 - OSI Approved::GNU Affero General Public License v3
BANNED: edx-rbac :: AGPL 3.0 - OSI Approved::GNU Affero General Public License v3 or later (AGPLv3+)
BANNED: edx-django-utils :: AGPL 3.0 - OSI Approved::GNU Affero General Public License v3 or later (AGPLv3+)
BANNED: django-config-models :: AGPL 3.0 - OSI Approved::GNU Affero General Public License v3 or later (AGPLv3+)
```

### Using dep-license in Docker
```bash
$ docker run -t -v $PWD:/stage abduh/dep-license deplic /stage
Found dependencies: 1

| Name         | Meta   | Classifier                |
|--------------|--------|---------------------------|
| editdistance |        | OSI Approved::MIT License |
```

### Output Formats:

Supported table formats are (thanks to python-tabulate package):

- "plain"
- "simple"
- "github"
- "grid"
- "fancy_grid"
- "pipe"
- "orgtbl"
- "jira"
- "presto"
- "psql"
- "rst"
- "mediawiki"
- "moinmoin"
- "youtrack"
- "html"
- "latex"
- "latex_raw"
- "latex_booktabs"
- "textile"
- "csv"
