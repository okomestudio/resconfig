from functools import wraps

from .actions import Action
from .dicttype import Dict
from .typing import Key
from .typing import Optional
from .typing import WatchFunction


class Watchers(Dict):
    _create = True
    __watcher_key = "__watchers__"

    def deregister(self, key, func=None):
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

    def exists(self, key: Key):
        return key in self and self.__watcher_key in self[key]

    def funcs(self, key):
        if key in self:
            return self[key].get(self.__watcher_key, [])
        return []

    def trigger(self, key, action, oldval, newval):
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

    def reload(self):
        """Trigger all watch functions using the current config."""
        for key, val in self._conf.items():
            self._watchers.trigger(key, Action.RELOADED, val, val)

    def watch(self, key: Key) -> WatchFunction:
        """Decorate a function to make it a watch function for the key."""

        def deco(f):
            @wraps(f)
            def _deco(*args, **kwargs):
                return f(*args, **kwargs)

            self.register(key, _deco)
            return _deco

        return deco
