from io import StringIO

import pytest

from resconfig.fields import bool_
from resconfig.fields import datetime_
from resconfig.fields import extract_values
from resconfig.fields import float_
from resconfig.fields import int_
from resconfig.fields import str_
from resconfig.ondict import ONDict


class BaseTestLoad:
    module = None

    def test_empty(self):
        stream = StringIO("")
        loaded = self.module.load(stream)
        assert loaded == {}, "Blank file should load as an empty dict"


class BaseTestIODump:
    module = None
    schema = ONDict(
        {
            "section": {
                "bool": bool_(True),
                "datetime": datetime_("2019-05-27T10:00:00.000000-07:00"),
                "float": float_(3.14),
                "int": int_(255),
                "str": str_("foo bar"),
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
