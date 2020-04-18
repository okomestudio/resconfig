#!/usr/bin/env python
import codecs
import os
import re

from setuptools import find_packages
from setuptools import setup

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
readme = fread("README.rst")


requires = []
toml_requires = ["toml>=0.10.0"]
yaml_requires = ["PyYAML>=5.3.1"]

setup_requires = ["pytest-runner>=5.2"]

dev_requires = (
    [
        "black>=19.10b0",
        "flake8>=3.7.9",
        "isort[pyproject]>=4.3.21",
        "pre-commit>=2.2.0",
        "seed-isort-config>=2.1.1",
    ]
    + toml_requires
    + yaml_requires
)

doc_requires = ["sphinx>=3.0.1", "sphinx_autodoc_typehints>=1.10.3"]

tests_require = (
    ["coverage[toml]>=5.0.4", "pytest>=5.4.1", "pytest-cov>=2.8.1"]
    + toml_requires
    + yaml_requires
)


setup(
    name="resconfig",
    version=version,
    description="A minimalistic application configuration library for Python",
    long_description=readme,
    long_description_content_type="text/x-rst",
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
    install_requires=requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    extras_require={
        "dev": dev_requires + tests_require,
        "doc": doc_requires,
        "tests": tests_require,
        "toml": toml_requires,
        "yaml": yaml_requires,
    },
    entry_points={"console_scripts": []},
)
