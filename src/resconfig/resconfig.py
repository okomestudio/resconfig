REMOVE = object()


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

    def _update(self, dic, new, cbs):
        for k, v in new.items():
            if isinstance(v, dict):
                self._update(dic.setdefault(k, {}), v, cbs[k] if k in cbs else {})
            else:
                if v is REMOVE:
                    del dic[k]
                else:
                    dic[k] = v

            if k in cbs and self.reloaderkey in cbs[k]:
                cbs[k][self.reloaderkey](v)

    def update(self, new):
        self._update(self._d, new, self._reloaders)
