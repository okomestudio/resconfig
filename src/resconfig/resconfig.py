from copy import deepcopy
from enum import Enum
from functools import wraps
from logging import getLogger
from pathlib import Path

from .dicttype import Dict
from .io import IO
from .schema import Schema
from .typing import Any
from .typing import Callable
from .typing import Key
from .typing import List
from .typing import Optional
from .typing import Text
from .utils import expand
from .utils import isdict
from .utils import merge
from .utils import normkey

log = getLogger(__name__)


Missing = object()
"""Sentinel value for missing value."""

REMOVE = object()
"""Sentinel value indicating the config field to be removed."""


class Action(Enum):
    """Action performed by the update method."""

    ADDED = 1
    MODIFIED = 2
    REMOVED = 3
    RELOADED = 4


WatchFunction = Callable[[Action, Any, Any], None]
"""Callback function, i.e., watcher, that triggers on an event happening at the key. It
takes in Action value, old, and new values.
"""


class _Watchable:
    """Mix-in for adding the watch functionality."""

    __watcher_key = "__watchers__"

    def deregister(self, key: Key, func: Optional[WatchFunction] = None):
        """Deregister the watch function for the key."""
        r = self._watchers
        try:
            for k in normkey(key):
                r = r[k]
        except KeyError:
            raise KeyError(f"Watch function not registered for {key}")

        if func is None:
            if self.__watcher_key in r:
                del r[self.__watcher_key]
        else:
            try:
                r[self.__watcher_key].remove(func)
            except KeyError:
                raise KeyError(f"Watch functions not registered for {key}")
            except ValueError:
                raise ValueError(f"{func!r} not registered for {key}")
            # If this was the last watch function, remove the node.
            if not r[self.__watcher_key]:
                del r[self.__watcher_key]

    def register(self, key: Key, func: WatchFunction):
        """Register the watch function for the key."""
        r = self._watchers
        for k in normkey(key):
            r = r.setdefault(k, Dict())
        r.setdefault(self.__watcher_key, []).append(func)

    def _reload(self, watchers, key, action, oldval, newval):
        if key in watchers and self.__watcher_key in watchers[key]:
            for func in watchers[key][self.__watcher_key]:
                func(action, oldval, newval)

    def reload(self):
        """Trigger all watch functions using the current config."""
        for key, val in self._conf.items():
            self._reload(self._watchers, key, Action.RELOADED, val, val)

    def watchers(self, key: Key) -> List[WatchFunction]:
        """Get all watch functions registered for the key."""
        return self._watchers[key][self.__watcher_key]

    def watch(self, key: Key) -> WatchFunction:
        """Decorate a function to make it a watch function for the key."""

        def deco(f):
            @wraps(f)
            def _deco(*args, **kwargs):
                return f(*args, **kwargs)

            self.register(key, _deco)
            return _deco

        return deco


class ResConfig(_Watchable, IO):
    """Resource Configuration.

    Args:
        default: Default configuration.
        watchers: Configuration watchers.
        schema: Configuration schema.

    """

    def __init__(
        self,
        default: dict = None,
        paths: List[Text] = None,
        watchers: dict = None,
        schema: dict = None,
    ):
        self._watchers = Dict()
        if watchers:
            watchers = expand(watchers)
            for k, v in watchers.items():
                self.register(k, v)

        self._schema = Schema(expand(schema) if schema else Dict())

        self._conf = Dict()
        default = expand(default) if default else Dict()
        if paths:
            for path in paths:
                path = Path(path)
                if path.is_file():
                    content = self._load_as_dict(path)
                    default = merge(default, content)
                    break
        if default:
            self.update(default)

    def __contains__(self, key):
        ref = self._conf
        for k in normkey(key):
            if not isdict(ref):
                return False
            if k not in ref:
                return False
            ref = ref[k]
        return True

    def asdict(self) -> dict:
        """Return the configuration as a dict object."""
        return deepcopy(self._conf)

    def get(self, key: Key, default=Missing):
        """Get the config item at the key."""
        ref = self._conf
        for k in normkey(key):
            try:
                ref = ref[k]
            except KeyError:
                if default is Missing:
                    raise
                else:
                    return default
        return deepcopy(ref)

    def __replace(self, conf: dict, newconf: dict, watchers: dict, schema: dict):
        action = None
        keys = list(newconf.keys())
        for key in keys:
            newval = newconf[key]
            action = None
            key_in_old_conf = key in conf

            if isdict(newval):
                oldval = deepcopy(conf[key]) if key_in_old_conf else Missing

                if not key_in_old_conf:
                    conf[key] = Dict()
                else:
                    if not isdict(conf[key]):
                        conf[key] = Dict()

                self.__replace(
                    conf[key],
                    newval,
                    watchers[key] if key in watchers else Dict(),
                    schema.get(key),
                )

                if key_in_old_conf:
                    if oldval != newval:
                        action = Action.MODIFIED
                    del conf[key]
                else:
                    action = Action.ADDED

            else:
                if key_in_old_conf:
                    oldval = deepcopy(conf[key])
                    if oldval != newval:
                        action = Action.MODIFIED
                        newconf[key] = schema.apply(key, newval)
                    del conf[key]
                else:
                    oldval = Missing
                    if newval is not REMOVE:
                        action = Action.ADDED
                        newconf[key] = schema.apply(key, newval)

            if action is not None:
                self._reload(watchers, key, action, oldval, newval)

        for key in tuple(conf.keys()):
            oldval = conf[key]
            if action is not None:
                action = Action.REMOVED
                newval = REMOVE
                self._reload(watchers, key, action, oldval, newval)
            del conf[key]

    def replace(self, *args, **kwargs):
        """Replace config."""
        if args and isdict(args[0]):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise TypeError("Invalid input args")
        newconf = expand(newconf)
        self.__replace(self._conf, newconf, self._watchers, self._schema)
        self._conf = newconf

    def __update(self, conf: dict, newconf: dict, watchers: dict, schema: dict):
        for key, newval in newconf.items():
            action = None

            if isdict(newval):
                key_in_old_conf = key in conf
                oldval = deepcopy(conf[key]) if key_in_old_conf else Missing

                if key not in conf:
                    conf[key] = Dict()
                else:
                    if not isdict(conf[key]):
                        conf[key] = Dict()

                self.__update(
                    conf[key],
                    newval,
                    watchers[key] if key in watchers else Dict(),
                    schema.get(key),
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
                        conf[key] = schema.apply(key, newval)
                else:
                    oldval = Missing
                    if newval is not REMOVE:
                        action = Action.ADDED
                        conf[key] = schema.apply(key, newval)

            if action is not None:
                self._reload(watchers, key, action, oldval, newval)

    def update(self, *args, **kwargs):
        """Update config."""
        if args and isdict(args[0]):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise TypeError("Invalid input args")
        self.__update(self._conf, expand(newconf), self._watchers, self._schema)
