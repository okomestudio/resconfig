==========================
 Configuration from Files
==========================

:class:`.ResConfig` understands INI (`.ini`), JSON (`.json`), TOML
(`.toml`), and YAML (`.yaml` or `.yml`). If not given, the file format
is inferred from these filename extensions. The filename with no
extension is assumed to be of INI.


Merge Behavior
--------------

When multiple files are supplied, :class:`.ResConfig` handles them in
two different ways, depending on the ``merge_config_files``
switch. When :obj:`True`, all existing files are read, but merging
will be in the reverse of the input file list. For example, in the
following case,

.. code-block:: python

    config = ResConfig(config_files=["myconf.yml",
                                     "~/.myconf.yml,
                                     "/etc/myconf.yml"],
                       merge_config_files=True)

the configurations read from these files are merged in the following
order: */etc/myconf.yml*, *~/.myconf.yml*, and *myconf.yml*. This
effectively allows overriding configuration based on environment,
i.e., personal configuration has a higher precedence to the system
configuration in this example, typical of UNIX-like systems.

When :obj:`False`, only the first existing file will be read. For
example, suppose that *~/.myconf.yml* and */etc/myconf.yml* exist but
not *myconf.yml*. Then

.. code-block:: python

    config = ResConfig(config_files=["myconf.yml",
                                     "~/.myconf.yml,
                                     "/etc/myconf.yml"],
                       merge_config_files=False)

will read only from *~/.myconf.yml*. :class:`.ResCongif` skips
*myconf.yml* and ignores */etc/myconf.yml*.

The default behavior is ``merge_config_files=True``.

In general, non-existing files are simply skipped without throwing
errors.

The “``~``” character in file paths will be expanded to the path
defined in the ``HOME`` environment variable.


File Types
----------

:class:`.ResConfig` understands the following file formats:

- INI (`.ini`)
- JSON (`.json`)
- TOML (`.toml`)
- YAML (`.yaml` or `.yml`)

with the given filename extensions.

By default, a filename without extension is assumed to be of INI
type. If you wish to explicitly specify file type, you may do so using
a :class:`.ConfigPath` subclass as follows:

.. code-block:: python

   from resconfig.io.paths import YAMLPath

   config = ResConfig(config_files=[YAMLPath("myconf"),
                                    YAMLPath("~/.myconf),
                                    YAMLPath("/etc/myconf")])

This way, all the files are considered to be of YAML type, regardless
of extension. :class:`.ResConfig` supplies :class:`.INIPath`,
:class:`.JSONPath`, :class:`TOMLPath`, and :class:`YAMLPath` for this
purpose.
