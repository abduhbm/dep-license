#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import tempfile
import argparse
import requests
import multiprocessing as mp
from tabulate import tabulate

from dep_license.utils import parse_file

__version__ = open('VERSION', 'r').readline().strip()

SUPPORTED_SITES = ['github.com']
SUPPORTED_FILES = ['requirements.txt', 'Pipfile', 'setup.py']
PYPYI_URL = 'https://pypi.python.org/pypi'
GITHUB_URL = 'https://raw.githubusercontent.com/'


def is_valid_url(url):
    p = requests.utils.urlparse(url)
    return p.scheme in ('http', 'https') and p.netloc in SUPPORTED_SITES


def get_params():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('PROJECT', help='path or URL to the project repo')
    parser.add_argument('-p', '--processes', default='MAX', help='number of processes to run in parallel')
    parser.add_argument('-f', '--format', default='github', help='define how result is formatted')
    parser.add_argument('-o', '--output', default=None, help='path for output file')
    parser.add_argument('-d', '--dev', action='store_true', default=False, help='include dev packages from Pipfile')
    parser.add_argument('-n', '--name', default=None, help='name for pip-requirements file')
    parser.add_argument('-v', '--version', action='version', version=__version__)

    args = parser.parse_args()
    project = args.PROJECT
    np = args.processes
    fmt = args.format
    output = args.output
    dev = args.dev
    name = args.name

    return project, np, fmt, output, dev, name


def chunker_list(seq, size):
    return (seq[i::size] for i in range(size))


def worker(chunk):
    columns = ['Name', 'Meta', 'Classifier']
    records = []
    for d in chunk:
        if not d:
            continue
        record = [d]
        r = requests.get('{}/{}/json'.format(PYPYI_URL, d))
        if r.status_code != 200:
            continue
        output = r.json().get('info')

        meta = output.get('license', '')
        record.append(meta.strip())

        license_class = ''
        classifier = output.get('classifiers', '')
        for c in classifier:
            if c.startswith('License'):
                license_class = '::'.join([x.strip() for x in c.split('::')[1:]])
        record.append(license_class)

        records.append(dict(zip(columns, record)))

    return records


def run():
    project, np, fmt, output_file, dev, name = get_params()
    if name:
        req_files = [name]
    else:
        req_files = SUPPORTED_FILES

    dependencies = []

    if os.path.isdir(os.path.abspath(project)):
        for f in req_files:
            filename = os.path.join(project, f)
            if os.path.isfile(filename):
                dependencies += parse_file(filename, f, dev=dev)

    elif os.path.isfile(os.path.abspath(project)):
        filename = os.path.basename(project)
        if filename in req_files:
            dependencies += parse_file(project, filename, dev=dev)

    elif is_valid_url(project):
        if project.endswith('/'):
            project = project[:-1]

        for f in req_files:
            url = GITHUB_URL + '/'.join(project.split('/')[-2:]) + '/master/' + f
            r = requests.get(url)
            if r.status_code != 200:
                continue
            with tempfile.NamedTemporaryFile(mode='w') as fb:
                lines = [str(l) for l in r.text.splitlines()]
                lines = [l for l in lines if not l.startswith('-r')]
                fb.write('\n'.join(lines))
                fb.seek(0)
                dependencies += parse_file(fb.name, f, dev=dev)
                fb.close()

    else:
        print("Path or URL for the given project is invalid.", file=sys.stderr)
        sys.exit(1)

    dependencies = list(set(dependencies))
    if len(dependencies) == 0:
        print("no dependencies found", file=sys.stderr)
        sys.exit(1)

    if np == 'MAX':
        cpu_count = mp.cpu_count()
    else:
        cpu_count = int(np)

    if len(dependencies) < cpu_count:
        cpu_count = len(dependencies)

    print("Number of dependencies: {}".format(len(dependencies)))
    print("Running with {} processes...".format(cpu_count))

    chunks = chunker_list(dependencies, cpu_count)
    pool = mp.Pool(cpu_count)
    procs = pool.map(worker, chunks)
    pool.terminate()
    pool.close()

    results = []
    for p in procs:
        results += p

    if len(results) == 0:
        print("no license information found", file=sys.stderr)
        sys.exit(1)

    print("licenses:\n")
    output = ''
    fmt = fmt.lower()
    if fmt == 'json':
        import json
        output = json.dumps(results, indent=4)
        print(output)

    else:
        rows = []
        columns = []
        for r in results:
            rows.append(list(r.values()))
            columns = list(r.keys())
        if fmt == 'csv':
            output += ','.join(columns) + '\n'
            for row in rows:
                output += ','.join(row) + '\n'
        else:
            output = tabulate(rows, columns, tablefmt=fmt)
        print(output)

    print(" ")
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
            f.close()
            print("output file is stored in {}".format(os.path.abspath(output_file)))
