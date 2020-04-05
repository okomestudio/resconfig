from collections import OrderedDict
from collections.abc import MutableMapping
from copy import deepcopy
from functools import wraps

from .typing import Any
from .typing import Generator
from .typing import Key

_default = object()


class Dict(OrderedDict):
    def __repr__(self):
        items = []
        for k, v in self.items():
            items.append(f"{k!r}: {v!r}")
        return "{{" + ", ".join(items) + "}}"

    def __contains__(self, key):
        try:
            ref, lastkey = _get(self, key)
        except Exception:
            return False
        return (super() if ref is self else ref).__contains__(lastkey)

    def __delitem__(self, key):
        ref, lastkey = _get(self, key)
        if lastkey not in ref:
            raise _key_error(ref, key)
        return (super() if ref is self else ref).__delitem__(lastkey)

    def __getitem__(self, key):
        ref, lastkey = _get(self, key)
        if ref is self:
            return super().__getitem__(lastkey)
        else:
            if lastkey not in ref:
                raise _key_error(ref, key)
            return ref.__getitem__(lastkey)

    def __setitem__(self, key, value):
        ref, lastkey = _get(self, key)
        return (super() if ref is self else ref).__setitem__(lastkey, value)

    def get(self, key, default=None):
        try:
            ref, lastkey = _get(self, key)
        except Exception:
            return default
        return (super() if ref is self else ref).get(lastkey, default)

    def pop(self, key, d=_default):
        if d is _default:
            ref, lastkey = _get(self, key)
            if lastkey not in ref:
                raise _key_error(ref, key)
            return (super() if ref is self else ref).pop(lastkey)
        else:
            try:
                ref, lastkey = _get(self, key)
            except Exception:
                return d
            return (super() if ref is self else ref).pop(lastkey, d)

    def setdefault(self, key, default=None):
        ref, lastkey = _get(self, key)
        return (super() if ref is self else ref).setdefault(lastkey, default)

    def update(self, *args, **kwargs):
        if args:
            if len(args) == 1:
                e = args[0]
                if hasattr(e, "keys"):
                    e = expand(e)
                    for k in e:
                        self[k] = e[k]
                else:
                    for k, v in e:
                        v = expand({k: v})
                        for kk, vv in v.items():
                            self[kk] = vv
            else:
                raise TypeError(f"update expected at most 1 argument, got {len(args)}")
        kwargs = expand(kwargs)
        for k in kwargs:
            self[k] = kwargs[k]

    @classmethod
    def fromkeys(cls, iterable, value=None):
        dic = cls()
        for key in iterable:
            dic = merge(dic, expand({key: value}))
        return dic


def _key_error(obj, key):
    return KeyError(f"'{key}'")


def _type_error(obj, key):
    return TypeError(f"'{type(obj)}' object at '{key}' is not subscriptable")


def _get(dic, key):
    keys = list(normkey(key))
    ref = dic
    for idx, k in enumerate(keys[:-1]):
        try:
            ref = ref[k]
        except KeyError:
            raise _key_error(ref, ".".join(keys[: idx + 1]))
        except TypeError:
            raise _type_error(ref, ".".join(keys[: idx + 1]))
    if not isdict(ref):
        raise _type_error(ref, key)
    return ref, keys[-1]


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
    else:
        raise TypeError("key must be str or tuple")


def normkeyget(dic: dict, key: Key, default: Any = None) -> Any:
    ref = dic
    for k in normkey(key):
        try:
            ref = ref[k]
        except KeyError:
            return default
    return ref


def _merge(d1, d2):
    for k, v in d1.items():
        if k in d2:
            if isdict(v) and isdict(d2[k]):
                d2[k] = _merge(v, d2[k])
    d3 = d1.copy()
    d3.update(d2)
    return d3


def merge(d1: dict, d2: dict) -> dict:
    """Update two dicts recursively.

    If either mapping has leaves that are non-dicts, the second's leaf overwrites the
    first's.
    """
    return _merge(deepcopy(d1), deepcopy(d2))


def expand(d: dict) -> Dict:
    if not isdict(d):
        return d
    new = Dict()
    for key, value in d.items():
        keys = list(normkey(key))
        if len(keys) == 1:
            k = keys[0]
            expanded = expand(value)
            new[k] = (
                merge(new[k], expanded) if k in new and isdict(new[k]) else expanded
            )
        else:
            ref = new
            for idx, k in enumerate(keys[:-1]):
                if k not in ref:
                    ref[k] = Dict()
                ref = ref[k]
                if not isdict(ref):
                    k = ".".join(keys[: idx + 1])
                    raise TypeError(
                        f"cannot convert a node from non-dict to dict at '{k}'"
                    )
            k = keys[-1]
            expanded = expand(value)
            ref[k] = (
                merge(ref[k], expanded) if k in ref and isdict(ref[k]) else expanded
            )
    return new


def flexdictargs(func):
    @wraps(func)
    def f(self, *args, **kwargs):
        if args and isdict(args[0]):
            dic = args[0]
        elif kwargs:
            dic = kwargs
        else:
            raise TypeError("invalid input arguments")
        dic = expand(dic)
        return func(self, dic)

    return f


def isdict(val: Any) -> bool:
    """Test if the value is dict."""
    return isinstance(val, MutableMapping)
