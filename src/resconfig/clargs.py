from argparse import ArgumentParser
from argparse import Namespace

from .dicttype import Dict


class CLArgs:
    def add_arguments_to_argparse(
        self, parser: ArgumentParser, prefix: str = "", ignore: set = None
    ):
        """Add the config arguments to the ArgumentParser.

        The long option will be ``-``-delimited for nested keys, e.g.,
        ``config["foo.bar"]`` will be mapped to ``--foo-bar``. If ``prefix`` is
        supplied, the supplied string is prepended to the long option, e.g.,
        ``--prefix-foo-bar``.

        Args:
            parser: The parser object to which config arguments are added.
            prefix: The argument prefix.
            ignore: The configuration keys to ignore.
        """
        ignore = ignore or set()
        for key in self._default.allkeys():
            if ".".join(key) not in ignore:
                default = self._default[key]
                key = (prefix,) + key if prefix else key
                longopt = "--" + "-".join(key)
                parser.add_argument(longopt, default=default)

    def prepare_from_argparse(
        self, args: Namespace, config_paths=None, prefix: str = "", keymap: dict = None
    ):
        """Prepare the config from :class:`~argparse.ArgumentParser` result.

        Args:
            args: The :class:`~argparse.Namespace` object returned from
                  :meth:`~argparse.ArgumentParser.parse_args`.
            config_paths: TBD.
            prefix: The argument prefix.
            keymap: The key mapping from the parsed argument name to the config key.
        """
        keymap = keymap or {}
        conf = Dict()
        if config_paths:
            conf.merge(self._read_from_files_as_dict(config_paths))

        for k, v in vars(args).items():
            if k in keymap:
                k = keymap[k]
            else:
                k = ".".join(k.split("_"))
                if prefix and k.startswith(prefix):
                    k = k[len(prefix) + 1 :]
            if k in self._default:
                conf.update({k: v})

        self._clargs = conf
