from .dicttype import Dict


class Schema(Dict):
    def _cast(self, cls, value):
        if callable(cls):
            try:
                return cls(value)
            except Exception:
                raise TypeError(f"{value!r} cannot be converted to {cls}")
        return value

    def apply(self, key, value):
        item = self.get(key, None)
        cls = item[0] if isinstance(item, tuple) else item
        return self._cast(cls, value)

    def unapply(self, key, value):
        item = self.get(key, None)
        cls = item[1] if isinstance(item, tuple) else item
        return self._cast(cls, value)

    def unapply_all(self, d):
        for key in self.allkeys():
            print(key, "in", d)
            if key in d:
                print("applying")
                d[key] = self.unapply(key, d[key])
