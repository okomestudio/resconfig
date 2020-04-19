============================
 The “.”-Style Key Notation
============================

To access nested item, e.g.,

.. code-block:: python

   config = ResConfig({"hosts": {"localhost": {"user": "John"}}})

you may use the “.”-style notation, so that

.. code-block:: python

   print(config["hosts.localhost.user"])

will print ``John``.

Similarly, the same style can be used when supplying a
:class:`dict`-like object to :class:`.ResConfig`:

.. code-block:: python

   config = ResConfig({"hosts.localhost.user": "John"})

This will set exactly the same default configuration as the one above.

.. note::

   **Question**: *What if the key includes one of more “.” characters?
   It is quite common for us to see configuration with IP addresses
   like this:*

   .. code-block:: python

      config = ResConfig(
          {"hosts": {"127.0.0.1": {"user": "John"}}}
      )

   *Will this configuration be butchers into a mess like this?*

   .. code-block:: python

      {"hosts": {"127": {"0": {"0": {"1": {"user": "John"}}}}}}

   *Is this the end of the world?*

   **Answer**: Indeed, if you write the nested key like this,

   .. code-block:: python

      config = ResConfig({"hosts.127.0.0.1.user": "John"})

   the mess you mentioned will ensue. In order to avoid period to be
   interpreted as delimiter, you will need to escape them, e.g.,

   .. code-block:: python

      config = ResConfig({"hosts.127\.0\.0\.1.user": "John"})

   This way, they will not be interpret as nested keys:

   .. code-block:: python

      {"hosts": {"127\.0\.0\.1": {"user": "John"}}}

   Unfortunately, they need to be escaped all the time. For this
   reason, **it is strongly recommended to use “.” only as the
   delimiter for nested keys, not as part of a key.** While the end
   may not be near, this makes the world a bit messier place to be.
