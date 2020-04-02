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
from .typing import List
from .typing import Optional
from .utils import apply_schema
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
            r = r.setdefault(k, dicttype())
        r.setdefault(self.__watcher_key, []).append(func)

    def _reload(self, watchers, schema, key, action, oldval, newval):
        if key in watchers and self.__watcher_key in watchers[key]:
            sche = schema.get(key, {})
            oldval = apply_schema(sche, oldval) if oldval is not Missing else oldval
            newval = apply_schema(sche, newval)
            for func in watchers[key][self.__watcher_key]:
                func(action, oldval, newval)

    def reload(self):
        """Trigger all watch functions using the current config."""
        for key, val in self._conf.items():
            self._reload(self._watchers, self._schema, key, Action.RELOADED, val, val)

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


class _IO:
    def read_from_dict(self, dic):
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


class ResConfig(_Watchable, _IO):
    """Resource Configuration.

    Args:
        default: Default configuration.
        watchers: Configuration watchers.
        schema: Configuration schema.

    """

    def __init__(
        self, default: dict = None, watchers: dict = None, schema: dict = None
    ):
        self._watchers = dicttype()
        if watchers:
            for k, v in watchers.items():
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

    def asdict(self) -> dict:
        """Returns the configuration as a dict object."""
        return self._conf

    def get(self, key: Key, default=Missing):
        """Get the config item at the key."""
        s = self._schema
        d = self._conf
        for k in normkey(key):
            try:
                s = s.get(k, {})
                d = d[k]
            except KeyError:
                if default is Missing:
                    raise
                else:
                    return default
        return apply_schema(s, d)

    def _replace(
        self, conf: dict, newconf: dict, watchers: dict, schema: dict, reload=True
    ):
        for key, newval in newconf.items():
            action = None
            key_in_old_conf = key in conf

            if isdict(newval):
                oldval = deepcopy(conf[key]) if key_in_old_conf else Missing

                if not key_in_old_conf:
                    conf[key] = dicttype()
                else:
                    if not isdict(conf[key]):
                        conf[key] = dicttype()

                self._replace(
                    conf[key],
                    newval,
                    watchers[key] if key in watchers else dicttype(),
                    schema[key] if key in schema else dicttype(),
                    reload=reload,
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
                    del conf[key]
                else:
                    oldval = Missing
                    if newval is not REMOVE:
                        action = Action.ADDED

            if reload and action is not None:
                self._reload(watchers, schema, key, action, oldval, newval)

        for key in tuple(conf.keys()):
            oldval = conf[key]
            if reload and action is not None:
                action = Action.REMOVED
                newval = REMOVE
                self._reload(watchers, schema, key, action, oldval, newval)
            del conf[key]

    def replace(self, *args, reload: bool = True, **kwargs):
        """Replace config."""
        if args and isdict(args[0]):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise TypeError("Invalid input args")
        newconf = expand(newconf)
        self._replace(self._conf, newconf, self._watchers, self._schema, reload)
        self._conf = newconf

    def _update(
        self, conf: dict, newconf: dict, watchers: dict, schema: dict, reload=True
    ):
        for key, newval in newconf.items():
            action = None

            if isdict(newval):
                key_in_old_conf = key in conf
                oldval = deepcopy(conf[key]) if key_in_old_conf else Missing

                if key not in conf:
                    conf[key] = dicttype()
                else:
                    if not isdict(conf[key]):
                        conf[key] = dicttype()

                self._update(
                    conf[key],
                    newval,
                    watchers[key] if key in watchers else dicttype(),
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
                    oldval = Missing
                    if newval is not REMOVE:
                        action = Action.ADDED
                        conf[key] = newval

            if reload and action is not None:
                self._reload(watchers, schema, key, action, oldval, newval)

    def update(self, *args, reload: bool = True, **kwargs):
        """Update config."""
        if args and isdict(args[0]):
            newconf = args[0]
        elif kwargs:
            newconf = kwargs
        else:
            raise ValueError("Invalid input args")
        self._update(self._conf, expand(newconf), self._watchers, self._schema, reload)
