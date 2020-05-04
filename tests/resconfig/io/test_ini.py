import re
from datetime import datetime
from io import StringIO

import pytest

from resconfig.io import ini

from .bases import BaseTestIODump
from .bases import BaseTestIOLoad

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

[section]
bool = true
datetime = 2020-01-02T20:00:00.000000
float = 3.14
int = 255
str = foo bar
nullable = null
custom = 3
"""


class TestLoad(BaseTestIOLoad):
    module = ini

    @pytest.fixture
    def loaded(self):
        yield ini.load(StringIO(content), schema=self.schema)

    @pytest.mark.parametrize("key", ["section", r"bitbucket\.org", "extras section"])
    def test_section(self, loaded, key):
        assert key in loaded

    def test_bool(self, loaded):
        assert loaded["section.bool"] is True

    def test_custom(self, loaded):
        assert loaded["section.custom"] == "3"

    def test_datetime(self, loaded):
        assert loaded["section.datetime"] == datetime(2020, 1, 2, 20, 0, 0)

    def test_float(self, loaded):
        assert loaded["section.float"] == 3.14

    def test_int(self, loaded):
        assert loaded["section.int"] == 255

    def test_nullable(self, loaded):
        assert loaded["section.nullable"] is None

    def test_str(self, loaded):
        assert loaded["section.str"] == "foo bar"

    # def test_default_pass_through(self, loaded):
    #     assert loaded[r"bitbucket\.org"]["serveraliveinterval"] == "45"

    # def test_integer(self, loaded):
    #     assert loaded[r"bitbucket\.org"]["compressionlevel"] == "9"

    # def test_string(self, loaded):
    #     assert loaded[r"bitbucket\.org"]["user"] == "hg"
    #     assert loaded[r"extras section"][r"foo\.bar"] == "baz qux"

    # def test_bool(self, loaded):
    #     assert loaded[r"bitbucket\.org"]["compression"] == "yes"

    # def test_colon(self, loaded):
    #     assert loaded["extras section"]["key"] == "Value"


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
