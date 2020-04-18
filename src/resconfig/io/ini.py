from collections.abc import MutableMapping
from configparser import ConfigParser

from ..typing import IO


def load(f: IO) -> dict:
    parser = ConfigParser()
    parser.read_file(f)
    dic = {}
    for section in parser.sections():
        ref = dic.setdefault(_escape_dot(section), {})
        for option in parser[section]:
            ref[_escape_dot(option)] = parser[section][option]
    return dic


def dump(content: dict, f: IO):
    if _depth(content) > 2:
        raise ValueError("INI config does not allow nested options")

    _unescape_all_keys(content)

    parser = ConfigParser()
    parser.read_dict(content)
    parser.write(f)


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
