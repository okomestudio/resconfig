[![pyversion Status](https://img.shields.io/pypi/pyversions/resconfig.svg)](https://img.shields.io/pypi/pyversions/resconfig.svg)
[![CircleCI](https://circleci.com/gh/okomestudio/resconfig.svg?style=shield)](https://circleci.com/gh/okomestudio/resconfig)
[![Coverage Status](https://coveralls.io/repos/github/okomestudio/resconfig/badge.svg?branch=development)](https://coveralls.io/github/okomestudio/resconfig?branch=development&kill_cache=1)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# resconfig

*resconfig* is a minimalistic application configuration library for
Python. It is essentially a thin wrapper around nested `dict`s and
can:

- Read from multiple configuration file formats: INI, JSON, TOML, and
  YAML.

- Dynamically reload configuration at run time: Watch functions can be
  attached to any keys within the configuration, so that separate
  resources can be reloaded and managed.

- Access nested configuration item with a `.`-delimited string key:
  The underlying configuration data structure is nested dicts, but no
  need to manually traverse or use the verbose `config["foo"]["bar"]`
  form (can use `config["foo.bar"]` instead).

- Apply schema (experimental): Type casting can be performed upon
  loading configuration from files.


## Installation

``` bash
$ pip install resconfig
```

## Basic Usage

``` python
from resconfig import ResConfig

config = ResConfig()              # create empty config
config.load_from_yaml("pg.yaml")  # load config from YAML file
dbname = config.get("pg.dbname")  # get value at config["pg"]["dbname"]
```

``` python
config = ResConfig({"pg": {"dbname": "foo"}})  # with default config
config = ResConfig({"pg.dbname": "foo"}})      # this also works
```


### Watching for Configuration Changes

The `ResConfig` object is aware of changes to its
configuration. *Watch functions* can be registered to watch changes
happening at any nested key to act on them. For example,

``` python
import signal

from resconfig import Action, ResConfig

config = ResConfig(skip_reload_on_init=True)  # do not immediately load config


@config.watch("nested.key")
def act_on_nested_key(action, old, new):
    if action == Action.ADDED:
        # ... do something when the new value is added to nested.key ...
    elif action == Action.MODIFIED:
        # ... do something when the value at nested.key is modified ...
    elif action == Action.RELOADED:
        # ... do something when the value at nested.key is reloaded ...
    elif action == Action.REMOVED:
        # ... do something when the value at nested.key is removed ...


def reload(signum=None, stack_frame=None):
    config.load_from_yaml("myconf.yml")


signal.signal(signal.SIGHUP, reload)  # run reload on receiving SIGHUP signal

reload()  # ready to do the initial config loading
```

Here, the `act_on_nested_key` function is invoked whenever an action
occurs at the *nested.key* of the configuration and can decide what to
do with the `old` and/or `new` values. In this code, the configuration
reload function is also a signal handler for `SIGHUP` and is triggered
on the process receiving the signal.

The same watch function above can be registered in a couple more
different ways, via the method

``` python
config.register("nested.key", act_on_nested_key)
```

or as an argument to `ResConfig`

``` python
config = ResConfig(watchers={"nested.key": act_on_nested_key})
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
