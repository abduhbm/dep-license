import logging
import distutils
import sys
import os
import pkg_resources
import toml
import json
import yaml
from collections import OrderedDict

# for pip >= 10
try:
    from pip._internal.req import parse_requirements

# for pip <= 9.0.3
except ImportError:
    from pip.req import parse_requirements

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
            return parse_pyproject_file(input_file)

        elif base_name == "conda.yaml":
            return parse_conda_yaml_file(input_file)

        else:
            return parse_req_file(input_file)
    except Exception as e:
        logger.error(f"{base_name}: {e}")
        return []


def parse_req_file(input_file):
    output = []
    for r in parse_requirements(input_file, session="hack"):
        output.append(r.name)

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


def parse_setup_file(input_file):
    output = []
    cur_dir = os.getcwd()
    setup_dir = os.path.abspath(os.path.dirname(input_file))
    sys.path.append(setup_dir)
    os.chdir(setup_dir)
    try:
        setup = distutils.core.run_setup(input_file, stop_after="config")
    except Exception:
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
