===================
 Config Precedence
===================

With several ways to set configuration, the precedence matters when
multiple methods are used simultaneously. :class:`.ResConfig` resolves
conflicts based on the following order, with the earlier methods in
the list take precedence when defined:

1. Command-line arguments.

2. Configuration files specified as command-line arguments.

3. Environment variables.

4. Configuration files supplied to :class:`.ResConfig` initializer.

5. Default configuration supplied to :class:`.ResConfig` initializer.

As an example, consider the following code, which we call *myapp.py*:

.. code-block:: python

   config = ResConfig({"db.host": "localhost", "db.port": 5432},
                      config_files=["~/.myapp.conf",
                                    "/etc/myapp.conf"],
                      load_on_init=False)

   parser = argparse.ArgumentParser()
   parser.add_argument("--conf")
   config.add_arguments_to_argparse(parser)

   args = parser.parse_args()
   config.prepare_from_argparse(args, config_file_arg="conf")
   config.load()

and the following files:

*myapp.conf*:

.. code-block:: ini

   [db]
   host = local.org

*~/.myapp.conf*:

.. code-block:: ini

   [db]
   host = home.org

(Let us assume that */etc/myapp.conf* does not exist.)

What would ``conf["db.host"]`` return? The answer depends on how
*myapp.py* is started.

(a)
   .. code-block:: sh

      $ DB_HOST=env.org python myapp.py --conf=myapp.conf \
                                     --db-host=cmdline.org
(b)
   .. code-block:: sh

      $ DB_HOST=env.org python myapp.py --conf=myapp.conf \

(c)
   .. code-block:: sh

      $ DB_HOST=env.org python myapp.py

(d)
   .. code-block:: sh

      $ python myapp.py

(e)
   .. code-block:: sh

      $ python myapp.py  # with ~/.myapp.conf not found

Answers: (a) ``cmdline.org``, (b) ``local.org``, (c) ``env.org``, (d)
``home.org``, (e) ``localhost``.
