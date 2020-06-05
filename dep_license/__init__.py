#!/usr/bin/env python
import argparse
import concurrent.futures
import json
import logging
import os
import subprocess
import sys
import tempfile
import warnings
from urllib.request import urlopen

import git
from tabulate import tabulate

from dep_license.utils import parse_file

logger = logging.getLogger("dep_license")

__version__ = (
    open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION"), "r")
    .readline()
    .strip()
)

SUPPORTED_FILES = [
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "setup.py",
    "conda.yml",
]
PYPYI_URL = "https://pypi.python.org/pypi"
COLUMNS = ["Name", "Meta", "Classifier"]


def is_valid_git_remote(project):
    import git

    g = git.cmd.Git()
    try:
        g.ls_remote(project).split("\n")
        return True
    except Exception:
        return False


def get_params(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("PROJECT", nargs="+", help="path to project or its GIT repo")
    parser.add_argument(
        "-w", "--workers", default=5, help="number of workers to run in parallel"
    )
    parser.add_argument(
        "-f", "--format", default="github", help="define how result is formatted"
    )
    parser.add_argument("-o", "--output", default=None, help="path for output file")
    parser.add_argument(
        "-d",
        "--dev",
        action="store_true",
        default=False,
        help="include dev packages from Pipfile",
    )
    parser.add_argument("-n", "--name", default=None, help="name for dependency file")
    parser.add_argument(
        "-c",
        "--check",
        default=None,
        help="path to a configuration file to check against banned licenses",
    )
    parser.add_argument(
        "-e",
        "--env",
        action="store_true",
        default=False,
        help="check against selected virtual environment in PROJECT",
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args(argv)
    project = args.PROJECT
    w = args.workers
    fmt = args.format
    output = args.output
    dev = args.dev
    name = args.name
    check = args.check
    env = args.env

    return project, w, fmt, output, dev, name, check, env


def worker(d):
    d = d.replace('"', "")
    d = d.replace("'", "")
    record = [d]
    try:
        with urlopen("{}/{}/json".format(PYPYI_URL, d)) as conn:
            output = json.loads(conn.read().decode()).get("info")

    except Exception:
        logger.warning(f"{d}: error in fetching pypi metadata")
        return None

    meta = output.get("license", "")
    record.append(meta.strip())

    license_class = ""
    classifier = output.get("classifiers", "")
    for c in classifier:
        if c.startswith("License"):
            license_class = "::".join([x.strip() for x in c.split("::")[1:]])
    record.append(license_class)

    return dict(zip(COLUMNS, record))


def start_concurrent(dependencies, max_workers=5):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_worker = {executor.submit(worker, x): x for x in dependencies}
        for future in concurrent.futures.as_completed(future_to_worker):
            dependency = future_to_worker[future]
            try:
                data = future.result()
            except Exception as e:  # pragma: no cover
                logger.error(f"{dependency}: {e}")
                continue
            else:
                if data:
                    results.append(data)

    return results


def run(argv=None):
    warnings.simplefilter("ignore", UserWarning)

    projects, max_workers, fmt, output_file, dev, name, check, env = get_params(argv)
    return_val = 0

    if name:
        req_files = [name]
    else:
        req_files = SUPPORTED_FILES

    dependencies = []

    for project in projects:
        if env:
            if sys.platform.startswith("win"):
                py_exec = os.path.join(
                    os.path.abspath(project), "Scripts", "python.exe"
                )
            else:
                py_exec = os.path.join(os.path.abspath(project), "bin/python")
            if not os.path.isfile(py_exec):
                logger.error(f"{py_exec} is invalid virtualenv python executable.")
                logger.error(f"{sys.executable}")
                continue
            try:
                out = subprocess.check_output([py_exec, "-m", "pip", "freeze"])
                if out:
                    with tempfile.NamedTemporaryFile() as f:
                        f.write(out)
                        f.seek(0)
                        dependencies += parse_file(f.name, "requirements.txt", dev=dev)
            except Exception as e:
                raise e

        elif os.path.isdir(os.path.abspath(project)):
            project = os.path.abspath(project)
            for f in req_files:
                filename = os.path.join(project, f)
                if os.path.isfile(filename):
                    dependencies += parse_file(filename, f, dev=dev)

        elif os.path.isfile(os.path.abspath(project)):
            project = os.path.abspath(project)
            filename = os.path.basename(project)
            if filename in req_files:
                dependencies += parse_file(project, filename, dev=dev)

        elif is_valid_git_remote(project):
            temp_dir = tempfile.TemporaryDirectory()
            git.Git(temp_dir.name).clone(project)
            dir_name = os.path.join(
                temp_dir.name, project.rsplit("/", 1)[-1].split(".")[0]
            )
            for f in req_files:
                f_name = os.path.join(dir_name, f)
                if os.path.isfile(f_name):
                    dependencies += parse_file(f_name, f, dev=dev)
            temp_dir.cleanup()

        else:
            logger.error(f"{project} is invalid project.")

    dependencies = list(set(dependencies))
    if len(dependencies) == 0:
        print("no dependencies found")
        return 1

    print("Found dependencies: {}\n".format(len(dependencies)))
    logger.debug("Running with {} workers ...".format(max_workers))

    results = start_concurrent(dependencies, max_workers=max_workers)
    if len(results) == 0:
        logger.error("no license information found")
        return 1

    output = ""
    fmt = fmt.lower()
    if fmt == "json":
        import json

        output = json.dumps(results, indent=4)

    else:
        rows = []
        for r in results:
            rows.append(list(r.values()))
        if fmt == "csv":
            output += ",".join(COLUMNS) + "\n"
            for row in rows:
                output += ",".join(row) + "\n"
        else:
            output = tabulate(rows, COLUMNS, tablefmt=fmt)

    if not check:
        print(output, end="\n")

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
            f.close()
            print("output file is stored in {}".format(os.path.abspath(output_file)))

    if check:
        import configparser
        from difflib import get_close_matches

        if not os.path.isfile(check):
            logger.error("configuration file not found")
            return 1
        config = configparser.ConfigParser()
        config.read(check)
        try:
            banned_licenses = config.get("deplic", "banned")
        except Exception:
            banned_licenses = None

        if banned_licenses:
            banned_licenses = banned_licenses.split(",")
            banned_licenses = [x.lower() for x in banned_licenses]
            for r in results:
                name = r.get("Name")
                meta = r.get("Meta")
                if get_close_matches(meta.lower(), banned_licenses):
                    print(
                        f"\x1b[1;31mBANNED\x1b[0m: "
                        f"\x1b[1;33m{name}\x1b[0m "
                        f"with license \x1b[1;33m{meta}\x1b[0m",
                        end="\n",
                    )
                    return_val = 1

    return return_val
