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
from .utils import flexdictargs
from .utils import isdict
from .utils import merge
from .utils import normkey

log = getLogger(__name__)


class Sentinel(Enum):
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

    def get(self, key: Key, default=Sentinel.Missing):
        """Get the config item at the key."""
        ref = self._conf
        for k in normkey(key):
            try:
                ref = ref[k]
            except KeyError:
                if default is Sentinel.Missing:
                    raise
                else:
                    return default
        return deepcopy(ref)

    def __update(
        self,
        key: Key,
        conf: dict,
        newconf: dict,
        watchers: dict,
        schema: dict,
        replace: bool = False,
    ):
        if not isdict(newconf[key]):
            newval = schema.apply(key, newconf[key])
            action = None
            if not isdict(conf):
                oldval = Sentinel.Missing
                if newval is not Sentinel.REMOVE:
                    action = Action.ADDED
            elif key not in conf or conf[key] is Sentinel.Missing or not conf[key]:
                oldval = Sentinel.Missing
                if newval is not Sentinel.REMOVE:
                    action = Action.ADDED
            else:
                oldval = deepcopy(conf[key])
                if newval is Sentinel.REMOVE:
                    action = Action.REMOVED
                elif oldval != newval:
                    action = Action.MODIFIED
            return action, oldval, newval

        oldval_at_dict_node = deepcopy(conf[key]) if key in conf else Sentinel.Missing
        newval_at_dict_node = Dict()

        conf.setdefault(key, Dict())

        for subkey in newconf[key].keys():
            action, oldval, newval = self.__update(
                subkey,
                conf[key],
                newconf[key],
                watchers.get(key, Dict()),
                schema.get(key),
                replace=replace,
            )

            # Actually update the config storage
            if action in (Action.MODIFIED, Action.ADDED):
                if isdict(newval):
                    newval = merge(conf[key][subkey], newval)
                    newval_at_dict_node[subkey] = merge(
                        newval_at_dict_node.setdefault(subkey, Dict()), newval
                    )
                else:
                    newval_at_dict_node[subkey] = newval

                if not isdict(conf[key]):
                    conf[key] = Dict()
                conf[key][subkey] = newval

            elif action in (Action.REMOVED,):
                del conf[key][subkey]
                if subkey in newval_at_dict_node:
                    del newval_at_dict_node[subkey]

            # If an action occurs, trigger its watch functions
            if action is not None:
                self._reload(watchers.get(key, Dict()), subkey, action, oldval, newval)

        if replace:
            seen = set(newconf[key].keys())
            for subkey in (k for k in list(conf[key].keys()) if k not in seen):
                self._reload(
                    watchers.get(key, Dict()),
                    subkey,
                    Action.REMOVED,
                    conf[key][subkey],
                    Sentinel.REMOVE,
                )
                del conf[key][subkey]

        # Define the action performed on this dict node.
        action = None
        if newval_at_dict_node:
            if not oldval_at_dict_node or oldval_at_dict_node is Sentinel.Missing:
                action = Action.ADDED
                oldval_at_dict_node = Sentinel.Missing
            else:
                if newval_at_dict_node != oldval_at_dict_node:
                    action = Action.MODIFIED
        elif not oldval_at_dict_node:
            action = Action.REMOVED

        return action, oldval_at_dict_node, newval_at_dict_node

    @flexdictargs
    def update(self, conf):
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update(
            k, {k: self._conf}, {k: conf}, {k: self._watchers}, {k: self._schema}
        )

    @flexdictargs
    def replace(self, conf):
        """Replace config."""
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update(
            k, {k: self._conf}, {k: conf}, {k: self._watchers}, {k: self._schema}, True
        )
