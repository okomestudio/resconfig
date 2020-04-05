from .dicttype import Dict
from .dicttype import normkey


class Schema(Dict):
    def apply(self, key, val):
        cls = self.get(key)
        if not isinstance(cls, Schema):
            try:
                return cls(val)
            except Exception:
                raise TypeError(f"{val!r} cannot be converted to {cls}")
        return val

    def get(self, key):
        ref = self
        for k in normkey(key):
            if k in ref:
                ref = ref[k]
            else:
                return Schema()
        return Schema(ref) if isinstance(ref, dict) else ref
