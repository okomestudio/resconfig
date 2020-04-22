Unreleased
----------

Added:

- Documentation for using :class:`.ConfigPath` objects to specify file
  types (`#20`_)


.. _#20: https://github.com/okomestudio/resconfig/issues/20


Fixed:

- Reading from an empty JSON/YAML file results in load error
  (`2fc94fa`_, `1346f3f`_).


.. _2fc94fa: https://github.com/okomestudio/resconfig/commit/2fc94fa6adb9a73e5078d1bedeb9f905f4953aa5
.. _1346f3f: https://github.com/okomestudio/resconfig/commit/1346f3fe27795903a1843720934a85eccb297c5c


20.4.3a (April 19, 2020)
------------------------

Added:

- Allow file formats to be hinted by wrapping as ConfigPath objects
  (`#20`_).

- The config precedence page in documentation (`#13`_).

- Logging on `#17`_:

  - config value setting by environment variable and command-line
    argument.
  - watch function de/registration.


.. _#20: https://github.com/okomestudio/resconfig/issues/20
.. _#13: https://github.com/okomestudio/resconfig/issues/13
.. _#17: https://github.com/okomestudio/resconfig/issues/17


Changed:

- Move changelog to the repo root and include it into docs.


Fixed:

- None values from CL arg default passed through (`447adc1`_).

- Environment variable overridden by command-line argument if the
  latter does not default to None (`#21`_).


.. _447adc1: https://github.com/okomestudio/resconfig/commit/447adc10dd237b911c1a7a05f6fc513477063a23
.. _#21: https://github.com/okomestudio/resconfig/issues/21


20.4.2a (April 18, 2020)
------------------------

Initial alpha version.
