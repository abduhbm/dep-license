import json
import logging
import os
import re
import sys
from collections import OrderedDict
from distutils.core import run_setup
from pathlib import Path

import pkg_resources
import toml
import yaml

logger = logging.getLogger("dep_license")


def extract_project(s: str) -> str:
    match = re.compile("[^=<>~]+").match(s)
    if match is None:
        logger.error(f"could not parse {s}")
        return None
    return match.group(0).strip()


def extract_projects(pp):
    extracted = [extract_project(p) for p in pp]
    return [e for e in extracted if e is not None]


def parse_file(input_file, base_name, dev=False):
    input_file = str(input_file)
    try:
        if base_name == "Pipfile":
            return parse_pip_file(input_file, dev=dev)

        elif base_name == "Pipfile.lock":
            return parse_pip_lock_file(input_file, dev=dev)

        elif base_name == "setup.py":
            return parse_setup_file(input_file)

        elif base_name == "pyproject.toml":
            return parse_pyproject_file(input_file) + parse_pyproject_file_poetry(
                input_file
            )

        elif base_name == "conda.yml":
            return parse_conda_yaml_file(input_file)

        elif base_name == "poetry.lock":
            return parse_poetry_lock_file(input_file)
        else:
            return parse_req_file(input_file)
    except Exception as e:
        logger.error(f"{base_name}: {e}")
        return []


def parse_req_file(input_file):
    lines = Path(input_file).read_text(encoding="utf8").splitlines()
    lines = [x for x in lines if not x.startswith("-")]
    return extract_projects(lines)


def parse_pip_file(input_file, dev=False):
    output = []
    cf = toml.load(input_file)
    output += list(cf.get("packages", {}).keys())
    if dev:
        output += list(cf.get("dev-packages", {}).keys())
    return output


def parse_pip_lock_file(input_file, dev=False):
    output = []
    r_type = ["default"]
    if dev:
        r_type.append("develop")
    with open(input_file, "r") as f:
        cf = json.load(f, object_pairs_hook=OrderedDict)
    if cf:
        for t in r_type:
            output.extend(list(cf[t].keys()))

    return output


def parse_pyproject_file(input_file):
    cf = toml.load(input_file)
    # parse build requirements
    reqs = cf.get("build-system", {}).get("requires", [])
    output = extract_projects(reqs)
    # process poetry runtime dependencies
    # ignore dev deps
    reqs = cf.get("tool", {}).get("poetry", {}).get("dependencies", {})
    output += extract_projects(reqs.keys())
    return output


def parse_pyproject_file_poetry(input_file):
    cf = toml.load(input_file)
    return [
        k
        for k, v in cf.get("tool", {}).get("poetry", {}).get("dependencies", {}).items()
        if not (isinstance(v, dict) and "path" in v) and k not in ["python"]
    ]


def parse_poetry_lock_file(input_file):
    output = []
    cf = toml.load(input_file)
    output = [pkg["name"] for pkg in cf.get("package", []) if "name" in pkg]
    return output


def parse_setup_file(input_file):
    cur_dir = os.getcwd()
    setup_dir = os.path.abspath(os.path.dirname(input_file))
    was_in_path = setup_dir in sys.path
    sys.path.append(setup_dir)
    os.chdir(setup_dir)
    try:
        try:
            setup = run_setup(input_file, stop_after="config")
        except Exception as e:
            logger.error(f"run_setup: {e}")
            logger.debug(f"run_setup: {e}", exc_info=True)
            return []

        reqs_var = ["install_requires", "setup_requires", "extras_require"]
        for v in reqs_var:
            reqs = getattr(setup, v)
            if isinstance(reqs, dict):
                reqs = reqs.values()
            return [extract_project(dep) for dep in reqs]
    finally:
        if not was_in_path:
            sys.path.remove(setup_dir)
        os.chdir(cur_dir)


def parse_conda_yaml_file(input_file):
    with open(input_file, "r") as f:
        cf = yaml.safe_load(f)
    if cf and "dependencies" in cf and isinstance(cf["dependencies"], list):
        reqs = []
        for r in cf["dependencies"]:
            if isinstance(r, dict) and "pip" in r:
                for i in r["pip"]:
                    reqs.append(i)
        return extract_projects(reqs)
    return []
