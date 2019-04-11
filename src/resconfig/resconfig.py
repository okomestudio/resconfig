from collections import OrderedDict as dicttype
from copy import deepcopy
from enum import Enum
from functools import wraps
from logging import getLogger

from . import json
from . import yaml
from .typing import Any
from .typing import Callable
from .typing import Key
from .typing import Optional
from .utils import apply_schema
from .utils import expand
from .utils import isdict
from .utils import merge
from .utils import normkey


log = getLogger(__name__)


_missing = object()
"""Sentinel value for missing value."""

REMOVE = object()
"""Sentinel value indicating the config field to be removed."""


class Action(Enum):
    """Action performed by the update method."""

    ADDED = 1
    MODIFIED = 2
    REMOVED = 3
    RELOADED = 4


Reloader = Callable[[Action, Any, Any], None]


class _Reloadable:
    """Mix-in for adding the reloader functionality."""

    reloaderkey = "__reloader__"

    def deregister(self, key: Key, func: Optional[Reloader] = None):
        """Deregister the reloader function for the key."""
        r = self._reloaders
        try:
            for k in normkey(key):
                r = r[k]
        except KeyError:
            raise KeyError(f"Reloader not registered at {key}")

        if func is None:
            if self.reloaderkey in r:
                del r[self.reloaderkey]
        else:
            try:
                r[self.reloaderkey].remove(func)
            except KeyError:
                raise KeyError(f"Reloaders not registered at {key}")
            except ValueError:
                raise ValueError(f"{func!r} not registered at {key}")
            # If this was the last reloader, remove the node entirely.
            if len(r[self.reloaderkey]) == 0:
                del r[self.reloaderkey]

    def register(self, key: Key, func: Reloader):
        """Register the reloader function for the key."""
        r = self._reloaders
        for k in normkey(key):
            r = r.setdefault(k, dicttype())
        r.setdefault(self.reloaderkey, []).append(func)

    def _reload(self, reloaders, schema, key, action, oldval, newval):
        if key in reloaders and self.reloaderkey in reloaders[key]:
            oldval = apply_schema(schema, oldval)
            newval = apply_schema(schema, newval)
            for func in reloaders[key][self.reloaderkey]:
                func(action, oldval, newval)

    def reload(self):
        """Trigger all registered reloaders using the current config."""
        for key, val in self._conf.items():
            self._reload(self._reloaders, self._schema, key, Action.RELOADED, val, val)

    def reloader(self, key: Key) -> Reloader:
        """Decorate a reloader function."""

        def deco(f):
            @wraps(f)
            def _deco(*args, **kwargs):
                return f(*args, **kwargs)

            self.register(key, _deco)
            return _deco

        return deco


class _IO:
    def read_from_dict(self, dic):
        self._conf = dicttype()
        self.update(dic)

    def read_from_json(self, filename):
        with open(filename) as f:
            loaded = json.load(f)
        self.read_from_dict(loaded)

    def read_from_yaml(self, filename):
        with open(filename) as f:
            loaded = yaml.load(f)
        self.read_from_dict(loaded)

    def save_to_json(self, filename):
        with open(filename, "w") as f:
            json.dump(self._conf, f)

    def save_to_yaml(self, filename):
        with open(filename, "w") as f:
            yaml.dump(self._conf, f)


class ResConfig(_Reloadable, _IO):
    """Resource Configuration.

    Args:
        default: Default configuration.
        reloaders: Configuration reloaders.
        schema: Configuration schema.

    """

    def __init__(
        self, default: dict = None, reloaders: dict = None, schema: dict = None
    ):
        self._reloaders = dicttype()
        if reloaders:
            for k, v in reloaders.items():
                self.register(k, v)

        self._schema = expand(schema) if schema else dicttype()

        self._conf = dicttype()
        if default:
            self.update(default)

    def __contains__(self, key):
        r = self._conf
        for k in normkey(key):
            if not isdict(r):
                return False
            if k not in r:
                return False
            r = r[k]
        return True

    def get(self, key: Key, default=_missing):
        """Get the config item at the key."""
        s = self._schema
        d = self._conf
        for k in normkey(key):
            try:
                s = s.get(k, {})
                d = d[k]
            except KeyError:
                if default is _missing:
                    raise
                else:
                    return default
        return apply_schema(s, d)

    def _update(
        self, conf: dict, newconf: dict, reloaders: dict, schema: dict, reload=True
    ):
        for key, newval in newconf.items():
            action = None

            if isdict(newval):
                key_in_old_conf = key in conf
                oldval = deepcopy(conf[key]) if key_in_old_conf else None

                if key not in conf:
                    conf[key] = dicttype()
                else:
                    if not isdict(conf[key]):
                        conf[key] = dicttype()

                self._update(
                    conf[key],
                    newval,
                    reloaders[key] if key in reloaders else dicttype(),
                    schema[key] if key in schema else dicttype(),
                    reload=reload,
                )

                if key_in_old_conf:
                    if isdict(oldval):
                        newval = merge(oldval, newval)

                    if oldval != newval:
                        action = Action.MODIFIED
                else:
                    action = Action.ADDED

            else:
                if key in conf:
                    oldval = deepcopy(conf[key])
                    if newval is REMOVE:
                        action = Action.REMOVED
                        del conf[key]
                    elif oldval != newval:
                        action = Action.MODIFIED
                        conf[key] = newval
                else:
                    oldval = None
                    if newval is not REMOVE:
                        action = Action.ADDED
                        conf[key] = newval

            if reload and action is not None:
                self._reload(reloaders, schema, key, action, oldval, newval)

    def update(self, *args, reload: bool = True, **kwargs):
        """Update config."""
        if args and isdict(args[0]):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise ValueError("Invalid input args")
        self._update(self._conf, expand(newconf), self._reloaders, self._schema, reload)
