import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest

from resconfig import ResConfig
from resconfig.io.paths import ConfigPath
from resconfig.io.paths import INIPath
from resconfig.io.paths import JSONPath
from resconfig.io.paths import TOMLPath
from resconfig.io.paths import YAMLPath


class TestReadAsDict:
    def test(self, filename):
        expected = {"a": {"b": "1"}}
        conf = ResConfig(expected)
        conf.save_to_file(filename)
        content = ConfigPath.from_extension(filename).load()
        assert isinstance(content, dict)
        assert content == expected


class Base:
    filetype = None
    filename_suffix = None
    config_path_type = ConfigPath

    @contextmanager
    def tempfile(self, suffix=""):
        f = NamedTemporaryFile(delete=False, suffix=suffix)
        filename = f.name
        try:
            yield filename
        finally:
            os.remove(filename)

    @pytest.fixture
    def filename(self):
        with self.tempfile(self.filename_suffix) as filename:
            yield filename

    def test_IO__update_from_file(self, filename):
        conf = ResConfig()
        path = self.config_path_type(filename)
        with patch.object(conf, "update") as update:
            conf._IO__update_from_file(path)
            assert isinstance(update.call_args[0][0], dict)

    def test_update_from_filetype(self, filename):
        conf = ResConfig()
        meth = getattr(conf, "update_from_" + self.filetype)
        with patch("resconfig.ResConfig._IO__update_from_file") as update:
            meth(filename)
            assert type(update.call_args[0][0]) is self.config_path_type

    def test_update_from_file_with_suffix(self, filename):
        conf = ResConfig()
        with patch("resconfig.ResConfig._IO__update_from_file") as update:
            conf.update_from_file(filename)
            update.assert_called_with(self.config_path_type(filename))
            assert type(update.call_args[0][0]) is self.config_path_type

    def test_IO__save(self, filename):
        conf = ResConfig()
        path = self.config_path_type(filename)
        with patch.object(path, "dump") as dump:
            conf._IO__save(path)
            dump.assert_called_with(conf._conf, schema=conf._default)

    def test_save_to_filetype(self, filename):
        conf = ResConfig()
        meth = getattr(conf, "save_to_" + self.filetype)
        with patch("resconfig.ResConfig._IO__save") as save:
            meth(filename)
            assert type(save.call_args[0][0]) is self.config_path_type

    def test_save_to_file_with_suffix(self, filename):
        conf = ResConfig()
        with patch("resconfig.ResConfig._IO__save") as save:
            conf.save_to_file(filename)
            save.assert_called_with(self.config_path_type(filename))
            assert type(save.call_args[0][0]) is self.config_path_type


class TestINI(Base):
    filetype = "ini"
    filename_suffix = ".ini"
    config_path_type = INIPath

    def test_nested(self, filename):
        conf = ResConfig(
            {"sec1": {"opt1": "2", "opt2": {"nested": "foo"}}, "sec2": {"foo": "bar"}}
        )
        with pytest.raises(ValueError):
            conf.save_to_ini(filename)


class TestJSON(Base):
    filetype = "json"
    filename_suffix = ".json"
    config_path_type = JSONPath


class TestTOML(Base):
    filetype = "toml"
    filename_suffix = ".toml"
    config_path_type = TOMLPath


class TestYAML(Base):
    filetype = "yaml"
    filename_suffix = ".yaml"
    config_path_type = YAMLPath
