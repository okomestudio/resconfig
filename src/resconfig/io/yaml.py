from ..fields import bool_
from ..fields import datetime_
from ..fields import ddef
from ..fields import float_
from ..fields import int_
from ..fields import str_
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
    if isinstance(vdef, ddef):
        if isinstance(vdef, (bool_, float_, int_, str_)):
            pass
        elif isinstance(vdef, (datetime_,)):
            value = vdef.to_str(value)
        else:
            value = vdef.to_str(value)
    return value


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    content = yaml.load(f, yaml.FullLoader)
    return ONDict(content if content else {})
