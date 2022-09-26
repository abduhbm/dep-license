#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import sys
from shutil import rmtree

from setuptools import Command
from setuptools import find_packages
from setuptools import setup

NAME = "dep_license"
DESCRIPTION = "Report licenses information for dependencies in use by a Python project"
URL = "https://github.com/abduhbm/dep-license"
AUTHOR = "Abdulelah Bin Mahfoodh"

REQUIRED = ["tabulate", "GitPython", "toml", "PyYAML"]

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

with open(os.path.join(here, NAME, "VERSION")) as version_file:
    version = version_file.read().strip()


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPi via Twine…")
        os.system("twine upload dist/*")

        sys.exit()


setup(
    name=NAME,
    version=version,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    # author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=REQUIRED,
    license="MIT",
    keywords="license check dependency package report",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Utilities",
        "Topic :: System :: System Shells",
    ],
    # $ setup.py publish support.
    cmdclass={"upload": UploadCommand},
    entry_points={"console_scripts": ["deplic=dep_license.__main__:main"]},
)
