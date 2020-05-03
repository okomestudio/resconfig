from io import StringIO

import pytest

from resconfig.fields import Bool
from resconfig.fields import Datetime
from resconfig.fields import Float
from resconfig.fields import Int
from resconfig.fields import Str
from resconfig.fields import extract_values
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
                "bool": Bool(True),
                "datetime": Datetime("2019-05-27T10:00:00.000000-07:00"),
                "float": Float(3.14),
                "int": Int(255),
                "str": Str("foo bar"),
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
