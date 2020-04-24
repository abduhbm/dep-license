import logging
import distutils
import sys
import os
import pkg_resources

# for pip >= 10
try:
    from pip._internal.req import parse_requirements

# for pip <= 9.0.3
except ImportError:
    from pip.req import parse_requirements

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

logger = logging.getLogger(__name__)


def parse_file(input_file, base_name, dev=False):
    try:
        if base_name == "Pipfile":
            return parse_pip_file(input_file, dev=dev)

        elif base_name == "setup.py":
            return parse_setup_file(input_file)

        else:
            return parse_req_file(input_file)
    except Exception as e:
        logger.error(e)
        return []


def parse_req_file(input_file):
    output = []
    for r in parse_requirements(input_file, session="hack"):
        output.append(r.name)

    return output


def parse_pip_file(input_file, dev=False):
    output = []
    cf = configparser.ConfigParser()
    with open(input_file) as f:
        cf.read_file(f)
        output += list(dict(cf.items("packages")).keys())
        if dev:
            output += list(dict(cf.items("dev-packages")).keys())
    return output


def parse_setup_file(input_file):
    output = []
    cur_dir = os.getcwd()
    setup_dir = os.path.abspath(os.path.dirname(input_file))
    sys.path.append(setup_dir)
    os.chdir(setup_dir)
    setup = distutils.core.run_setup(input_file)
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
