from collections.abc import MutableMapping

from .typing import Generator
from .typing import Key


def normkey(key: Key) -> Generator[str, None, None]:
    if isinstance(key, tuple):
        for k in key:
            yield k
    elif isinstance(key, str):
        if "." in key:
            for k in key.split("."):
                yield k
        else:
            yield key


def merge(d1: dict, d2: dict) -> dict:
    """Update two dicts recursively.

    If either mapping has leaves that are non-dicts, the second's leaf overwrites the
    first's.
    """
    for k, v in d1.items():
        if k in d2:
            if all(isinstance(e, MutableMapping) for e in (v, d2[k])):
                d2[k] = merge(v, d2[k])
    d3 = d1.copy()
    d3.update(d2)
    return d3


def expand(d: dict) -> dict:
    new = {}
    for k, v in d.items():
        dnew = new

        keys = list(normkey(k))
        if len(keys) == 1:
            key = keys[0]
        else:
            for key in keys[:-1]:
                dnew = dnew.setdefault(key, {})
                if not isinstance(dnew, MutableMapping):
                    raise ValueError("Cannot upcast a non-dict node to a dict node")
            key = keys[-1]

        if isinstance(v, MutableMapping):
            expanded = expand(v)
            if key in dnew:
                assert isinstance(dnew[key], MutableMapping)
                dnew[key] = merge(dnew[key], expanded)
            else:
                dnew[key] = expanded
        else:
            dnew[key] = v

    return new
