==============
 Introduction
==============

:mod:`resconfig` is a minimalistic application configuration library
for Python. It is a thin wrapper around nested :class:`dict` objects
with added features that make it easy to deal with the data structure
as a centralized storage of application configuration.

:class:`.ResConfig` supports

- multiple configuration file formats: INI, JSON, TOML, and YAML;

- environment variables: Configuration can be easily overridden with
  environment variables;

- command-line arguments: Configuration can be easily overridden with
  ArgumentParser command-line arguments.

- “.”-delimited nested keys: ``config["foo.bar"]`` is equivalent to
  ``config["foo"]["bar"]``.


The advanced usage of :class:`.ResConfig` allows:

- Dynamic reloading of configuration at run time: Watch functions can
  be attached to any keys within the configuration to trigger actions
  to manage resources.
