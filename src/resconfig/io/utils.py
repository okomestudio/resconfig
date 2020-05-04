from collections.abc import MutableMapping
from pathlib import Path

from ..typing import FilePath


def ensure_path(path: FilePath) -> Path:
    return (path if isinstance(path, Path) else Path(path)).expanduser()


def escape_dot(key: str) -> str:
    return key.replace(".", r"\.")


def unescape_dot(key: str) -> str:
    return key.replace(r"\.", ".")


def unescape_dots_in_keys(d: dict):
    if not isinstance(d, MutableMapping):
        return
    for k in list(d.keys()):
        unescape_dots_in_keys(d[k])
        uk = unescape_dot(k)
        if uk != k:
            d[uk] = d[k]
            del d[k]


def escape_dots_in_keys(d: dict):
    if not isinstance(d, MutableMapping):
        return
    for k in list(d.keys()):
        escape_dots_in_keys(d[k])
        ek = escape_dot(k)
        if ek != k:
            d[ek] = d[k]
            del d[k]
