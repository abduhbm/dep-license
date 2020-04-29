# dep_license

**dep_lic**: a simple utility to report licenses information for dependencies in use by a Python project. It supports parsing contents from `setup.py`, `pyproject.toml`, `requirements.txt` and `Pipfile` files from the project directory or its GIT repo.

### Installation

```
$ pip install dep_license
```

### Command-Line Options

```
$ deplic --help
usage: deplic [-h] [-p PROCESSES] [-f FORMAT] [-o OUTPUT] [-d] [-n NAME]
              [-c CHECK] [-v]
              PROJECT

positional arguments:
  PROJECT               path to project or its GIT repo

optional arguments:
  -h, --help            show this help message and exit
  -p PROCESSES, --processes PROCESSES
                        number of processes to run in parallel (default: MAX)
  -f FORMAT, --format FORMAT
                        define how result is formatted (default: github)
  -o OUTPUT, --output OUTPUT
                        path for output file (default: None)
  -d, --dev             include dev packages from Pipfile (default: False)
  -n NAME, --name NAME  name for pip-requirements file (default: None)
  -c CHECK, --check CHECK
                        path to a configuration file to check against banned
                        licenses (default: None)
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
banned = AGPL
# or comma separated values
# banned = AGPL,....
```
```
$ deplic --check ./deplic.cfg https://github.com/edx/edx-enterprise

BANNED: django-config-models with license AGPL 3.0
BANNED: code-annotations with license AGPL 3.0
BANNED: edx-opaque-keys with license AGPL-3.0
BANNED: edx-rbac with license AGPL 3.0
BANNED: edx-django-utils with license AGPL 3.0
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
