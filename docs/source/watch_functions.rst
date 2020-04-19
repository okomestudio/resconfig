=================
 Watch Functions
=================

The :class:`.ResConfig` object is aware of changes to its
configuration. *Watch functions* can be registered to watch changes
happening at any nested key to act on them.

The following example shows how a watch function, named
:meth:`manage_db_host`, can be triggered on changes happening for the
``db.host`` item in configuration:

.. code-block:: python

    import signal
    from resconfig import Action, ResConfig

    config = ResConfig(load_on_init=False)

    @config.watch("db.host")
    def manage_db_host(action, old, new):
        if action == Action.ADDED:
            # Initialize database connection?
        elif action == Action.MODIFIED:
            # Change database connection?
        elif action == Action.RELOADED:
            # Refresh database connection?
        elif action == Action.REMOVED:
            # Clean up on database connection?

    def reload(signum=None, stack_frame=None):
        config.reload()

    signal.signal(signal.SIGHUP, reload)  # run reload on SIGHUP

    config.load()

Here, the :func:`manage_db_host` function is called whenever a change
occurs at the ``db.host`` item in the configuration and can decide
what to do with the ``old`` and/or ``new`` values based on the actual
:class:`.Action`. In this example, the configuration reload function
is a handler for ``SIGHUP`` and is triggered when the process receives
the signal, for example, via ``kill -SIGHUP <pid>`` where ``<pid>`` is
the application process ID.

The watch function can be registered in a few different ways:
:meth:`.watch`, :meth:`.register`, and the ``watchers`` argument to
the :class:`.ResConfig` initializer. There are no differences among
the styles in terms of functionality. The decorator style:

.. code-block:: python

    @config.watch("db.host")
    def watch_function(action, old, new):
        ...

The method style:

.. code-block:: python

    def watch_function(action, old, new):
        ...

    config.register("db.host", watch_function)

The initial argument style:

.. code-block:: python

    def watch_function(action, old, new):
        ...

    config = ResConfig(watchers={"db.host": watch_function})
