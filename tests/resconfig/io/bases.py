from io import StringIO

import pytest

from resconfig import fields
from resconfig.fields import extract_values
from resconfig.ondict import ONDict


class BaseTestLoad:
    module = None

    def test_empty(self):
        stream = StringIO("")
        loaded = self.module.load(stream)
        assert loaded == {}, "Blank file should load as an empty dict"


class CustomField(fields.Field):
    @classmethod
    def from_obj(cls, value):
        return value

    @classmethod
    def to_str(cls, value):
        return "by custom"


class BaseTestIODump:
    module = None
    schema = ONDict(
        {
            "section": {
                "bool": fields.Bool(True),
                "datetime": fields.Datetime("2019-05-27T10:00:00.000000-07:00"),
                "float": fields.Float(3.14),
                "int": fields.Int(255),
                "str": fields.Str("foo bar"),
                "nullable": fields.NullableInt(),
                "custom": CustomField(0),
            }
        }
    )

    @pytest.fixture(scope="class")
    def dumped(self):
        conf = extract_values(self.schema)
        f = StringIO()
        self.module.dump(conf, f, schema=self.schema)
        f.seek(0)
        content = f.read()
        return content
