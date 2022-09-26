import json
import logging
import os
import sys
from collections import OrderedDict

import pkg_resources
import toml
import yaml
from distutils.core import run_setup

logger = logging.getLogger("__name__")


def parse_file(input_file, base_name, dev=False):
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
    output = []
    with open(input_file) as f:
        lines = [x for x in f.readlines() if not x.startswith("-")]
        for line in lines:
            try:
                for r in pkg_resources.parse_requirements(line):
                    output.append(r.name)
            except pkg_resources.RequirementParseError:
                pass

    return output


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
    output = []
    cf = toml.load(input_file)
    reqs = cf.get("build-system", {}).get("requires", [])
    for i in pkg_resources.parse_requirements(reqs):
        output.append(i.project_name)
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
    output = []
    cur_dir = os.getcwd()
    setup_dir = os.path.abspath(os.path.dirname(input_file))
    sys.path.append(setup_dir)
    os.chdir(setup_dir)
    try:
        setup = run_setup(input_file, stop_after="config")
    except Exception as e:
        logger.error(f"run_setup: {e}")
        return []

    reqs_var = ["install_requires", "setup_requires", "extras_require"]
    for v in reqs_var:
        reqs = getattr(setup, v)
        if isinstance(reqs, list):
            for i in pkg_resources.parse_requirements(reqs):
                output.append(i.project_name)

        elif isinstance(reqs, dict):
            for i in pkg_resources.parse_requirements(
                {v for req in reqs.values() for v in req}
            ):
                output.append(i.project_name)
    os.chdir(cur_dir)
    return output


def parse_conda_yaml_file(input_file):
    output = []
    with open(input_file, "r") as f:
        cf = yaml.safe_load(f)
    if cf and "dependencies" in cf and isinstance(cf["dependencies"], list):
        reqs = []
        for r in cf["dependencies"]:
            if isinstance(r, dict) and "pip" in r:
                for i in r["pip"]:
                    reqs.append(i)
        for i in pkg_resources.parse_requirements(reqs):
            output.append(i.project_name)

    return output
