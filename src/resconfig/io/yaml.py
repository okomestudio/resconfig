from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    schema = schema or {}
    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        con[key] = _dumpobj(content[key], schema.get(key))
    yaml.dump(con.asdict(), f)


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
    content = yaml.load(f, yaml.FullLoader)
    return ONDict(content if content else {})
