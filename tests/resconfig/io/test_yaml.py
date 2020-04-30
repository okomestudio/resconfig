from io import StringIO

import pytest

from resconfig.io import yaml

from .bases import BaseTestLoad

content = """
---
str: str
int: 10
bool: true
nullval: null
array: [0, 1, 2]
nested:
  str: mystr
  int: 10
"""


@pytest.fixture
def stream():
    yield StringIO(content)


@pytest.fixture
def loaded(stream):
    yield yaml.load(stream)


@pytest.fixture
def dumped(loaded, stream):
    yaml.dump(loaded, stream)
    stream.seek(0)
    yield stream.read()


class TestLoad(BaseTestLoad):
    module = yaml

    def test_integer(self, loaded):
        assert loaded["int"] == 10

    def test_string(self, loaded):
        assert loaded["str"] == "str"

    def test_bool(self, loaded):
        assert loaded["bool"] is True

    def test_null(self, loaded):
        assert loaded["nullval"] is None

    def test_array(self, loaded):
        assert loaded["array"] == [0, 1, 2]

    def test_nested(self, loaded):
        assert loaded["nested"]["int"] == 10


class TestDump:
    def test_string(self, dumped):
        assert "str: str" in dumped

    def test_integer(self, dumped):
        assert "int: 10" in dumped

    def test_bool(self, dumped):
        assert "bool: true" in dumped

    def test_null(self, dumped):
        assert "nullval: null" in dumped

    def test_array(self, dumped):
        assert "array:\n- 0\n- 1\n- 2\n" in dumped

    def test_nested(self, dumped):
        assert "nested:" in dumped
