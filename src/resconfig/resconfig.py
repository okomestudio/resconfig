from copy import deepcopy
from enum import Enum
from logging import getLogger
from pathlib import Path

from .actions import Action
from .dicttype import Dict
from .dicttype import flexdictargs
from .dicttype import isdict
from .dicttype import merge
from .io import IO
from .schema import Schema
from .typing import Key
from .typing import List
from .typing import Text
from .watchers import Watchable
from .watchers import Watchers

log = getLogger(__name__)


class Sentinel(Enum):
    MISSING = object()
    """Sentinel value for missing value."""

    REMOVE = object()
    """Sentinel value indicating the config field to be removed."""


class ResConfig(Watchable, IO):
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
        self._watchers = Watchers()
        for k, v in (watchers or {}).items():
            for func in v if isinstance(v, (list, tuple)) else [v]:
                self.register(k, v)

        self._schema = Schema(schema or {})

        self._conf = Dict()
        default = Dict(default or {})
        if paths:
            d = self.config_from_file(paths)
            default = merge(default, d)
        if default:
            self.update(default)

    def __contains__(self, key):
        return key in self._conf

    def asdict(self) -> dict:
        """Return the configuration as a dict object."""
        return dict(deepcopy(self._conf))

    def get(self, key: Key, default=Sentinel.MISSING):
        """Get the config item at the key."""
        try:
            value = self._conf[key]
        except Exception:
            if default is Sentinel.MISSING:
                raise
            else:
                return default
        return deepcopy(value)

    def __update(
        self, key: Key, conf: dict, newconf: dict, schema: dict, replace: bool = False
    ):
        _key = key[-1]

        if not isdict(newconf[_key]):
            newval = schema.apply(_key, newconf[_key])
            action = None
            if not isdict(conf):
                oldval = Sentinel.MISSING
                if newval is not Sentinel.REMOVE:
                    action = Action.ADDED
            elif _key not in conf or conf[_key] is Sentinel.MISSING or not conf[_key]:
                oldval = Sentinel.MISSING
                if newval is not Sentinel.REMOVE:
                    action = Action.ADDED
            else:
                oldval = deepcopy(conf[_key])
                if newval is Sentinel.REMOVE:
                    action = Action.REMOVED
                elif oldval != newval:
                    action = Action.MODIFIED
            return action, oldval, newval

        oldval_at_dict_node = deepcopy(conf[_key]) if _key in conf else Sentinel.MISSING
        newval_at_dict_node = Dict()

        conf.setdefault(_key, Dict())

        for subkey in newconf[_key].keys():
            if not isdict(conf[_key]):
                conf[_key] = Dict()

            action, oldval, newval = self.__update(
                key + (subkey,),
                conf[_key],
                newconf[_key],
                schema.get(_key),
                replace=replace,
            )

            # Actually update the config storage
            if action in (Action.MODIFIED, Action.ADDED):
                if isdict(newval):
                    newval = merge(conf[_key][subkey], newval)
                    newval_at_dict_node[subkey] = merge(
                        newval_at_dict_node.setdefault(subkey, Dict()), newval
                    )
                else:
                    newval_at_dict_node[subkey] = newval

                conf[_key][subkey] = newval

            elif action in (Action.REMOVED,):
                del conf[_key][subkey]
                if subkey in newval_at_dict_node:
                    del newval_at_dict_node[subkey]

            # If an action occurs, trigger its watch functions
            if action is not None and self._watchers.exists(key[1:] + (subkey,)):
                self._watchers.trigger(key[1:] + (subkey,), action, oldval, newval)

        if replace:
            seen = set(newconf[_key].keys())
            for subkey in (k for k in list(conf[_key].keys()) if k not in seen):
                if self._watchers.exists(key[1:] + (subkey,)):
                    self._watchers.trigger(
                        key[1:] + (subkey,),
                        Action.REMOVED,
                        conf[_key][subkey],
                        Sentinel.REMOVE,
                    )
                del conf[_key][subkey]

        # Define the action performed on this dict node.
        action = None
        if newval_at_dict_node:
            if not oldval_at_dict_node or oldval_at_dict_node is Sentinel.MISSING:
                action = Action.ADDED
                oldval_at_dict_node = Sentinel.MISSING
            else:
                if newval_at_dict_node != oldval_at_dict_node:
                    action = Action.MODIFIED
        elif not oldval_at_dict_node:
            action = Action.REMOVED

        return action, oldval_at_dict_node, newval_at_dict_node

    @flexdictargs
    def update(self, conf):
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf}, {k: self._schema})

    @flexdictargs
    def replace(self, conf):
        """Replace config."""
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf}, {k: self._schema}, True)
