|license| |versions| |pypi-version| |status| |ci-status| |coverage| |black|


*********
resconfig
*********

*resconfig* is a minimalistic application configuration library for
Python. It is a thin wrapper around nested ``dict`` objects with added
features that make it easy to deal with the data structure as a
centralized storage of application configuration.

``ResConfig`` supports

- multiple configuration file formats: INI, JSON, TOML, and YAML;

- environment variables: Configuration can be easily overridden with
  environment variables;

- command-line arguments: Configuration can be easily overridden with
  ArgumentParser command-line arguments.

- “.”-delimited nested keys: ``config["foo.bar"]`` is equivalent to
  ``config["foo"]["bar"]``.

The advanced usage of ``ResConfig`` allows:

- Dynamic reloading of configuration at run time: Watch functions can
  be attached to any keys within the configuration to trigger actions
  to manage resources.

For the full documentation, visit `documentation`_.


Installation
============

.. code-block:: sh

    $ pip install resconfig


Quickstart
==========

Let us first create an ``ResConfig`` object with a simple default
configuration for your application, *myapp.py*:

.. code-block:: python

    from resconfig ResConfig

    config = ResConfig({"db": {"host": "localhost", "port": 5432}})

By default, ``ResConfig`` loads configuration immediately after its
initialization. To control the timing of load, use the
``load_on_init`` flag:

.. code-block:: python

    config = ResConfig({"db": {"host": "localhost", "port": 5432}},
                       load_on_init=False)
    config.load()

The following sections introduce you to the basic usage of
``ResConfig`` object.


The “.”-Style Key Notation
--------------------------

``ResConfig`` exposes ``dict``-like interface for value access but
additionally allows the “.”-style notation for nested keys. The
following methods all return the same value, ``localhost``:

.. code-block:: python

    host = config["db"]["host"]
    host = config["db.host"]
    host = config.get("db.host")  # similar to dict.get

The “.”-style can be used elsewhere, e.g.,

.. code-block:: python

    config = ResConfig({"db.host": "localhost", "db.port": 5432})

This will be the same default configuration shown
earlier. ``ResConfig`` takes care of nesting the ``dict`` for you.


Use with Configuration Files
----------------------------

To read configuration from (multiple) files, supply a list of paths on
object initialization:

.. code-block:: python

    config = ResConfig({"db.host": "localhost", "db.port": 5432},
                       config_files=["myconf.yml",
                                     "~/.myconf.yml,
                                     "/etc/myconf.yml"])

If any of the files exists, they are read in the reverse order, i.e.,
*/etc/myconf.yml*, *~/.myconf.yml*, and then *myconf.yml*, and the
configuration read from them get merged in that order, overriding the
default. This allows layered configuration based on specificity by
filesystem location.


Use with Environment Variables
------------------------------

Properly named environment variables can override default
configuration. When you run your *myapp.py* app with the ``DB_HOST``
and/or ``DB_PORT`` environment variables set, their values override
the default:

.. code-block:: sh

    $ DB_HOST=remotehost DB_PORT=3306 python myapp.py

That is, ``config["db.host"]`` and ``config["db.port"]`` will return
``remotehost`` and ``3306``, respectively. As a rule of thumb, a
configuration key maps to an uppercased, “_”-delimited (when nested)
environment variable name.


Use with ArgumentParser
-----------------------

A ``ResConfig`` object can dynamically generate
``argparse.ArgumentParser`` arguments from default configuration:

.. code-block:: python

    parser = argparse.ArgumentParser()
    parser.add_argument(...)  # Define other arguments

    config.add_arguments_to_argparse(parser)
    # --pg-host and --pg-port arguments are now available

After actually parsing the (command-line) arguments, pass the parse
result to ``ResConfig`` and then load the configuration:

.. code-block:: python

    args = parser.parse_args()
    config.prepare_from_argparse(args)
    config.load()


Adding Actions on Changes
-------------------------

A ``ResConfig`` object is aware of changes to its
configuration. *Watch functions* watch changes happening at any nested
key to act on them:

.. code-block:: python

    from resconfig import Action

    @config.watch("db.host")
    def act_on_nested_key(action, old, new):
        if action == Action.ADDED:
            # db.host added
        elif action == Action.MODIFIED:
            # db.host modified
        elif action == Action.RELOADED:
            # db.host reloaded
        elif action == Action.REMOVED:
            # db.host removed

Here, the ``act_on_nested_key`` function is called whenever
configuration changes occur at ``db.host`` and can decide what to do
with the ``old`` and/or ``new`` values.


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
