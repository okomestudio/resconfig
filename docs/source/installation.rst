Installation
============

:mod:`resconfig` is available at PyPI. To install using :command:`pip`:

.. code-block:: sh

    $ pip install resconfig

If you wish to use TOML and/or YAML files for configuration, install
extra dependencies:

.. code-block:: sh

    $ pip install resconfig[toml]  # TOML support
    $ pip install resconfig[yaml]  # YAML support

To install from source, download the code from GitHub:

.. code-block:: sh

    $ git clone git@github.com:okomestudio/resconfig.git
    $ cd resconfig
    $ pip install .[toml,yaml]  # install both TOML and YAML support
    $ pip install -e .[dev]  # for development
