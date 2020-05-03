from collections.abc import MutableMapping
from configparser import ConfigParser

from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Key
from ..typing import Optional
from .utils import escape_dot
from .utils import unescape_dots_in_keys


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    if _depth(content) > 2:
        raise ValueError("INI config does not allow nested options")
    content = _dumpobj(content, schema or {})
    unescape_dots_in_keys(content)
    parser = ConfigParser()
    parser.read_dict(content)
    parser.write(f)


def _dumpobj(content: ONDict, schema: ONDict) -> dict:
    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        value = content[key]
        if key in schema and isinstance(schema[key], fields.Field):
            value = schema[key].to_str(value)
        con[key] = value
    return con.asdict()


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    schema = schema or {}
    parser = ConfigParser()
    parser.read_file(f)
    conf = ONDict()
    for section in parser.sections():
        ref = conf.setdefault(escape_dot(section), ONDict())
        for option in parser[section]:
            key = escape_dot(option)
            ref[key] = _loadobj(schema, key, parser[section], option)
    return conf


def _loadobj(schema: ONDict, key: Key, section: dict, option: str) -> Any:
    if key in schema and isinstance(schema[key], fields.Field):
        vtype = schema[key]
        if isinstance(vtype, fields.Bool):
            value = section.getboolean(option)
        elif isinstance(vtype, fields.Datetime):
            value = section[option]
        elif isinstance(vtype, fields.Float):
            value = section.getfloat(option)
        elif isinstance(vtype, fields.Int):
            value = section.getint(option)
        elif isinstance(vtype, fields.Str):
            value = section[option]
        else:
            value = section[option]
        value = vtype.from_obj(value)
    else:
        value = section[option]
    return value


def _depth(d: dict, depth: int = 0) -> int:
    if not isinstance(d, MutableMapping):
        return depth
    max_depth = depth
    for key in d:
        max_depth = max(max_depth, _depth(d[key], depth + 1))
    return max_depth
