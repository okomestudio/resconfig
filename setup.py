#!/usr/bin/env python
import codecs
import os
import re
import sys

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["-vv", "--cov=src/resconfig", "--cov-report=term-missing"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def meta(category, fpath="src/resconfig/__init__.py"):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, fpath), "r") as f:
        package_root_file = f.read()
    matched = re.search(
        r"^__{}__\s+=\s+['\"]([^'\"]*)['\"]".format(category), package_root_file, re.M
    )
    if matched:
        return matched.group(1)
    raise Exception("Meta info string for {} undefined".format(category))


requires = []

test_requires = [
    "black==18.9b0",
    "coverage==4.5.2",
    "pre-commit==1.14.4",
    "pytest==4.2.1",
    "pytest-cov==2.6.1",
]


setup(
    name="resconfig",
    version=meta("version"),
    description="Application resource configuration library for Python",
    author=meta("author"),
    url="https://github.com/restlessbandit/resconfig",
    platforms=["Linux"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    packages=find_packages("src"),
    package_data={"": ["LICENSE"]},
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.7",
    license=meta("license"),
    scripts=[],
    cmdclass={"test": PyTest},
    install_requires=requires,
    tests_require=test_requires,
)
