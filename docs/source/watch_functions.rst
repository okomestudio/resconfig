=================
 Watch Functions
=================

The watch function can be registered in a few different ways. There
are no differences among the styles in terms of functionality.

The decorator style:

.. code-block:: python

    @config.watch("nested.key")
    def watch_function(action, old, new):
        ...

The method style:

.. code-block:: python

    def watch_function(action, old, new):
        ...

    config.register("nested.key", watch_function)

The initial argument style:

.. code-block:: python

    def watch_function(action, old, new):
        ...

    config = ResConfig(watchers={"nested.key": watch_function})
