from argparse import ArgumentParser

import pytest

from resconfig import ResConfig


@pytest.fixture
def default():
    default = {"foo": {"bar": {"baz": None}}}
    yield default


class TestCLArgs:
    @pytest.fixture(autouse=True)
    def setup(self, default):
        self.default = default
        yield

    def _parse(self, clargs=None, *args, **kwargs):
        clargs = clargs or []
        conf = ResConfig(self.default)
        p = ArgumentParser()
        conf.add_arguments_to_argparse(p, *args, **kwargs)
        return p.parse_args(clargs)

    @pytest.mark.parametrize("default_value", [1, "str"])
    def test_add_arguments_to_argparse_to_default(self, default_value):
        self.default["foo"]["bar"]["baz"] = default_value
        args = self._parse()
        assert args.foo_bar_baz == default_value

    @pytest.mark.parametrize("default_value", [1, "str"])
    def test_add_arguments_to_argparse_to_arg(self, default_value):
        self.default["foo"]["bar"]["baz"] = default_value
        expected = "THIS"
        args = self._parse(["--foo-bar-baz", expected])
        assert args.foo_bar_baz == expected

    @pytest.mark.parametrize("clargs", [[], ["--prefix-foo-bar-baz", "bar"]])
    def test_add_arguments_to_argparse_with_prefix(self, clargs):
        expected = clargs[1] if clargs else "foo"
        self.default["foo"]["bar"]["baz"] = expected
        args = self._parse(clargs, prefix="prefix")
        assert args.prefix_foo_bar_baz == expected

    def test_add_arguments_to_argparse_with_ignore(self):
        ignore = {"foo.bar.baz"}
        expected = "foo"
        self.default["foo"]["bar"]["baz"] = expected
        args = self._parse([], ignore=ignore)
        with pytest.raises(AttributeError) as exc:
            args.foo_bar_baz
        assert "foo_bar_baz" in str(exc.value)

    @pytest.mark.parametrize(
        "longarg, kwargs",
        [
            ("--foo-bar-baz", {}),
            ("--prefix-foo-bar-baz", {"prefix": "prefix"}),
            ("--foobar", {"keymap": {"foobar": "foo.bar.baz"}}),
        ],
    )
    def test_prepare_from_argparse(self, longarg, kwargs):
        expected = 523
        conf = ResConfig(self.default)
        p = ArgumentParser()
        p.add_argument(longarg, default=expected)
        args = p.parse_args([])
        conf.prepare_from_argparse(args, **kwargs)
        assert conf._clargs["foo.bar.baz"] == expected

    def _test_prepare_from_argparse_with_conf_file_arg(
        self, savedconfigfile, kwargs, args
    ):
        filename, _ = savedconfigfile
        args = [filename if a == "FILENAME" else a for a in args]
        conf = ResConfig(self.default)
        p = ArgumentParser()
        p.add_argument("--conf", **kwargs)
        args = p.parse_args(args)
        conf.prepare_from_argparse(args, config_file_arg="conf")
        return conf

    @pytest.fixture
    def savedconfigfile(self, filename):
        expected = "5234"
        conf = ResConfig({"foo.bar": expected})
        conf.save_to_file(filename)
        yield filename, expected

    @pytest.mark.parametrize(
        "kwargs, args",
        [
            ({}, ["--conf", "FILENAME"]),
            ({"action": "append"}, ["--conf", "nonexisting", "--conf", "FILENAME"]),
        ],
    )
    def test_prepare_from_argparse_with_conf_file_arg(
        self, savedconfigfile, kwargs, args
    ):
        _, expected = savedconfigfile
        conf = self._test_prepare_from_argparse_with_conf_file_arg(
            savedconfigfile, kwargs, args
        )
        assert conf._clargs["foo.bar"] == expected

    @pytest.mark.parametrize(
        "kwargs, args",
        [
            ({}, []),
            ({}, ["--conf", "nonexisting"]),
            ({"action": "append"}, ["--conf", "nonexisting", "--conf", "nonexisting"]),
        ],
    )
    def test_prepare_from_argparse_with_conf_file_arg_error(
        self, savedconfigfile, kwargs, args
    ):
        _, expected = savedconfigfile
        conf = self._test_prepare_from_argparse_with_conf_file_arg(
            savedconfigfile, kwargs, args
        )
        with pytest.raises(KeyError):
            conf._clargs["foo.bar"]
