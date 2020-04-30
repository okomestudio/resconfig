from datetime import datetime
from io import StringIO

import pytest
from dateutil.parser import parse

from resconfig.ddefs import datetime_
from resconfig.io import ini
from resconfig.ondict import ONDict

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
    spec = {"extras section": {"dt": datetime_(datetime.now())}}
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


@pytest.fixture
def dumped(cast, stream, spec):
    ini.dump(cast, stream, spec)
    stream.seek(0)
    yield stream.read()


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


class TestDump:
    def test_section(self, dumped):
        assert "[extras section]" in dumped
        assert "[bitbucket.org]" in dumped

    def test_string(self, dumped):
        assert "user = hg" in dumped

    def test_integer(self, dumped):
        assert "compressionlevel = 9" in dumped

    def test_datetime(self, dumped):
        assert "dt = 2020-01-02T20:00:00.000000" in dumped

    def test_boolean(self, dumped):
        assert "compression = yes" in dumped
