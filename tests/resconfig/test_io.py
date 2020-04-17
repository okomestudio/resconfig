import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import mock

import pytest
from resconfig import ResConfig
from resconfig.io.io import FileType
from resconfig.io.io import _suffix_to_filetype

from .test_resconfig import TestCase


class TestSuffixToFiletype:
    @pytest.mark.parametrize(
        "name, filetype",
        [
            ("a", FileType.ini),
            ("a.ini", FileType.ini),
            ("a.json", FileType.json),
            ("a.toml", FileType.toml),
            ("a.yaml", FileType.yaml),
            ("a.yml", FileType.yaml),
        ],
    )
    def test(self, name, filetype):
        assert _suffix_to_filetype(name) == filetype


class TestIO(TestCase):
    @contextmanager
    def tempfile(self, suffix=""):
        f = NamedTemporaryFile(delete=False, suffix=suffix)
        filename = f.name
        try:
            yield filename
        finally:
            os.remove(filename)

    def test_read_as_dict(self, filename):
        expected = {"a": {"b": "1"}}
        conf = ResConfig(expected)
        conf.save_to_file(filename)
        content = conf._read_as_dict(filename)
        assert isinstance(content, dict)
        assert content == expected

    def test_with_suffix(self, filename):
        conf = ResConfig()
        with mock.patch("resconfig.io.io._suffix_to_filetype") as func:
            conf.save_to_file(filename)
        func.assert_called_with(filename)
        with mock.patch("resconfig.io.io._suffix_to_filetype") as func:
            conf.load_from_file(filename)
        func.assert_called_with(filename)


class TestINI(TestIO):
    ini_default = {"sec1": {"opt1": "2"}}

    @pytest.fixture
    def filename(self):
        with self.tempfile(".ini") as filename:
            yield filename

    def test(self, filename):
        conf = ResConfig(self.ini_default)
        conf.save_to_ini(filename)
        with open(filename) as f:
            content = f.read()
        assert "[sec1]" in content

        conf = ResConfig()
        conf.load_from_ini(filename)
        assert "sec1.opt1" in conf
        assert conf.get("sec1.opt1") == self.ini_default["sec1"]["opt1"]

    def test_nested(self, filename):
        conf = ResConfig(
            {"sec1": {"opt1": "2", "opt2": {"nested": "foo"}}, "sec2": {"foo": "bar"}}
        )
        with pytest.raises(ValueError):
            conf.save_to_ini(filename)


class TestJSON(TestIO):
    @pytest.fixture
    def filename(self):
        with self.tempfile(".json") as filename:
            yield filename

    def test(self, filename):
        conf = ResConfig(self.default, schema={"x2": (Path, str)})
        conf.save_to_json(filename)
        with open(filename) as f:
            content = f.read()
        assert '{"x1": 1' in content

        conf = ResConfig()
        conf.load_from_json(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]


class TestTOML(TestIO):
    @pytest.fixture
    def filename(self):
        with self.tempfile(".toml") as filename:
            yield filename

    def test(self, filename):
        conf = ResConfig(self.default, schema={"x2": (Path, str)})
        # conf = ResConfig(self.default)
        conf.save_to_toml(filename)
        with open(filename) as f:
            content = f.read()
        assert "x1 = 1" in content
        assert "[x3.y3]\nz1 = 3" in content

        conf = ResConfig()
        conf.load_from_toml(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]


class TestYAML(TestIO):
    @pytest.fixture
    def filename(self):
        with self.tempfile(".yaml") as filename:
            yield filename

    def test(self, filename):
        conf = ResConfig(self.default, schema={"x2": (Path, str)})
        # conf = ResConfig(self.default)
        conf.save_to_yaml(filename)
        with open(filename) as f:
            content = f.read()
        assert "x1: 1" in content

        conf = ResConfig()
        conf.load_from_yaml(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]
