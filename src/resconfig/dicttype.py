from collections import OrderedDict
from collections.abc import MutableMapping
from functools import wraps

from .typing import Any
from .typing import Generator
from .typing import Key
from .typing import Tuple

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

    # custom utility methods

    def __allkeys(self, key, d):
        _key = key[-1]
        if not isdict(d[_key]):
            yield key[1:]
            return
        for k in d[_key]:
            for i in self.__allkeys(key + (k,), d[_key]):
                yield i

    def allkeys(self, as_str=False):
        """Generate all keys to the leaves"""
        for key in self.__allkeys(("__ROOT__",), {"__ROOT__": self}):
            yield ".".join(key) if as_str else key

    def merge(self, d):
        merge(self, d)


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


def _get(dic: dict, key: Key, create: bool = False) -> Tuple[dict, Key]:
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


def get(dic: dict, key: Key) -> Any:
    ref, key = _get(dic, key)
    return ref[key]


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


def __merge(a, b):
    for k in b:
        if k in a:
            if isdict(a[k]):
                if isdict(b[k]):
                    __merge(a[k], b[k])
                else:
                    if a[k] != b[k]:
                        a[k] = b[k]
            else:
                if a[k] != b[k]:
                    a[k] = b[k]
        else:
            a[k] = b[k]
    return a


def merge(a: dict, b: dict) -> dict:
    """Merge dict b into a recursively.

    If either dict has leaves that are non-dicts, the leaf in dict b overwrites that in
    dict a.
    """
    return __merge(a, b)


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
