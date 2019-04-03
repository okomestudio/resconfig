from collections import OrderedDict as dicttype
from copy import deepcopy
from enum import Enum
from functools import wraps

from .typing import Any
from .typing import Callable
from .typing import Key
from .typing import Optional
from .utils import normkey
from .utils import expand


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


Reloader = Callable[[Action, Any, Any], None]


class _Reloadable:
    """Mix-in for adding the reloader functionality."""

    def deregister(self, key: Key, func: Optional[Reloader] = None):
        r = self._reloaders
        for k in normkey(key):
            r = r[k]
        if func is None:
            del r[self.reloaderkey]
        else:
            r[self.reloaderkey].remove(func)
            if len(r[self.reloaderkey]) == 0:
                del r[self.reloaderkey]

    def register(self, key: Key, func: Reloader):
        """Register a reloader function to key."""
        r = self._reloaders
        for k in normkey(key):
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


class ResConfig(_Reloadable):
    """Resource Configuration."""

    reloaderkey = "__reloader__"

    def __init__(self, default=None):
        self._conf = deepcopy(default) or dicttype()
        self._reloaders = dicttype()

    def get(self, key: Key, default=missing):
        """Get the config item at the key."""
        d = self._conf
        for k in normkey(key):
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

    def _update(self, conf: dict, newconf: dict, reloaders: dict, reload=True):
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

    def update(self, *args, reload: bool = True, **kwargs):
        """Update config."""
        if args and isinstance(args[0], dict):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise ValueError("Invalid input args")
        newconf = expand(newconf)
        self._update(self._conf, newconf, self._reloaders, reload=reload)
