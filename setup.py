#!/usr/bin/env python
import codecs
import os
import re

from setuptools import find_packages
from setuptools import setup


def find_meta(category, fpath="src/resconfig/__init__.py"):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, fpath), "r") as f:
        package_root_file = f.read()
    matched = re.search(
        r"^__{}__\s+=\s+['\"]([^'\"]*)['\"]".format(category), package_root_file, re.M
    )
    if matched:
        return matched.group(1)
    raise Exception("Meta info string for {} undefined".format(category))


def _parse_requirements(filename):
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            yield line


def requirements(*filenames):
    reqs = []
    for filename in filenames:
        reqs.extend(_parse_requirements(filename))
    return reqs


setup(
    name="resconfig",
    description="Application resource configuration library for Python",
    author=find_meta("author"),
    version=find_meta("version"),
    platforms=["Linux"],
    classifiers=[],
    package_dir={"": "src"},
    packages=find_packages("src"),
    scripts=[],
    url="https://github.com/restlessbandit/resconfig",
    install_requires=requirements("requirements.txt"),
    extra_require={"dev": requirements("requirements-dev.txt")},
)
