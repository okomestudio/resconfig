import re
from datetime import datetime
from io import StringIO

import pytest
from dateutil.parser import parse

from resconfig import fields
from resconfig.io import ini
from resconfig.ondict import ONDict

from .bases import BaseTestIODump
from .bases import BaseTestLoad

content = """
[DEFAULT]
ServerAliveInterval = 45
Compression = yes
CompressionLevel = 9
ForwardX11 = yes

[bitbucket.org]
User = hg

[topsecret.server.com]
Port = 50022
ForwardX11 = no

[extras section]
Key : Value
foo.bar = baz qux
dt = 2020-01-02T20:00:00.000000
"""


@pytest.fixture
def spec():
    spec = {"extras section": {"dt": fields.Datetime(datetime.now())}}
    yield ONDict(spec)


@pytest.fixture
def stream():
    yield StringIO(content)


@pytest.fixture
def loaded(stream):
    yield ini.load(stream)


@pytest.fixture
def cast(loaded):
    loaded["extras section"]["dt"] = parse(loaded["extras section"]["dt"])
    yield loaded


class TestLoad(BaseTestLoad):
    module = ini

    def test_default_pass_through(self, loaded):
        assert loaded[r"bitbucket\.org"]["serveraliveinterval"] == "45"

    def test_section(self, loaded):
        assert r"bitbucket\.org" in loaded

    def test_section_with_spaces(self, loaded):
        assert "extras section" in loaded

    def test_integer(self, loaded):
        assert loaded[r"bitbucket\.org"]["compressionlevel"] == "9"

    def test_string(self, loaded):
        assert loaded[r"bitbucket\.org"]["user"] == "hg"
        assert loaded[r"extras section"][r"foo\.bar"] == "baz qux"

    def test_bool(self, loaded):
        assert loaded[r"bitbucket\.org"]["compression"] == "yes"

    def test_colon(self, loaded):
        assert loaded["extras section"]["key"] == "Value"


class TestDump(BaseTestIODump):
    module = ini

    def test_section(self, dumped):
        assert "[section]\n" in dumped

    def test_bool(self, dumped):
        assert "bool = true\n" in dumped

    def test_custom(self, dumped):
        assert "custom = by custom\n" in dumped

    def test_datetime(self, dumped):
        assert re.search(
            r"($|\n)datetime = 2019-05-27T10:00:00(\.0*)?-07:00(\n|$)", dumped
        )

    def test_float(self, dumped):
        assert "float = 3.14\n" in dumped

    def test_integer(self, dumped):
        assert "int = 255\n" in dumped

    def test_nullable(self, dumped):
        assert "nullable = null\n" in dumped

    def test_string(self, dumped):
        assert "str = foo bar\n" in dumped
