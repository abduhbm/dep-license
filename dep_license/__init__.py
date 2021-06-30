#!/usr/bin/env python
import argparse
import concurrent.futures
import json
import logging
import os
import stat
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path
from shutil import rmtree
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


def readonly_handler(func, path, execinfo):
    """
    Work-around for python problem with shutils tree remove functions on Windows.
    See:
        https://stackoverflow.com/questions/23924223
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


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
        nargs="?",
        const="setup.cfg",
        default=None,
        help="path to a configuration file to check against banned licenses",
    )
    parser.add_argument(
        "-e",
        "--env",
        action="store_true",
        default=False,
        help="check against selected python executable",
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

    projects, max_workers, fmt, output_file, dev, name, check, env = get_params(argv)
    return_val = 0

    if name:
        req_files = [name]
    else:
        req_files = SUPPORTED_FILES

    dependencies = []

    for project in projects:
        p_path = Path(project).absolute()
        if env:
            if not p_path.isfile():
                logger.error(f"{project} is invalid python executable.")
                continue
            try:
                out = subprocess.check_output([project, "-m", "pip", "freeze"])
                if out:
                    f = None
                    try:
                        f = tempfile.NamedTemporaryFile(delete=False)
                        f.write(out)
                        f.close()
                        dependencies += parse_file(f.name, "requirements.txt", dev=dev)
                    finally:
                        if f is not None:
                            os.remove(f.name)
            except Exception:
                logger.error(f"{project}: error in freezing dependencies.")

        elif p_path.isdir():
            for f in req_files:
                filename = Path(project) / f
                if filename.isfile():
                    dependencies += parse_file(filename, f, dev=dev)

        elif p_path.isfile():
            filename = p_path.parent
            if filename in req_files:
                dependencies += parse_file(project, filename, dev=dev)

        elif is_valid_git_remote(project):
            temp_dir = tempfile.TemporaryDirectory()
            git.Git(temp_dir.name).clone(project)
            dir_name = Path(temp_dir.name) / project.rsplit("/", 1)[-1].split(".")[0]
            for f in req_files:
                f_name = dir_name / f
                if f_name.isfile():
                    dependencies += parse_file(f_name, f, dev=dev)
            if sys.platform.startswith("win"):
                rmtree(temp_dir.name, onerror=readonly_handler)
            else:
                temp_dir.cleanup()

        else:
            logger.error(f"{project} is invalid project.")

    dependencies = list(set(dependencies))
    if len(dependencies) == 0:
        print("no dependencies found")
        return 1

    print(f"Found dependencies: {len(dependencies)}\n")
    logger.debug(f"Running with {max_workers} workers ...")

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
        rows = [list(r.values()) for r in results]
        if fmt == "csv":
            output += ",".join(COLUMNS) + "\n"
            for row in rows:
                output += ",".join([f'"{r}"' for r in row]) + "\n"
        else:
            output = tabulate(rows, COLUMNS, tablefmt=fmt)

    if not check:
        print(output, end="\n")

    if output_file:
        Path(output_file).write_text(output, encoding="utf8")
        print(f"output file is stored in {Path(output_file).absolute()}")

    if check:
        import configparser
        from difflib import get_close_matches

        if not Path(check).isfile():
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
            banned_licenses = [x.lower().strip() for x in banned_licenses if x]
            banned_licenses = list(set(banned_licenses))
            for r in results:
                name = r.get("Name")
                meta = r.get("Meta")
                classifier = r.get("Classifier")
                if get_close_matches(
                    meta.lower().replace("license", "").strip(), banned_licenses
                ) or get_close_matches(
                    classifier.lower()
                    .replace("license", "")
                    .replace("osi approved::", "")
                    .strip(),
                    banned_licenses,
                ):
                    print(
                        f"\x1b[1;31mBANNED\x1b[0m: "
                        f"\x1b[1;33m{name}\x1b[0m "
                        f":: \x1b[1;33m{meta} - {classifier}\x1b[0m",
                        end="\n",
                    )
                    return_val = 1

    return return_val
