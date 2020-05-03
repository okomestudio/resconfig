from collections.abc import MutableMapping
from json import dump as _dump
from json import load as _load
from json.decoder import JSONDecodeError

from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Optional
from ..typing import Union
from .utils import escape_dot


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    schema = schema or {}
    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        con[key] = _dumpobj(content[key], schema.get(key))
    _dump(con.asdict(), f)


def _dumpobj(value, vdef) -> Any:
    if isinstance(vdef, fields.Field):
        if isinstance(vdef, (fields.Bool, fields.Float, fields.Int, fields.Str)):
            pass
        elif isinstance(vdef, (fields.Datetime,)):
            value = vdef.to_str(value)
        else:
            value = vdef.to_str(value)
    return value


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    try:
        content = _load(f)
    except JSONDecodeError:
        content = {}

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


def _loadobj(vdef: Union[fields.Field, Any], value: Any) -> Any:
    if isinstance(
        vdef, (fields.Bool, fields.Datetime, fields.Float, fields.Int, fields.Str)
    ):
        value = vdef.from_obj(value)
    return value
