from collections import OrderedDict
from collections.abc import MutableMapping
from copy import deepcopy
from functools import wraps

from .typing import Any
from .typing import Generator
from .typing import Key

_default = object()


class Dict(OrderedDict):
    _create = None

    def __init__(self, *args, **kwargs):
        args, kwargs = _expand_args(args, kwargs)
        super().__init__(*args, **kwargs)

    def __repr__(self):
        items = []
        for k, v in self.items():
            items.append(f"{k!r}: {v!r}")
        return "{{" + ", ".join(items) + "}}"

    def __contains__(self, key):
        try:
            ref, lastkey = _get(self, key, self._create)
        except Exception:
            return False
        return (super() if ref is self else ref).__contains__(lastkey)

    def __delitem__(self, key):
        ref, lastkey = _get(self, key, self._create)
        if lastkey not in ref:
            raise _key_error(ref, key)
        return (super() if ref is self else ref).__delitem__(lastkey)

    def __getitem__(self, key):
        ref, lastkey = _get(self, key, self._create)
        if ref is self:
            return super().__getitem__(lastkey)
        else:
            if lastkey not in ref:
                raise _key_error(ref, key)
            return ref.__getitem__(lastkey)

    def __setitem__(self, key, value):
        ref, lastkey = _get(self, key, self._create)
        return (super() if ref is self else ref).__setitem__(lastkey, value)

    def get(self, key, default=None):
        try:
            ref, lastkey = _get(self, key, self._create)
        except Exception:
            return default
        return (super() if ref is self else ref).get(lastkey, default)

    def pop(self, key, d=_default):
        if d is _default:
            ref, lastkey = _get(self, key, self._create)
            if lastkey not in ref:
                raise _key_error(ref, key)
            return (super() if ref is self else ref).pop(lastkey)
        else:
            try:
                ref, lastkey = _get(self, key, self._create)
            except Exception:
                return d
            return (super() if ref is self else ref).pop(lastkey, d)

    def setdefault(self, key, default=None):
        ref, lastkey = _get(self, key, self._create)
        return (super() if ref is self else ref).setdefault(lastkey, default)

    def update(self, *args, **kwargs):
        args, kwargs = _expand_args(args, kwargs)
        if args:
            if len(args) != 1:
                raise TypeError(f"update expected at most 1 argument, got {len(args)}")
            for k, v in args[0].items():
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]

    @classmethod
    def fromkeys(cls, iterable, value=None):
        dic = cls()
        for key in iterable:
            dic = merge(dic, expand({key: value}))
        return dic


def _expand_args(args, kwargs):
    if args:
        arg = args[0]
        if hasattr(arg, "keys"):
            new = expand(arg)
        else:
            new = Dict()
            for key, val in arg:
                new = merge(new, expand({key: val}))
        args = [new] + list(args[1:])
    return args, expand(kwargs)


def _key_error(obj, key):
    return KeyError(f"'{key}'")


def _type_error(obj, key):
    return TypeError(f"'{type(obj)}' object at '{key}' is not subscriptable")


def _get(dic, key, create=False):
    keys = list(normkey(key))
    ref = dic
    for idx, k in enumerate(keys[:-1]):
        try:
            ref = ref[k]
        except KeyError:
            if not create:
                raise _key_error(ref, ".".join(keys[: idx + 1]))
            ref[k] = dic.__class__()
            ref = ref[k]
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


def expand(d: dict) -> dict:
    if not isdict(d):
        return d
    new = d.__class__()
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
                    ref[k] = d.__class__()
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
