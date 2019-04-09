#!/usr/bin/env python
import codecs
import os
import re
import sys

from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install as Install
from setuptools.command.test import test as TestCommand


here = os.path.abspath(os.path.dirname(__file__))


def fread(filename):
    with codecs.open(os.path.join(here, filename), "r", encoding="utf-8") as f:
        return f.read()


def meta(category, fpath="src/resconfig/__init__.py"):
    package_root_file = fread(fpath)
    matched = re.search(
        r"^__{}__\s+=\s+['\"]([^'\"]*)['\"]".format(category), package_root_file, re.M
    )
    if matched:
        return matched.group(1)
    raise Exception("Meta info string for {} undefined".format(category))


version = meta("version")
author = meta("author")
author_email = meta("author_email")
license = meta("license")
readme = fread("README.md")


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


class Verify(Install):
    description = "Verify that the tag and version match"

    def run(self):
        tag = os.getenv("CIRCLE_TAG")
        if tag != "v" + version:
            info = "Git tag: {} does not match the version {}".format(tag, version)
            sys.exit(info)


requires = ["PyYAML>=5.1"]

test_requires = [
    "black==18.9b0",
    "coverage==4.5.2",
    "pre-commit==1.14.4",
    "pytest==4.2.1",
    "pytest-cov==2.6.1",
]


setup(
    name="resconfig",
    version=version,
    description="Application resource configuration library for Python",
    long_description=readme,
    long_description_content_type="text/markdown",
    author=author,
    author_email=author_email,
    url="https://github.com/restlessbandit/resconfig",
    platforms=["Linux"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    packages=find_packages("src"),
    package_data={"": ["LICENSE"]},
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.7",
    license=license,
    scripts=[],
    cmdclass={"test": PyTest, "verify": Verify},
    install_requires=requires,
    tests_require=test_requires,
    extras_require={"test": test_requires},
)
