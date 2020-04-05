[![pyversion Status](https://img.shields.io/pypi/pyversions/resconfig.svg)](https://img.shields.io/pypi/pyversions/resconfig.svg)
[![CircleCI](https://circleci.com/gh/okomestudio/resconfig.svg?style=shield)](https://circleci.com/gh/okomestudio/resconfig)
[![Coverage Status](https://coveralls.io/repos/github/okomestudio/resconfig/badge.svg?branch=development)](https://coveralls.io/github/okomestudio/resconfig?branch=development&kill_cache=1)


# resconfig

*resconfig* is a minimalistic application configuration library for
Python applications. The features include:

- Multiple configuration file formats: INI, JSON, and YAML.

- Dynamic reloading of resource configurations: Watch functions can be
  attached to nested keys, so that the configurations can be reloaded
  and the resources be managed based on the changes while the main
  application stays running.

- Schema: Type casting can be performed based on fixed schema.

- Flexible getter key format: The underlying configuration data
  structure is a nested dict, but the item can be obtained with a
  single key or tuple.


## Installation

``` bash
$ pip install .
```

## Basic Usage

TODO.


## Development

``` bash
$ pip install .[dev]
$ pre-commit install
```

### Running Tests

```bash
$ python setup.py test
```
