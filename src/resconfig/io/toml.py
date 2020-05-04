from collections.abc import MutableMapping

from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Optional
from ..typing import Union
from .utils import escape_dot

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
    content = _load(f.read())

    def _walk(d, schema):
        if not isinstance(d, MutableMapping):
            return _loadobj(schema, d)
        for key in list(d.keys()):
            ekey = escape_dot(key)
            _walk(d[key], schema.get(ekey, {}))
            if ekey != key:
                d[ekey] = d[key]
                del d[key]

    _walk(content, schema or {})

    return ONDict(content)


def _loadobj(field: Union[fields.Field, Any], value: Any) -> Any:
    # if isinstance(field, fields.Nullable) and value is None:
    #    return value
    if isinstance(
        field, (fields.Bool, fields.Datetime, fields.Float, fields.Int, fields.Str)
    ):
        value = field.from_obj(value)
    return value
