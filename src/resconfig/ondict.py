import re
from collections import OrderedDict
from collections.abc import MutableMapping
from functools import wraps

from .typing import RT
from .typing import Any
from .typing import Callable
from .typing import Generator
from .typing import Iterable
from .typing import Key
from .typing import Mapping
from .typing import Optional
from .typing import Tuple
from .typing import Type

_default = object()


class ONDict(OrderedDict):
    _create = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.merge(*args, **kwargs)

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
        """Update from dict and/or iterable.

        This method takes in the same argument(s) as :meth:`dict.update`. Compared to
        the built-in :class:`dict` object, the update behavior is expanded to allow
        nested key notation.

        Note that update happens only on the top-level keys, just like built-in
        :class:`dict`, to supply consistent behavior. If you desire a full merging
        behavior, use :meth:`ONDict.merge`.

        Raises:
            TypeError: When more than one positional argument is supplied.
            ValueError: When the iterable does not hold two-element items.
        """
        if args:
            if len(args) != 1:
                raise TypeError(f"update expected at most 1 argument, got {len(args)}")
            arg = args[0]
            if hasattr(arg, "keys"):
                super().update(normalize(arg, cls=self.__class__))
            else:
                try:
                    for k, v in arg:
                        super().update(normalize({k: v}, cls=self.__class__))
                except Exception:
                    raise ValueError(
                        "dictionary update sequence element #0 has length "
                        f"{ len(arg[0]) }; 2 is required"
                    )
        for k in kwargs:
            super().update(normalize({k: kwargs[k]}, cls=self.__class__))

    @classmethod
    def fromkeys(cls, iterable, value=None):
        dic = cls()
        for key in iterable:
            dic = merge(dic, normalize({key: value}, cls=cls))
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

    def merge(self, *args, **kwargs):
        """Merge from dict and/or iterable.

        This method takes in the same argument(s) as :meth:`dict.update`, but merge the
        input instead of :class:`dict`-like update. Merging extends the update behavior
        to allow nested updates and to support nested key notation.

        Raises:
            TypeError: When more than one positional argument is supplied.
            ValueError: When the iterable does not hold two-element items.
        """
        if args:
            if len(args) != 1:
                raise TypeError(f"update expected at most 1 argument, got {len(args)}")
            arg = args[0]
            if hasattr(arg, "keys"):
                for k, v in arg.items():
                    merge(self, normalize({k: v}, cls=self.__class__))
            else:
                try:
                    for k, v in arg:
                        merge(self, normalize({k: v}, cls=self.__class__))
                except Exception:
                    raise ValueError(
                        "dictionary update sequence element #0 has length "
                        f"{ len(arg[0]) }; 2 is required"
                    )
        for k in kwargs:
            merge(self, normalize({k: kwargs[k]}, cls=self.__class__))


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
    """Normalize key.

    If the input key is “.”-delimit nested keys, it is split on the delimiter. If the
    input key is a tuple of keys, they are simply yielded.

    In the string form, escaped “.” characters are not interpreted as delimiters.

    Args:
        key: Input key.

    Returns:
        Generator of str keys.

    Raises:
        TypeError: When input key is neither :class:`str` or :class:`tuple`.
    """
    if isinstance(key, tuple):
        for k in key:
            yield k
    elif isinstance(key, str):
        if "." in key:
            for k in re.split(r"(?<!\\)\.", key):
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


def normalize(
    d: Mapping[Key, Any], cls: Optional[Type[Mapping]] = None
) -> Mapping[Key, Any]:
    """Normalize the :class:`dict` by expanding nested keys.

    This function returns a new :class:`dict` object by expanding the nested keys and
    their values into nested :class:`dict` objects.

    Args:
        d: Dict to be normalized
        cls: The mapping class for creating new (nested) mappings.

    Raises:
        TypeError: When an attempt is made to convert a non-:class:`dict` node to a
            :class:`dict` node.
    """
    if not isinstance(d, MutableMapping):
        return d
    cls = cls or d.__class__
    new = cls()
    for key, value in d.items():
        keys = list(normkey(key))
        if len(keys) == 1:
            k = keys[0]
            expanded = normalize(value, cls=cls)
            new[k] = (
                merge(new[k], expanded)
                if k in new and isinstance(new[k], MutableMapping)
                else expanded
            )
        else:
            ref = new
            for idx, k in enumerate(keys[:-1]):
                if k not in ref:
                    ref[k] = cls()
                ref = ref[k]
                if not isinstance(ref, MutableMapping):
                    k = ".".join(keys[: idx + 1])
                    raise TypeError(
                        f"cannot convert a node from non-dict to dict at '{k}'"
                    )
            k = keys[-1]
            expanded = normalize(value, cls=cls)
            ref[k] = (
                merge(ref[k], expanded)
                if k in ref and isinstance(ref[k], MutableMapping)
                else expanded
            )
    return new


def flexdictargs(func: Callable[[dict], RT]) -> Callable[[Iterable, Any], RT]:
    """Decorate a method to add dict.update()-like interface.

    The decorated method should take one :class:`dict` object as an argument. Then the
    decorator makes it possible to accept an iterable or :class:`dict` as keyword
    arguments. The output :class:`dict`
    """

    @wraps(func)
    def f(self, *args, **kwargs):
        if args and isinstance(args[0], MutableMapping):
            d = args[0]
        elif kwargs:
            d = kwargs
        else:
            raise TypeError("invalid input arguments")
        return func(self, normalize(d))

    return f


def isdict(val: Any) -> bool:
    """Test if the value is dict."""
    return isinstance(val, MutableMapping)
