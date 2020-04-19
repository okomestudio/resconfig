============================
 ArgumentParser Integration
============================

:mod:`argparse` is a standard library tool to add command-line
argument parsing to your application. :class:`.ResConfig` makes it
easy to add command-line arguments to set configuration values.

In order to respect command-line arguments, the configuration needs to
be loaded after the :class:`~argparse.ArgumentParser` object completes
its parsing. By default, :class:`.ResConfig` loads the configuration
immediately after the initialization of itself. You can delay this by
setting the ``load_on_init`` flag to :obj:`False` and load it yourself
at an appropriate timing.


Dynamic Argument Generation
---------------------------

:class:`.ResConfig` object can generate and add command-line arguments
to :class:`~argparse.ArgumentParser` object from the default
configuration by the :meth:`.add_arguments_to_argparse` method.

Once :class:`~argparse.ArgumentParser` object does its parsing, the
result should be passed to the :meth:`.prepare_from_argparse` method
to prepare the configuration from the parse result. At that point, the
configuration is good to be loaded.

In summary, the following is the standard procedure:

.. code-block:: python

   config = ResConfig({"db.host": "localhost", "db.port": 5432},
                      load_on_init=False)

   parser = argparse.ArgumentParser()
   parser.add_argument(...)  # Define other arguments
   config.add_arguments_to_argparse(parser)

   args = parser.parse_args()
   config.prepare_from_argparse(args)
   config.load()

In this case, :meth:`.add_arguments_to_argparse` adds ``--db-host``
and ``--db-port`` as command-line arguments.

As a rule of thumb, a nested key maps to a “-”-delimited long
argument. To avoid conflict with other options, the ``prefix`` option
can supply a custom prefix:

.. code-block:: python

   config.add_arguments_to_argparse(parser, prefix="myapp")

With this, :meth:`.add_arguments_to_argparse` adds ``--myapp-db-host``
and ``--myapp-db-port`` as command-line arguments.

If you want certain items from the default to be skipped, provide
their keys as a :class:`set` in ``ignore``:

.. code-block:: python

   config.add_arguments_to_argparse(parser, ignore={"db.port"})

This way, ``--db-host`` will be added to the parser but not
``--db-port``.


Reading from Argument
---------------------

You may also manually define arguments and let
:meth:`.prepare_from_argparse` automatically pick them up by naming
pattern, e.g.,

.. code-block:: python

   config = ResConfig({"db.host": "localhost", "db.port": 5432},
                      load_on_init=False)

   parser = argparse.ArgumentParser()
   parser.add_argument(...)  # Define other arguments
   parser.add_argument("--db-host", default="localhost")
   parser.add_argument("--db-port", default=5432)

   args = parser.parse_args()
   config.prepare_from_argparse(args)
   config.load()

Here, ``--db-host`` and ``--db-port`` are mapped to the ``db.host``
and ``db.port`` keys in configuration.

If you used a common prefix, use the ``prefix`` option to supply it:

.. code-block:: python

   parser.add_argument("--myapp-db-host", default="localhost")
   parser.add_argument("--myapp-db-port", default=5432)
   ...
   config.prepare_from_argparse(args, prefix="myapp")

Or if you want a more generic mapping that does not match expected
pattern, use the ``keymap`` option to supply the mapping:

.. code-block:: python

   parser.add_argument("--hostname", default="localhost")
   parser.add_argument("--portnumber", default=5432)
   ...
   config.prepare_from_argparse(args,
                                keymap={"hostname": "db.host",
                                        "portnumber": "db.port"})

Often you want to supply configuration files as command line
argument. Indicate the argument for configuration file as the
``config_file_arg`` option:

.. code-block:: python

   parser.add_argument("--db-host", default="localhost")
   parser.add_argument("--db-port", default=5432)
   parser.add_argument("--conf", action="append")
   ...
   config.prepare_from_argparse(args, config_file_arg="conf")

The multiple files are handled just as ``config_files`` in
:class:`.ResConfig`, but with a higher precedence over those given at
the initialization; see :doc:`config_files` for detail of multi-file
configuration.


.. note::

   The escaped “.” in keys will map to a “.” character for
   command-line argument by the :meth:`.add_arguments_to_argparse`
   method. For example, if the config key is ``127\.0\.0\.1``, then
   the corresponding long option will be ``--127.0.0.1`` (and vice
   versa in :meth:`.prepare_from_argparse`).
