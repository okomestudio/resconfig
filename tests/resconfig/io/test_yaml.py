import re
from datetime import datetime

from resconfig.io import yaml

from .bases import BaseTestIODump
from .bases import BaseTestIOLoad

content = """
---
section:
  bool: true
  datetime: 2020-01-02T20:00:00.000000
  float: 3.14
  int: 255
  str: foo bar
  nullable: null
  custom: 3
  array: [0, 1, 2]
  nested:
    str: mystr
    int: 10
"""


class TestLoad(BaseTestIOLoad):
    module = yaml
    content = content

    def test_section(self, loaded):
        assert "section" in loaded

    def test_bool(self, loaded):
        assert loaded["section"]["bool"] is True

    def test_custom(self, loaded):
        assert loaded["section"]["custom"] == 3

    def test_datetime(self, loaded):
        assert loaded["section"]["datetime"] == datetime(2020, 1, 2, 20)

    def test_float(self, loaded):
        assert loaded["section"]["float"] == 3.14

    def test_int(self, loaded):
        assert loaded["section"]["int"] == 255

    def test_nullable(self, loaded):
        assert loaded["section"]["nullable"] is None

    def test_str(self, loaded):
        assert loaded["section"]["str"] == "foo bar"

    def test_array(self, loaded):
        assert loaded["section"]["array"] == [0, 1, 2]

    def test_nested(self, loaded):
        assert loaded["section"]["nested"]["int"] == 10


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
