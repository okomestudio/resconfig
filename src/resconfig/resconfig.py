import os
from copy import deepcopy
from enum import Enum
from logging import getLogger

from .actions import Action
from .dicttype import Dict
from .dicttype import flexdictargs
from .dicttype import isdict
from .dicttype import merge
from .io import IO
from .schema import Schema
from .typing import Any
from .typing import FilePath
from .typing import Key
from .typing import List
from .typing import Optional
from .watchers import Watchable
from .watchers import Watchers

log = getLogger(__name__)


class Sentinel(Enum):
    MISSING = object()
    """Sentinel value for missing value."""

    REMOVE = object()
    """Sentinel value indicating the config key to be removed."""


class ResConfig(Watchable, IO):
    """Application resource configuration.

    Args:
        default: Default config.
        config_paths: List of paths to config files.
        watchers: Config watchers.
        schema: Config schema.
        skip_load_on_init: True to skip config load on initialization.

    """

    def __init__(
        self,
        default: dict = None,
        config_paths: List[FilePath] = None,
        watchers: dict = None,
        schema: dict = None,
        envvar_prefix: str = "",
        skip_load_on_init: bool = False,
    ):
        self._watchers = Watchers()
        for k, v in (watchers or {}).items():
            for func in v if isinstance(v, (list, tuple)) else [v]:
                self.register(k, v)

        self._schema = Schema(schema or {})
        self._default = Dict(default or {})
        self._clargs = Dict()
        self._config_paths = config_paths or []
        self._envvar_prefix = envvar_prefix
        self._conf = Dict()

        if not skip_load_on_init:
            self.load()

    def read_from_argparse(self, args, config_paths=None, keymap=None):
        keymap = keymap or {}
        conf = Dict()
        if config_paths:
            conf.merge(self._read_from_files_as_dict(config_paths))

        for k, v in vars(args).items():
            if k in keymap:
                k = keymap[k]
            else:
                k = ".".join(k.split("_"))
            conf.update({k: v})

        self._clargs = conf

    def __contains__(self, key):
        return key in self._conf

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self.get(key)

    def _prepare_config(
        self,
        from_files: Optional[List[Dict]] = None,
        from_env: Optional[os._Environ] = None,
        from_clargs=None,
    ):
        """Prepare a Dict to update the configuration with."""
        new = deepcopy(self._default)

        for conf in from_files or []:
            new.merge(conf)

        env = os.environ if from_env is None else from_env
        clargs = self._clargs if from_clargs is None else from_clargs

        for key in self._default.allkeys():
            envkey = self._envvar_prefix + ("_".join(key)).upper()
            if envkey in env:
                new[key] = env[envkey]

            if key in clargs:
                new[key] = clargs[key]

        return new

    def _asdict(self) -> dict:
        """Return the configuration as a dict object."""
        return dict(deepcopy(self._conf))

    def load(self):
        from_files = (
            [self._read_from_files_as_dict(self._config_paths)]
            if self._config_paths
            else None
        )
        self.replace(self._prepare_config(from_files=from_files))

    def reset(self):
        """Reset config to default."""
        self.replace(self._prepare_config())

    def get(self, key: Key, default: Optional[Any] = Sentinel.MISSING) -> Any:
        """Get the config item at the key."""
        try:
            value = self._conf[key]
        except Exception:
            if default is Sentinel.MISSING:
                raise
            else:
                return default
        return deepcopy(value)

    def __update(self, key: Key, conf: dict, newconf: dict, replace: bool = False):
        _key = key[-1]

        if not isdict(newconf[_key]):
            newval = self._schema.apply(key[1:], newconf[_key])
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
                key + (subkey,), conf[_key], newconf[_key], replace=replace
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
    def update(self, conf: dict):
        """Update the current config with the new one."""
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf})

    @flexdictargs
    def replace(self, conf: dict):
        """Replace the current config with the new one."""
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf}, replace=True)
