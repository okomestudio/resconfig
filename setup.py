#!/usr/bin/env python
import codecs
import os
import re
import sys

from setuptools import find_packages
from setuptools import setup
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


requires = ["PyYAML>=5.3.1", "toml>=0.10.0"]

setup_requires = []

dev_requires = ["black>=19.10b0", "flake8>=3.7.9", "isort>=4.3.21", "pre-commit>=2.2.0"]

doc_requires = ["sphinx>=3.0.1"]

tests_require = ["coverage>=5.0.4", "pytest>=5.4.1", "pytest-cov>=2.8.1"]


setup(
    name="resconfig",
    version=version,
    description="A minimalistic application configuration library for Python",
    long_description=readme,
    long_description_content_type="text/markdown",
    author=author,
    author_email=author_email,
    url="https://github.com/okomestudio/resconfig",
    platforms=["Linux"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Installation/Setup",
        "Topic :: Utilities",
    ],
    packages=find_packages("src"),
    package_data={"": ["LICENSE"]},
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.6",
    license=license,
    scripts=[],
    cmdclass={"tests": PyTest},
    install_requires=requires,
    tests_require=tests_require,
    extras_require={
        "dev": dev_requires + tests_require,
        "doc": doc_requires,
        "tests": tests_require,
    },
    entry_points={"console_scripts": []},
)
