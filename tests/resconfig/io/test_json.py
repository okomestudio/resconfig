import re

import pytest

from resconfig.io import json

from .bases import BaseTestIODump
from .bases import BaseTestIOLoad

content = """
{
  "section": {
    "bool": true,
    "datetime": "2020-01-02T20:00:00.000000",
    "float": 3.14,
    "int": 255,
    "str": "foo bar",
    "nullable": null,
    "custom": 3,
    "array": [0, 1, 2],
    "nested": {
      "str": "mystr",
      "int": 10
    },
    "inter.net": {"user": "foo bar"}
  }
}
"""


class TestLoad(BaseTestIOLoad):
    module = json
    content = content

    @pytest.mark.parametrize("key", ["section", r"section.inter\.net.user"])
    def test_section(self, loaded, key):
        assert key in loaded

    def test_bool(self, loaded):
        assert loaded["section"]["bool"] is True

    def test_custom(self, loaded):
        assert loaded["section"]["custom"] == 3

    def test_float(self, loaded):
        assert loaded["section"]["float"] == 3.14

    def test_int(self, loaded):
        assert loaded["section"]["int"] == 255

    def test_null(self, loaded):
        assert loaded["section"]["nullable"] is None

    def test_str(self, loaded):
        assert loaded["section"]["str"] == "foo bar"

    def test_array(self, loaded):
        assert loaded["section"]["array"] == [0, 1, 2]

    def test_nested(self, loaded):
        assert loaded["section"]["nested"]["int"] == 10


class TestDump(BaseTestIODump):
    module = json

    def test_section(self, dumped):
        assert '"section":' in dumped

    def test_bool(self, dumped):
        assert '"bool": true' in dumped

    def test_custom(self, dumped):
        assert '"custom": "by custom"' in dumped

    def test_datetime(self, dumped):
        assert re.search(r'"datetime": "2019-05-27T10:00:00(\.0*)?-07:00"', dumped)

    def test_float(self, dumped):
        assert '"float": 3.14' in dumped

    def test_int(self, dumped):
        assert '"int": 255' in dumped

    def test_nullable(self, dumped):
        assert '"nullable": null' in dumped

    def test_str(self, dumped):
        assert '"str": "foo bar"' in dumped
