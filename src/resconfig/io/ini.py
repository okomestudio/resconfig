from collections.abc import MutableMapping
from configparser import ConfigParser

from ..ddefs import ddef
from ..ondict import ONDict
from ..typing import IO


def load(f: IO) -> ONDict:
    parser = ConfigParser()
    parser.read_file(f)
    dic = ONDict()
    for section in parser.sections():
        ref = dic.setdefault(_escape_dot(section), {})
        for option in parser[section]:
            ref[_escape_dot(option)] = parser[section][option]
    return dic


def dump(content: ONDict, f: IO, spec=None):
    if _depth(content) > 2:
        raise ValueError("INI config does not allow nested options")

    content = _make_dumpable(content, spec or {})

    _unescape_all_keys(content)

    parser = ConfigParser()
    parser.read_dict(content)
    parser.write(f)


def _make_dumpable(content: ONDict, spec) -> dict:
    con = ONDict()
    con._create = True
    for key in list(content.allkeys()):
        con[key] = _to_dumpable(content[key], spec.get(key))
    return con.asdict()


def _to_dumpable(value, from_spec):
    if isinstance(from_spec, ddef):
        value = str(value)
    return value


def _escape_dot(key: str) -> str:
    return key.replace(".", r"\.")


def _unescape_dot(key: str) -> str:
    return key.replace(r"\.", ".")


def _unescape_all_keys(d: dict):
    if not isinstance(d, MutableMapping):
        return
    for k in list(d.keys()):
        _unescape_all_keys(d[k])
        uk = _unescape_dot(k)
        if uk != k:
            d[uk] = d[k]
            del d[k]


def _depth(d: dict, depth: int = 0) -> int:
    if not isinstance(d, MutableMapping):
        return depth
    max_depth = depth
    for key in d:
        max_depth = max(max_depth, _depth(d[key], depth + 1))
    return max_depth
