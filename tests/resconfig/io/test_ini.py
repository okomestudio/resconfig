from io import StringIO

import pytest

from resconfig.io import ini

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
foo.bar = baz
"""


@pytest.fixture
def stream():
    yield StringIO(content)


@pytest.fixture
def loaded(stream):
    yield ini.load(stream)


@pytest.fixture
def dumped(loaded, stream):
    ini.dump(loaded, stream)
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

    def test_boolean(self, dumped):
        assert "compression = yes" in dumped
