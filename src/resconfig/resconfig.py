import os
from collections.abc import Iterable
from copy import deepcopy
from enum import Enum
from logging import getLogger

from .actions import Action
from .clargs import CLArgs
from .io import IO
from .io.io import read_from_files_as_dict
from .io.utils import ensure_path
from .ondict import ONDict
from .ondict import flexdictargs
from .ondict import isdict
from .ondict import merge
from .schema import Schema
from .typing import Any
from .typing import Dict
from .typing import FilePath
from .typing import Key
from .typing import List
from .typing import Optional
from .typing import Tuple
from .typing import WatchFunction
from .watchers import Watchable
from .watchers import Watchers

log = getLogger(__name__)


class Flag(Enum):
    MISSING = 1
    """Flag missing value."""

    REMOVE = 2
    """Flag config item to be removed."""


class ResConfig(Watchable, IO, CLArgs):
    """An application resource configuration.

    This object holds the state and the internal data structure for the configuration.

    Args:
        default: Default config.
        config_files: List of config filename paths.
        envvar_prefix: Prefix used for environment variables used as configuration.
        load_on_init: :obj:`True` to load config on instantiation, :obj:`False` to skip.
        merge_config_files: :obj:`True` to merge all configs from existing files,
            :obj:`False` to read only the config from the first existing file.
        schema: *Experimental:* Config schema.
        watchers: Config watchers.
    """

    def __init__(
        self,
        default: Optional[dict] = None,
        config_files: Optional[List[FilePath]] = None,
        envvar_prefix: str = "",
        load_on_init: bool = True,
        merge_config_files: bool = True,
        schema: Optional[dict] = None,
        watchers: Optional[Dict[Key, List[WatchFunction]]] = None,
    ):
        self._default = ONDict(default or {})
        self._config_files = (
            [ensure_path(p) for p in config_files] if config_files else []
        )
        self._envvar_prefix = envvar_prefix
        self._clargs = ONDict()
        self._merge_config_files = merge_config_files
        self._schema = Schema(schema or {})
        self._watchers = Watchers()
        for k, v in (watchers or {}).items():
            for func in v if isinstance(v, Iterable) else [v]:
                self.register(k, v)

        # This is where the active config is stored.
        self._conf = ONDict()

        if load_on_init:
            self.load()

    def __contains__(self, key):
        return key in self._conf

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self.get(key)

    def _asdict(self) -> dict:
        """Return the config as a dict object."""
        return dict(deepcopy(self._conf))

    def _prepare_config(self) -> ONDict:
        """Prepare a new :class:`ONDict` object with the current object state.

        Returns:
             An :class:`~resconfig.ondict.ONDict` object.
        """
        new = deepcopy(self._default)

        if self._config_files:
            new.merge(
                read_from_files_as_dict(self._config_files, self._merge_config_files)
            )

        env = os.environ
        clargs = self._clargs
        for key in self._default.allkeys():
            envkey = self._envvar_prefix + "_".join(
                k.replace(r"\.", "_").upper() for k in key
            )
            if envkey in env:
                new[key] = env[envkey]

            if key in clargs:
                new[key] = clargs[key]

        return new

    def get(self, key: Key, default: Optional[Any] = None) -> Any:
        """Return the config value for key if it exists, else default.

        Args:
            key: Config key.
            default: Default value if key is not in config.

        Returns:
            The value found for the key.
        """
        try:
            value = self._conf[key]
        except Exception:
            return default
        return deepcopy(value)

    def load(self):
        """Load the prepared config."""
        self.replace(self._prepare_config())

    def __update(
        self, key: Tuple[str], conf: dict, newconf: dict, replace: bool = False
    ) -> Tuple[Action, Any, Any]:
        """Perform config update recursively.

        Tuple of keys to the current node ``k`` holds the full path from the root, i.e.,
        ``("root", "k1", "k2", ..., "k")``, where ``conf["k"]`` and ``newconf["k"]`` is
        the node to be inspected at the current call stack. The full key path needs to
        be retained this way to notify watch functions.

        Args:
            key: Tuple of keys to the current node.
            conf: Old config to be updated.
            newconf: New config to update with.
            replace: :obj:`True` to perform replacement instead of merge.

        Returns:
            A tuple of action, old value, and new value for the current key.
        """
        _key = key[-1]

        if not isdict(newconf[_key]):
            newval = self._schema.apply(key[1:], newconf[_key])
            action = None
            if not isdict(conf):
                oldval = Flag.MISSING
                if newval is not Flag.REMOVE:
                    action = Action.ADDED
            elif _key not in conf or conf[_key] is Flag.MISSING or not conf[_key]:
                oldval = Flag.MISSING
                if newval is not Flag.REMOVE:
                    action = Action.ADDED
            else:
                oldval = deepcopy(conf[_key])
                if newval is Flag.REMOVE:
                    action = Action.REMOVED
                elif oldval != newval:
                    action = Action.MODIFIED
            return action, oldval, newval

        oldval_at_dict_node = deepcopy(conf[_key]) if _key in conf else Flag.MISSING
        newval_at_dict_node = ONDict()

        conf.setdefault(_key, ONDict())

        for subkey in newconf[_key].keys():
            if not isdict(conf[_key]):
                conf[_key] = ONDict()

            action, oldval, newval = self.__update(
                key + (subkey,), conf[_key], newconf[_key], replace=replace
            )

            # Actually update the config storage
            if action in (Action.MODIFIED, Action.ADDED):
                if isdict(newval):
                    newval = merge(conf[_key][subkey], newval)
                    newval_at_dict_node[subkey] = merge(
                        newval_at_dict_node.setdefault(subkey, ONDict()), newval
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
                        Flag.REMOVE,
                    )
                del conf[_key][subkey]

        # Define the action performed on this dict node.
        action = None
        if newval_at_dict_node:
            if not oldval_at_dict_node or oldval_at_dict_node is Flag.MISSING:
                action = Action.ADDED
                oldval_at_dict_node = Flag.MISSING
            else:
                if newval_at_dict_node != oldval_at_dict_node:
                    action = Action.MODIFIED
        elif not oldval_at_dict_node:
            action = Action.REMOVED

        return action, oldval_at_dict_node, newval_at_dict_node

    @flexdictargs
    def update(self, conf: dict):
        """Perform update of config.

        Args:
            conf: Config to update with.
        """
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf})

    @flexdictargs
    def replace(self, conf: dict):
        """Perform replacement of config.

        Args:
            conf: Config for replacement.
        """
        k = "__ROOT__"  # Insert a layer for the first iteration
        self.__update((k,), {k: self._conf}, {k: conf}, replace=True)

    def reset(self):
        """Reset config to default."""
        self.replace(deepcopy(self._default))
