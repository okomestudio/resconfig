import re
from datetime import datetime
from io import StringIO

import pytest

from resconfig.io import toml

from .bases import BaseTestIODump
from .bases import BaseTestIOLoad

content = """
title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
dob = 1979-05-27T07:32:00-08:00 # First class dates

[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002 ]
connection_max = 5000
enabled = true

[servers]

  [servers.alpha]
  ip = "10.0.0.1"
  dc = "eqdc10"

  [servers.beta]
  ip = "10.0.0.2"
  dc = "eqdc10"

[clients]
data = [ ["gamma", "delta"], [1, 2] ]

hosts = [
  "alpha",
  "omega"
]

[extras]
nested.key.example = "foobar"

[section]
bool = true
datetime = 2020-01-02T20:00:00.000000
float = 3.14
int = 255
str = "foo bar"
nullable = "null"
custom = 3
"""


class TestLoad(BaseTestIOLoad):
    module = toml

    @pytest.fixture
    def loaded(self):
        yield toml.load(StringIO(content), schema=self.schema)

    def test_no_section(self, loaded):
        assert loaded["title"] == "TOML Example"

    def test_section(self, loaded):
        assert "section" in loaded

    def test_bool(self, loaded):
        assert loaded["section"]["bool"] is True

    def test_datetime(self, loaded):
        assert loaded["section"]["datetime"] == datetime(2020, 1, 2, 20)

    def test_custom(self, loaded):
        assert loaded["section"]["custom"] == 3

    def test_int(self, loaded):
        assert loaded["section"]["int"] == 255

    def test_nullable(self, loaded):
        assert loaded["section"]["nullable"] is None

    def test_str(self, loaded):
        assert loaded["section"]["str"] == "foo bar"

    def test_array(self, loaded):
        assert loaded["database"]["ports"] == [8001, 8001, 8002]

    def test_nested_arrays(self, loaded):
        assert loaded["clients"]["data"][0] == ["gamma", "delta"]

    def test_servers_nested_section(self, loaded):
        assert loaded["servers"]["alpha"]["ip"] == "10.0.0.1"

    def test_extras_nested_keys(self, loaded):
        assert loaded["extras"]["nested"]["key"]["example"] == "foobar"


class TestDump(BaseTestIODump):
    module = toml

    def test_section(self, dumped):
        assert "[section]\n" in dumped

    def test_bool(self, dumped):
        assert "bool = true\n" in dumped

    def test_custom(self, dumped):
        assert 'custom = "by custom"' in dumped

    def test_datetime(self, dumped):
        assert re.search(
            r"($|\n)datetime = 2019-05-27T10:00:00(\.0*)?-07:00(\n|$)", dumped
        )

    def test_float(self, dumped):
        assert "float = 3.14\n" in dumped

    def test_int(self, dumped):
        assert "int = 255\n" in dumped

    def test_nullable(self, dumped):
        assert "nullable" not in dumped

    def test_str(self, dumped):
        assert 'str = "foo bar"\n' in dumped
