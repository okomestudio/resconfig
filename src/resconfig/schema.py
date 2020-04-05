from .dicttype import Dict


class Schema(Dict):
    def apply(self, key, val):
        cls = self.get(key, None)
        if callable(cls):
            try:
                return cls(val)
            except Exception:
                raise TypeError(f"{val!r} cannot be converted to {cls}")
        return val
