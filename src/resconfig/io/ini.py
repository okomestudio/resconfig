from collections.abc import MutableMapping
from configparser import ConfigParser

from .. import fields
from ..ondict import ONDict
from ..typing import IO
from ..typing import Any
from ..typing import Optional
from .utils import escape_dot
from .utils import unescape_dots_in_keys


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    if _depth(content) > 2:
        raise ValueError("INI config does not allow nested options")
    schema = schema or {}

    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        con[key] = _dumpobj(content[key], schema.get(key))

    con = con.asdict()

    unescape_dots_in_keys(con)
    parser = ConfigParser()
    parser.read_dict(con)
    parser.write(f)


def _dumpobj(value, field) -> Any:
    if isinstance(field, fields.Field):
        value = field.to_str(value)
    return value


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    schema = schema or {}
    parser = ConfigParser()
    parser.read_file(f)
    conf = ONDict()
    conf._create = True
    for section in parser.sections():
        section_key = escape_dot(section)
        ref = conf.setdefault(section_key, ONDict())
        for option in parser[section]:
            option_key = escape_dot(option)
            ref[option_key] = _loadobj(
                schema.get((section_key, option_key)), parser[section][option]
            )
    return conf


def _loadobj(field, value) -> Any:
    if isinstance(field, fields.Field):
        value = field.from_obj(value)
    return value


def _depth(d: dict, depth: int = 0) -> int:
    if not isinstance(d, MutableMapping):
        return depth
    max_depth = depth
    for key in d:
        max_depth = max(max_depth, _depth(d[key], depth + 1))
    return max_depth
