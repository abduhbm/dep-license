# dep_license

Report licenses information for dependencies in use by a Python project

### Installation

```
$ pip install dep_license
```

### Usage

```
$ deplic --help
usage: deplic [-h] [-n PROCESSES] [-f FORMAT] [-o OUTPUT] PROJECT

positional arguments:
  PROJECT               path or URL to the project repo

optional arguments:
  -h, --help            show this help message and exit
  -n PROCESSES, --processes PROCESSES
                        number of processes to run in parallel (default: MAX)
  -f FORMAT, --format FORMAT
                        define how result is formatted (default: github)
  -o OUTPUT, --output OUTPUT
                        path for output file (default: None)
```

### Example

