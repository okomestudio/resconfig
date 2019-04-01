from collections import OrderedDict as dicttype
from copy import deepcopy
from enum import Enum
from functools import wraps
from typing import Any
from typing import Callable
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import Union


missing = object()
"""Sentinel value for missing value."""

REMOVE = object()
"""Sentinel value indicating the config field to be removed."""


class Action(Enum):
    """Action performed by the update method."""

    ADDED = 1
    MODIFIED = 2
    REMOVED = 3
    RELOADED = 4


# Custom types

Reloader = Callable[[Action, Any, Any], None]
Key = Union[str, Tuple[str]]


def _normkey(key: Key) -> Generator[str, None, None]:
    if isinstance(key, str):
        for k in key.split("."):
            yield k
    else:
        yield key


class ResConfig:
    """Resource Configuration."""

    reloaderkey = "__reloader__"

    def __init__(self, default=None):
        self._conf = deepcopy(default) or dicttype()
        self._reloaders = dicttype()

    def deregister(self, key: Key, func: Optional[Reloader] = None):
        r = self._reloaders
        for k in _normkey(key):
            r = r[k]
        if func is None:
            del r[self.reloaderkey]
        else:
            r[self.reloaderkey].remove(func)
            if len(r[self.reloaderkey]) == 0:
                del r[self.reloaderkey]

    def get(self, key: Key, default=missing):
        """Get the config item at the key."""
        d = self._conf
        for k in _normkey(key):
            try:
                d = d[k]
            except KeyError:
                if default is missing:
                    raise
                else:
                    return default
        return d

    def load(self, filename):
        pass

    def load_from_dict(self, dic):
        pass

    def register(self, key: Key, func: Reloader):
        """Register a reloader function to key."""
        r = self._reloaders
        for k in _normkey(key):
            r = r.setdefault(k, dicttype())
        r.setdefault(self.reloaderkey, []).append(func)

    def _reload(self, reloaders, key, action, oldval, newval):
        if key in reloaders and self.reloaderkey in reloaders[key]:
            for func in reloaders[key][self.reloaderkey]:
                func(action, oldval, newval)

    def reload(self):
        """Trigger all registered reloaders using the current config."""
        for key, val in self._conf.items():
            self._reload(self._reloaders, key, Action.RELOADED, val, val)

    def reloader(self, key: Key) -> Reloader:
        """Decorate a reloader function."""

        def deco(f):
            @wraps(f)
            def _deco(*args, **kwargs):
                return f(*args, **kwargs)

            self.register(key, _deco)
            return _deco

        return deco

    def _update(self, conf, newconf, reloaders, reload=True):
        for key, newval in newconf.items():
            action = None

            if isinstance(newval, dict):
                oldval = deepcopy(conf[key]) if key in conf else None
                self._update(
                    conf.setdefault(key, dicttype()),
                    newval,
                    reloaders[key] if key in reloaders else dicttype(),
                    reload=reload,
                )
                if key in conf:
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

            if reload:
                self._reload(reloaders, key, action, oldval, newval)

    def update(self, newconf: dicttype, reload: bool = True):
        """Update config."""
        self._update(self._conf, newconf, self._reloaders, reload=reload)
