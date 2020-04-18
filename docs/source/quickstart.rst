============
 Quickstart
============

This quickstart provides a short introduction on how to get started
with :class:`.ResConfig`. Read :doc:`installation` first, if you have
not installed the :mod:`resconfig` package.

Let us first create an :class:`.ResConfig` object with a simple
default configuration for your application, *myapp.py*:

.. code-block:: python

    from resconfig ResConfig

    config = ResConfig({"db": {"host": "localhost", "port": 5432}})

By default, :class:`.ResConfig` loads configuration immediately after
its initialization. To control the timing of load, use the
``load_on_init`` flag:

.. code-block:: python

    config = ResConfig({"db": {"host": "localhost", "port": 5432}},
                       load_on_init=False)
    config.load()

The following sections introduce you to the basic usage of
:class:`.ResConfig` object.


The “.”-Style Key Notation
--------------------------

:class:`.ResConfig` exposes :class:`dict`-like interface for value
access but additionally allows the “.”-style notation for nested
keys. The following methods all return the same value, ``localhost``:

.. code-block:: python

    host = config["db"]["host"]
    host = config["db.host"]
    host = config.get("db.host")  # similar to dict.get

The “.”-style can be used elsewhere, e.g.,

.. code-block:: python

    config = ResConfig({"db.host": "localhost", "db.port": 5432})

This will be the same default configuration shown
earlier. :class:`.ResConfig` takes care of nesting the :class:`dict`
for you.


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
filesystem location.  Read :doc:`config_files` for more detail.


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
environment variable name. Read :doc:`envvars` for more detail.


Use with ArgumentParser
-----------------------

A :class:`.ResConfig` object can dynamically generate
:class:`~argparse.ArgumentParser` arguments from default
configuration:

.. code-block:: python

    parser = argparse.ArgumentParser()
    parser.add_argument(...)  # Define other arguments

    config.add_arguments_to_argparse(parser)
    # --pg-host and --pg-port arguments are now available

After actually parsing the (command-line) arguments, pass the parse
result to :class:`.ResConfig` and then load the configuration:

.. code-block:: python

    args = parser.parse_args()
    config.prepare_from_argparse(args)
    config.load()

For more detail, read :doc:`argparse`.


Adding Actions on Changes
-------------------------

A :class:`.ResConfig` object is aware of changes to its
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

Here, the :func:`act_on_nested_key` function is called whenever
configuration changes occur at ``db.host`` and can decide what to do
with the ``old`` and/or ``new`` values. For more detail, read
:doc:`watch_functions`.
