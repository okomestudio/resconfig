import io
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from resconfig.io.toml import dump
from resconfig.io.toml import load

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
"""


@pytest.fixture
def stream():
    yield io.StringIO(content)


@pytest.fixture
def loaded(stream):
    yield load(stream)


@pytest.fixture
def dumped(loaded):
    stream = io.StringIO()
    dump(loaded, stream)
    stream.seek(0)
    yield stream.read()


class TestLoad:
    def test_no_section(self, loaded):
        assert loaded["title"] == "TOML Example"

    def test_section(self, loaded):
        assert "owner" in loaded

    def test_string(self, loaded):
        assert loaded["owner"]["name"] == "Tom Preston-Werner"

    def test_datetime(self, loaded):
        assert loaded["owner"]["dob"] == datetime(
            1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=-8))
        )

    def test_integer(self, loaded):
        assert loaded["database"]["connection_max"] == 5000

    def test_boolean(self, loaded):
        assert loaded["database"]["enabled"] is True

    def test_array(self, loaded):
        assert loaded["database"]["ports"] == [8001, 8001, 8002]

    def test_nested_arrays(self, loaded):
        assert loaded["clients"]["data"][0] == ["gamma", "delta"]

    def test_servers_nested_section(self, loaded):
        assert loaded["servers"]["alpha"]["ip"] == "10.0.0.1"

    def test_extras_nested_keys(self, loaded):
        assert loaded["extras"]["nested"]["key"]["example"] == "foobar"


class TestDump:
    def test_no_section(self, dumped):
        assert "title" in dumped

    def test_section(self, dumped):
        assert "[owner]" in dumped

    def test_string(self, dumped):
        assert 'name = "Tom Preston-Werner"' in dumped

    def test_datetime(self, dumped):
        assert "dob = 1979-05-27T07:32:00-08:00" in dumped

    def test_integer(self, dumped):
        assert "connection_max = 5000" in dumped

    def test_boolean(self, dumped):
        assert "enabled = true" in dumped

    def test_array(self, dumped):
        assert "ports = [ 8001, 8001, 8002,]" in dumped

    def test_nested_arrays(self, dumped):
        assert '[ [ "gamma", "delta",],' in dumped

    def test_servers_nested_section(self, dumped):
        assert "[servers.alpha]" in dumped
        assert 'ip = "10.0.0.1"' in dumped

    def test_extras_nested_keys(self, dumped):
        assert "[extras.nested.key]" in dumped
        assert 'example = "foobar"' in dumped
