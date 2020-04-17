|license| |versions| |pypi-version| |status| |ci-status| |coverage| |black|


*********
resconfig
*********

*resconfig* is a minimalistic application configuration library for
Python. It is essentially a thin wrapper around nested ``dict``
objects and can:

- Read from multiple configuration file formats: INI, JSON, TOML, and
  YAML.

- Read from environment variables: Configuration can be easily
  overridden with environment variables.

- Read from command-line arguments: Configuration can be easily
  overridden with ``ArgumentParser`` command-line arguments.

- Dynamically reload configuration at run time: Watch functions can be
  attached to any keys within the configuration, so that separate
  resources can be reloaded and managed.

- Access nested configuration item with a “.”-delimited string key:
  The underlying configuration data structure is nested dicts, but no
  need to manually traverse or use the verbose
  ``config["foo"]["bar"]`` form (can use ``config["foo.bar"]``
  instead).

- Apply schema (experimental): Type casting can be performed upon
  loading configuration from files.

For the full documentation, visit `documentation`_.


Installation
============

.. code-block:: sh

    $ pip install resconfig


Quickstart
==========

``ResConfig`` is essentially a thin wrapper around nested ``dict``
objects with added features that make it easy to deal with the data
structure as a centralized storage of application configuration.


The “.”-Style Key Access
------------------------

``ResConfig`` makes it easy to deal with nested configuration items by
supporting the “.”-style notation for nested keys. For example, the
following ways of setting the default configuration are the same.

.. code-block:: python

    from resconfig import ResConfig

    config = ResConfig({"db": {"host": "localhost", "port": 5432}})
    config = ResConfig({"db.host": "localhost", "db.port": 5432})

The access to nested items are similarly easy. The following methods
all return the same value, ``localhost``, given the ``config`` defined
above:

.. code-block:: python

    host = config["db"]["host"]
    host = config["db.host"]
    host = config.get("db.host")  # similar to dict.get


Use with Configuration Files
----------------------------

By supplying file paths, ``ResConfig`` will read the configuration
from the first existing file:

.. code-block:: python

    config = ResConfig(config_files=["myconf.yml",
                                     "~/.myconf.yml,
                                     "/etc/myconf.yml"])

The file format is inferred from the extension. ``ResConfig``
currently understands INI (*.ini*), JSON (*.json*), TOML (*.toml*),
and YAML (*.yaml* or *.yml*). The filename with no extension is
assumed to be of INI.

The current plan is to allow merge from multiple configuration files
with precedence, so that one configuration with higher specificity can
override another with lower specificity. This has not been implemented
yet.


Use with Environment Variables
------------------------------

Often, being able to override configuration with environment variables
is desirable. ``ResConfig`` by default looks for environment variables
that map to configuration keys.

For the configuration items that exist by default, environment
variables can override their values. Say your application, *myapp.py*
has the following default configuration:

.. code-block:: python

    config = ResConfig({"db.host": "localhost", "db.port": 5432})

When you run this app with the ``DB_HOST`` and/or ``DB_PORT``
environment variables set, their values override the default:

.. code-block:: sh

    $ DB_HOST=foo DB_PORT=3306 python myapp.py

That is, ``config["db.host"]`` and ``config["db.port"]`` will return
``foo`` and ``3306``, respectively. As a rule of thumb, a
configuration key maps to an uppercased, “_”-delimited (when nested)
environment variable name as in this example.


Use with ArgumentParser
-----------------------

``argparse.ArgumentParser`` is a standard library tool to add
command-line argument parsing to your application. ``ResConfig`` makes
it easy to add command-line arguments to set configuration values.

By default, the configuration is loaded immediately on the
instantiation of ``ResConfig`` object. You can delay this by setting
the ``load_on_init`` flag to ``False`` and load it yourself at an
appropriate timing. Before loading, you can add arguments dynamically
generated from the default configuration by supplying to the
``ResConfig.add_arguments_to_argparse`` method the ``ArgumentParser``
object, actually parse the arguments, and then calling calling the
``ResConfig.prepare_from_argparse`` method to read the parse result
into the configuration:

.. code-block:: python

    config = ResConfig({"db.host": "localhost",
                        "db.port": 5432},
                       load_on_init=False)

    parser = argparse.ArgumentParser()
    parser.add_argument(...)  # Define other arguments

    config.add_arguments_to_argparse(parser)
    args = parser.parse_args()
    config.prepare_from_argparse(args)
    config.load()

In this case, ``ResConfig.add_arguments_to_argparse`` adds
``--db-host`` and ``--db-port`` as command-line arguments. As a rule
of thumb, a nested key maps to a “-”-delimited long argument.

Alternatively, you may manually define arguments, and let
``ResConfig.prepare_from_argparse`` automatically pick them up, e.g.,

.. code-block:: python

    config = ResConfig({"db.host": "localhost",
                        "db.port": 5432},
                       load_on_init=False)

    parser = argparse.ArgumentParser()
    parser.add_argument(...)  # Define other arguments
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default=5432)
    args = parser.parse_args()
    config.prepare_from_argparse(args)
    config.load()

Here, ``--db-host`` and ``--db-port`` are mapped to
``config["db.host"]`` and ``config["db.port"]``.


Adding Actions on Changes
-------------------------

The ``ResConfig`` object is aware of changes to its
configuration. *Watch functions* can be registered to watch changes
happening at any nested key to act on them. For example,

.. code-block:: python

    import signal
    from resconfig import Action, ResConfig

    config = ResConfig(load_on_init=False)

    @config.watch("nested.key")
    def act_on_nested_key(action, old, new):
        if action == Action.ADDED:
            # Act on the addition of a new value
        elif action == Action.MODIFIED:
            # Act on modification of the value
        elif action == Action.RELOADED:
            # Act on reloading of the value
        elif action == Action.REMOVED:
            # Act on the removal of the value

    def reload(signum=None, stack_frame=None):
        config.reload()

    signal.signal(signal.SIGHUP, reload)  # run reload on SIGHUP

    config.load()  # ready to do the initial config loading

Here, the ``act_on_nested_key`` function is called whenever a change
occurs at the ``nested.key`` in the configuration and can decide what
to do with the ``old`` and/or ``new`` values. In this code, the
configuration reload function is also a handler for the ``SIGHUP``
signal and is triggered when the process receives it, for example,
with ``kill -SIGHUP <pid>``.


Development
===========

.. code-block:: sh

    $ pip install -e .[dev]
    $ pre-commit install


Running Tests
=============

.. code-block:: sh

    $ python setup.py tests


License
=======

`Apache License, Version 2.0`_

.. _Apache License, Version 2.0: https://raw.githubusercontent.com/okomestudio/resconfig/development/LICENSE.txt

.. _documentation: https://resconfig.readthedocs.io/


.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black

.. |ci-status| image:: https://circleci.com/gh/okomestudio/resconfig.svg?style=shield
   :target: https://circleci.com/gh/okomestudio/resconfig
   :alt: CI Status

.. |coverage| image:: https://coveralls.io/repos/github/okomestudio/resconfig/badge.svg?branch=development&kill_cache=1
   :target: https://coveralls.io/github/okomestudio/resconfig?branch=development
   :alt: Coverage

.. |license| image:: https://img.shields.io/pypi/l/resconfig.svg
   :target: https://pypi.org/project/resconfig/
   :alt: License

.. |pypi-version| image:: https://badge.fury.io/py/resconfig.svg
    :target: https://pypi.org/project/resconfig/
    :alt: PyPI Version

.. |status| image:: https://img.shields.io/pypi/status/resconfig.svg
    :target: https://pypi.org/project/resconfig/
    :alt: Package Status

.. |versions| image:: https://img.shields.io/pypi/pyversions/resconfig.svg
   :target: https://img.shields.io/pypi/pyversions/resconfig.svg
   :alt: Versions
