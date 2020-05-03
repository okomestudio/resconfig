from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Optional

try:
    from toml import dumps as _dump
    from toml import loads as _load
except ImportError:
    _dump = _load = None


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    schema = schema or {}
    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        con[key] = _dumpobj(content[key], schema.get(key))
    f.write(_dump(con.asdict()))


def _dumpobj(value, field) -> Any:
    if isinstance(field, fields.Field):
        if not isinstance(
            field, (fields.Bool, fields.Datetime, fields.Float, fields.Int, fields.Str)
        ):
            value = field.to_str(value)
    return value


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    return ONDict(_load(f.read()))
