import re
from io import StringIO

import pytest

from resconfig.io import yaml

from .bases import BaseTestIODump
from .bases import BaseTestIOLoad

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


class TestLoad(BaseTestIOLoad):
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


class TestDump(BaseTestIODump):
    module = yaml

    def test_section(self, dumped):
        assert "section:\n" in dumped

    def test_bool(self, dumped):
        assert "bool: true\n" in dumped

    def test_custom(self, dumped):
        assert "custom: by custom" in dumped

    def test_datetime(self, dumped):
        assert re.search(
            r"\s+datetime: '2019-05-27T10:00:00(\.0*)?-07:00'(\n|$)", dumped
        )

    def test_float(self, dumped):
        assert "float: 3.14\n" in dumped

    def test_int(self, dumped):
        assert "int: 255\n" in dumped

    def test_nullable(self, dumped):
        assert "nullable: null\n" in dumped

    def test_str(self, dumped):
        assert "str: foo bar\n" in dumped
