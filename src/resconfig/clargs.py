from argparse import ArgumentParser
from argparse import Namespace

from .io.io import read_from_files_as_dict
from .ondict import ONDict
from .typing import Dict
from .typing import Set


class CLArgs:
    def add_arguments_to_argparse(
        self, parser: ArgumentParser, prefix: str = "", ignore: Set[str] = None
    ):
        """Add config arguments to ArgumentParser.

        The method add to the parser arguments that exist in the default config supplied
        on the instantiation of :class:`~resconfig.ResConfig` object. The long option
        will be “-”-delimited for nested keys, e.g., ``config["foo.bar"]`` will be
        mapped to ``--foo-bar``. If ``prefix`` is supplied, the prefix is prepended to
        the long option, e.g., ``--prefix-foo-bar``.

        To prevent the method from adding arguments to the parser for some keys, supply
        ``ignore`` with a set of keys to ignore, e.g., ``{"foo.bar"}``, so that
        ``--foo-bar`` will not be added.

        Args:
            parser: Parser object to which config arguments are added.
            prefix: Argument prefix.
            ignore: Config keys to ignore.
        """
        ignore = ignore or set()
        for key in self._default.allkeys():
            if ".".join(key) not in ignore:
                default = self._default[key]
                key = (prefix,) + key if prefix else key
                longopt = "--" + "-".join(k.replace(r"\.", ".") for k in key)
                parser.add_argument(longopt, default=default)

    def prepare_from_argparse(
        self,
        args: Namespace,
        config_file_arg: str = None,
        prefix: str = "",
        keymap: Dict[str, str] = None,
    ):
        """Prepare config from :class:`~argparse.ArgumentParser` result.

        See the docstring of :meth:`~resconfig.ResConfig.add_arguments_to_argparse` for
        the rule on how parser long options map to config keys. If long options do not
        directly map to config keys by that rule, you can supply ``prefix`` or
        ``keymap`` to define your own mapping. For example, if you want to map
        ``--long-opt`` (which would be parsed as the ``long_opt`` attribute) to the
        ``foo.bar`` config key, use ``{"long_opt": "foo.bar"}`` for ``keymap``.

        If you want to allow config file(s) to be specified through
        :class:`~argparse.ArgumentParser`, specify the attribute name for the argument
        to ``config_file_arg``.

        Args:
            args: Parse result returned from
                :meth:`~argparse.ArgumentParser.parse_args`.
            config_file_arg: The attribute name for config files.
            prefix: Argument prefix.
            keymap: Key mapping from the parsed argument name to the config key.
        """
        args = vars(args)
        keymap = keymap or {}
        conf = ONDict()
        if config_file_arg and config_file_arg in args:
            paths = args[config_file_arg]
            if paths:
                paths = paths if isinstance(paths, (list, tuple)) else [paths]
                conf.merge(read_from_files_as_dict(paths, self._merge_config_files))

        # TODO: Prune items not in default config above?

        for k, v in (item for item in args.items() if item[0] != config_file_arg):
            if k in keymap:
                k = keymap[k]
            else:
                k = ".".join(i.replace(".", r"\.") for i in k.split("_"))
                if prefix and k.startswith(prefix):
                    k = k[len(prefix) + 1 :]
            if k in self._default:
                conf.merge(ONDict({k: v}))

        self._clargs = conf
