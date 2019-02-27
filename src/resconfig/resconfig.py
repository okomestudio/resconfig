def _normkey(key) -> list:
    return key.split(".") if isinstance(key, str) else key


class ResConfig:
    reloaderkey = "__reloader__"

    def __init__(self, default=None):
        self._d = default or {}
        self._reloaders = {}

    def deregister(self, key, func=None):
        r = self._reloaders
        for k in _normkey(key):
            r = r[k]
        if func is None:
            del r[self.reloaderkey]
        else:
            r[self.reloaderkey].remove(func)
            if len(r[self.reloaderkey]) == 0:
                del r[self.reloaderkey]

    def get(self, key):
        d = self._d
        for k in _normkey(key):
            d = d[k]
        return d

    def load(self, filename):
        pass

    def load_from_dict(self, dic):
        pass

    def register(self, key, func):
        # d = self._d
        r = self._reloaders
        for k in _normkey(key):
            # if k not in d:
            #     raise ValueError(f"{k} is not a valid config item")
            # d = d[k]
            r = r.setdefault(k, {})
        r.setdefault(self.reloaderkey, []).append(func)

    def reload(self):
        pass

    def set(self, key, value):
        ks = _normkey(key)
        d = self._d
        for k in ks[:-1]:
            d = d[k]
        d[ks[-1]] = value

        r = self._reloaders
        for k in ks:
            if k not in r:
                break
            r = r[k]
            if self.reloaderkey in r:
                for func in r[self.reloaderkey]:
                    func(self)
