from functools import wraps

from .actions import Action
from .dicttype import Dict
from .dicttype import isdict
from .typing import Any
from .typing import Key
from .typing import List
from .typing import Optional
from .typing import WatchFunction


class Watchers(Dict):
    _create = True
    __watcher_key = "__watchers__"

    def deregister(self, key: Key, func: Optional[WatchFunction] = None):
        """Deregister the watch function for the key."""
        ref = self.get(key)
        if not ref:
            raise KeyError(f"Watch function not registered for {key}")
        if func is None:
            if self.__watcher_key in ref:
                del ref[self.__watcher_key]
        else:
            if self.__watcher_key not in ref:
                raise KeyError(f"Watch functions not registered for {key}")
            try:
                ref[self.__watcher_key].remove(func)
            except ValueError:
                raise ValueError(f"{func!r} not registered for {key}")
            # If this was the last watch function, remove the node.
            if not ref[self.__watcher_key]:
                del ref[self.__watcher_key]

    def register(self, key: Key, func: WatchFunction):
        """Register the watch function for the key."""
        self.setdefault(key, self.__class__()).setdefault(
            self.__watcher_key, []
        ).append(func)

    def exists(self, key: Key) -> bool:
        """Test if any watch function exists for the key."""
        return key in self and self.__watcher_key in self[key]

    def funcs(self, key: Key) -> List[WatchFunction]:
        """Get the list of watch functions for the key."""
        if key in self:
            return self[key].get(self.__watcher_key, [])
        return []

    def trigger(self, key: Key, action: Action, oldval: Any, newval: Any):
        """Trigger the watch functions for the key."""
        for func in self.funcs(key):
            func(action, oldval, newval)


class Watchable:
    """Mix-in for adding the watch functionality."""

    def deregister(self, key: Key, func: Optional[WatchFunction] = None):
        """Deregister the watch function for the key."""
        self._watchers.deregister(key, func)

    def register(self, key: Key, func: WatchFunction):
        """Register the watch function for the key."""
        self._watchers.register(key, func)

    def __reload(self, key, d):
        _key = key[-1]
        if not isdict(d[_key]):
            self._watchers.trigger(key[1:], Action.RELOADED, d[_key], d[_key])
            return
        for subkey, v in d[_key].items():
            self.__reload(key + (subkey,), d[_key])
        self._watchers.trigger(key[1:], Action.RELOADED, d[_key], d[_key])

    def reload(self):
        """Trigger all watch functions using the current configuration.

        Note that the watch functions for the keys that do not exist in the current
        configuration will not be triggered.
        """
        # The reason why the recursive visit is on the conf, not the watchers is that we
        # want to trigger functions in order of configuration.
        self.__reload(("__ROOT__",), {"__ROOT__": self._conf})

    def watch(self, key: Key) -> WatchFunction:
        """Decorate a function to make it a watch function for the key."""

        def deco(f):
            @wraps(f)
            def _deco(*args, **kwargs):
                return f(*args, **kwargs)

            self.register(key, _deco)
            return _deco

        return deco
