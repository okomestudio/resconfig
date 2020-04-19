=======================
 Environment Variables
=======================

Often, being able to override configuration with environment variables
is desirable. :class:`.ResConfig` by default looks for environment
variables that map to configuration keys in a simple way, converting
“.”-delimited configuration keys to “_”-delimited, uppercase
environment variable names.

For example, the configuration key ``db.host`` will be mapped to
``DB_HOST``.

To avoid conflicts with variable names used for other purposes,
pprefix can be used. If you want ``MYAPP_`` to be your prefix, supply
it as the ``envvar_prefix`` option to :class:`.ResConfig`:

.. code-block:: python

    config = ResConfig({"db.host": "localhost", "db.port": 5432},
                       envvar_prefix="MYAPP_")

Then, the ``MYAPP_DB_HOST`` and ``MYAPP_DB_PORT`` will map to ``db.host``
and ``db.port`` configuration keys.

.. note::

   The escaped “.” in keys will map to a “_” character for environment
   variable names.
