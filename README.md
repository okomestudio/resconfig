[![pyversion Status](https://img.shields.io/pypi/pyversions/resconfig.svg)](https://img.shields.io/pypi/pyversions/resconfig.svg)
[![CircleCI](https://circleci.com/gh/okomestudio/resconfig.svg?style=shield)](https://circleci.com/gh/okomestudio/resconfig)
[![Coverage Status](https://coveralls.io/repos/github/okomestudio/resconfig/badge.svg?branch=development)](https://coveralls.io/github/okomestudio/resconfig?branch=development&kill_cache=1)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# resconfig

*resconfig* is a minimalistic application configuration library for
Python. It can:

- Read from multiple configuration file formats: INI, JSON, TOML, and
  YAML.

- Dynamically reload configuration at run time: Watch functions can be
  attached to any keys within the configuration, so that separate
  resources can be reloaded and managed.

- Apply schema: Type casting can be performed.

- Access nested configuration item with a '.'-delimited string key:
  The underlying configuration data structure is nested dicts, but no
  need to manually traverse or use the verbose `dict[k1][k2]` form.


## Installation

``` bash
$ pip install resconfig
```

## Basic Usage

``` python
from resconfig import ResConfig

config = ResConfig()  # create empty config
config.load_from_yaml("pg.yaml")  # load config from file
config.get("pg.dbname")  # get value at config["pg"]["dbname"]
config = ResConfig({"pg": {"dbname": "foo"}})  # with default config
```

### Reloading Configuration

``` python
import signal

from resconfig import ResConfig

config = ResConfig()

conn = None


@config.watch("pg")
def pg_conn(action, old, new):
    nonlocal conn
    if action == Action.ADDED:
        conn = psycopg2.connect(dbname=new.get("dbname"))
    elif action in (Action.MODIFIED, Action.RELOADED):
        conn.close()
        conn = psycopg2.connect(dbname=new.get("dbname"))
    elif action == Action.REMOVED:
        conn.close()


def reload(*args):
    config.load_from_yaml("pg.yaml")


signal.signal(signal.SIGHUP, reload)
```


## Development

``` bash
$ pip install .[dev]
$ pre-commit install
```

### Running Tests

``` bash
$ python setup.py test
```

## License

[Apache License, Version 2.0](https://raw.githubusercontent.com/okomestudio/resconfig/development/LICENSE.txt
)
