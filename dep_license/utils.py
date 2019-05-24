import os
# for pip >= 10
try:
    from pip._internal.req import parse_requirements
    from pip._internal.download import PipSession
# for pip <= 9.0.3
except ImportError:
    from pip.req import parse_requirements
    from pip.download import PipSession

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def parse_file(input_file, base_name, dev=False):
    if base_name == 'Pipfile':
        return parse_pip_file(input_file, dev=dev)

    elif base_name == 'setup.py':
        return parse_setup_file(input_file)

    else:
        return parse_req_file(input_file)


def parse_req_file(input_file):
    output = []
    for r in parse_requirements(input_file, session=PipSession()):
        output.append(r.name)

    return output


def parse_pip_file(input_file, dev=False):
    output = []
    cf = configparser.ConfigParser()
    with open(input_file) as f:
        cf.read_file(f)
        output += list(dict(cf.items('packages')).keys())
        if dev:
            output += list(dict(cf.items('dev-packages')).keys())

    return output


def parse_setup_file(input_file):
    # TODO: add support to parse setup.py
    return []